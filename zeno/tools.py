"""Small utility tools; external search is opt-in and returns untrusted data."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl
from urllib.request import urlopen


def git_info(workspace: Path) -> dict:
    if not (workspace / ".git").exists():
        return {"initialized": False, "message": "No Git repository in workspace."}
    status = subprocess.run(["git", "-C", str(workspace), "status", "--short"], text=True, capture_output=True, check=False)
    diff = subprocess.run(["git", "-C", str(workspace), "diff", "--stat"], text=True, capture_output=True, check=False)
    return {"initialized": True, "status": status.stdout, "diff_stat": diff.stdout}


def project_builder(name: str, workspace: Path) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,49}", name):
        raise ValueError("project name must be 1-50 simple letters, digits, underscores, or hyphens")
    workspace.mkdir(parents=True, exist_ok=True)
    target = workspace / name
    target.mkdir(exist_ok=False)
    (target / "README.md").write_text(f"# {name}\n\nProject scaffold created by ZENO AI.\n", encoding="utf-8")
    (target / "main.py").write_text('"""Project entry point."""\n\n\ndef main():\n    print("Hello from ' + name + '")\n\n\nif __name__ == "__main__":\n    main()\n', encoding="utf-8")
    return f"Created {target}"


def web_search(query: str) -> dict:
    endpoint = os.environ.get("ZENO_SEARCH_URL", "").strip()
    if not endpoint:
        raise ValueError("Set ZENO_SEARCH_URL to enable external search")
    parsed = urlsplit(endpoint)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("ZENO_SEARCH_URL must be an HTTPS URL")
    params = dict(parse_qsl(parsed.query, keep_blank_values=True))
    params["q"] = query
    url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(params), ""))
    with urlopen(url, timeout=10) as response:
        if response.status != 200:
            raise OSError(f"search endpoint returned HTTP {response.status}")
        body = response.read(1_000_001)
    if len(body) > 1_000_000:
        raise OSError("search response exceeded 1 MB")
    try:
        result = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OSError("search endpoint did not return valid JSON") from exc
    return {"untrusted_search_results": result}
