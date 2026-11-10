"""Strictly scoped Docker execution for Python and JavaScript workspace scripts."""

from __future__ import annotations

import math
import subprocess
from pathlib import Path


class SandboxError(ValueError):
    """Invalid sandbox request or unavailable Docker runtime."""


class SandboxTimeout(SandboxError):
    """The containerized script exceeded its configured time limit."""


def workspace_file(workspace: Path, relative: str) -> Path:
    """Resolve an existing regular script file without permitting path escape."""
    if not relative or Path(relative).is_absolute() or "\x00" in relative:
        raise SandboxError("provide a relative path inside the workspace")
    root = workspace.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise SandboxError("path must stay inside the workspace") from None
    if not candidate.is_file():
        raise SandboxError("script must be an existing regular file inside workspace")
    return candidate


def run_script(workspace: Path, relative: str, runtime: str, timeout: float = 30) -> int:
    """Run one workspace script in Docker; no user code runs on the host.

    GNU ``timeout`` enforces the limit inside the container (including child
    processes). The host-side timeout bounds a stuck Docker/Compose client too.
    Exit status 124 is reserved by GNU timeout and reported as SandboxTimeout.
    """
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or not 0 < timeout <= 3600:
        raise SandboxError("timeout must be greater than 0 and no more than 3600 seconds")

    script = workspace_file(workspace, relative)
    relative_path = script.relative_to(workspace.resolve()).as_posix()
    if runtime == "python" and script.suffix == ".py":
        command = ["python3", "/workspace/" + relative_path]
    elif runtime == "javascript" and script.suffix in {".js", ".mjs"}:
        command = ["node", "/workspace/" + relative_path]
    else:
        raise SandboxError("runtime must match a .py (python) or .js/.mjs (javascript) script")

    repo_root = Path(__file__).resolve().parent.parent
    compose_file = repo_root / "compose.yaml"
    docker_command = [
        "docker", "compose", "-f", str(compose_file), "run", "--build", "--rm", "-T", "sandbox",
        "timeout", "--signal=TERM", "--kill-after=2s", f"{timeout:g}s", *command,
    ]
    environment = None
    import os
    environment = os.environ.copy()
    environment["ZENO_WORKSPACE"] = str(workspace.resolve())

    try:
        result = subprocess.run(
            docker_command,
            cwd=repo_root,
            env=environment,
            check=False,
            timeout=timeout + 60,
        )
    except FileNotFoundError:
        raise SandboxError("Docker CLI was not found; install Docker Engine and Compose v2") from None
    except subprocess.TimeoutExpired:
        raise SandboxTimeout("Docker/Compose did not finish before the host-side timeout") from None
    if result.returncode == 124:
        raise SandboxTimeout(f"script exceeded the {timeout:g}-second execution limit")
    return result.returncode


def valid_runtime(value: str) -> bool:
    return value in {"python", "javascript"}
