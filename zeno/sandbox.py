"""Strictly scoped Docker execution for Python and JavaScript workspace scripts."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


class SandboxError(ValueError):
    pass


def workspace_file(workspace: Path, relative: str) -> Path:
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


def run_script(workspace: Path, relative: str, runtime: str) -> int:
    script = workspace_file(workspace, relative)
    if runtime == "python" and script.suffix == ".py":
        command = ["python", "/workspace/" + script.relative_to(workspace.resolve()).as_posix()]
    elif runtime == "javascript" and script.suffix in {".js", ".mjs"}:
        command = ["node", "/workspace/" + script.relative_to(workspace.resolve()).as_posix()]
    else:
        raise SandboxError("runtime must match a .py (python) or .js/.mjs (javascript) script")
    # The only host process invoked is the fixed Docker Compose client. User code
    # is passed as a script path to a container with no network or host mounts
    # other than the dedicated workspace. Never invoke a host shell.
    return subprocess.run(["docker", "compose", "-f", str(Path(__file__).resolve().parent.parent / "compose.yaml"), "run", "--rm", "sandbox", *command], cwd=Path(__file__).resolve().parent.parent, check=False).returncode


def valid_runtime(value: str) -> bool:
    return value in {"python", "javascript"}
