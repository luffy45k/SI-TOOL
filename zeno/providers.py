"""Environment-configured async chat providers with automatic fallback."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ProviderError(RuntimeError):
    """Safe-to-display provider error; deliberately excludes credentials/body."""


@dataclass(frozen=True)
class ProviderConfig:
    online_key: str | None
    online_url: str
    online_model: str
    local_url: str | None
    local_model: str

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        return cls(
            online_key=os.getenv("OPENAI_API_KEY"),
            online_url=os.getenv("ZENO_ONLINE_URL", "https://api.openai.com/v1/chat/completions"),
            online_model=os.getenv("ZENO_ONLINE_MODEL", "gpt-4o-mini"),
            local_url=os.getenv("ZENO_LOCAL_URL"),
            local_model=os.getenv("ZENO_LOCAL_MODEL", "llama3.2"),
        )


class ProviderRouter:
    """Try configured online provider first, then configured local Ollama."""

    def __init__(self, config: ProviderConfig | None = None):
        self.config = config or ProviderConfig.from_env()

    async def chat(self, messages: list[dict[str, str]]) -> str:
        failures: list[str] = []
        cfg = self.config
        if cfg.online_key:
            try:
                return await asyncio.to_thread(self._online, messages)
            except ProviderError as exc:
                logger.warning("Online provider unavailable; trying local fallback (%s)", exc)
                failures.append(f"online: {exc}")
        if cfg.local_url:
            try:
                return await asyncio.to_thread(self._local, messages)
            except ProviderError as exc:
                logger.warning("Local provider unavailable (%s)", exc)
                failures.append(f"local: {exc}")
        if failures:
            raise ProviderError("No configured provider succeeded (" + "; ".join(failures) + ")")
        raise ProviderError("No provider configured. Set OPENAI_API_KEY or ZENO_LOCAL_URL.")

    def _post(self, url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
        data = json.dumps(payload).encode("utf-8")
        request = Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})}, method="POST")
        try:
            with urlopen(request, timeout=90) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise ProviderError("provider response exceeded 2 MB")
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ProviderError("provider returned an invalid response")
            return result
        except HTTPError as exc:
            raise ProviderError(f"HTTP {exc.code}") from None
        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError(f"connection failed ({type(exc).__name__})") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ProviderError("provider returned invalid JSON") from None

    def _online(self, messages: list[dict[str, str]]) -> str:
        cfg = self.config
        result = self._post(cfg.online_url, {"model": cfg.online_model, "messages": messages, "temperature": 0.2}, {"Authorization": f"Bearer {cfg.online_key}"})
        try:
            content = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise ProviderError("online provider response lacked assistant content") from None
        if not isinstance(content, str):
            raise ProviderError("online provider returned non-text content")
        return content

    def _local(self, messages: list[dict[str, str]]) -> str:
        cfg = self.config
        url = cfg.local_url.rstrip("/")
        if not url.endswith("/api/chat"):
            url += "/api/chat"
        result = self._post(url, {"model": cfg.local_model, "messages": messages, "stream": False})
        try:
            content = result["message"]["content"]
        except (KeyError, TypeError):
            raise ProviderError("local provider response lacked assistant content") from None
        if not isinstance(content, str):
            raise ProviderError("local provider returned non-text content")
        return content
