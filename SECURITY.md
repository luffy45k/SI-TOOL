# Sandbox security model

The sandbox executes only an existing `.py`, `.js`, or `.mjs` file located under the selected workspace. The CLI starts a fixed Docker Compose command; it never runs the supplied code or a user-supplied command through a host shell. Workspace paths are resolved before execution and paths/symlinks that escape the workspace are rejected.

The container runs as UID/GID 1000, explicitly sets `privileged: false`, drops all Linux capabilities, disables privilege escalation, uses a read-only root filesystem, and has no network (`network_mode: none`). CPU, memory, process count, and `/tmp` size are constrained. The only host bind mount is the chosen workspace directory at `/workspace`; Docker credentials, home directories, source checkout, and other host paths are not mounted into the execution container. Python 3.12 and Node.js are installed in the container image. No API credentials are passed into the container.

GNU `timeout` runs inside the container and sends TERM then KILL after the configured execution time. A separate host-side timeout bounds a stuck Docker/Compose CLI. Timeout handling cannot make Docker a complete security boundary; keep Docker patched and prefer a disposable VM for actively malicious code. Do not mount the Docker socket, host credentials, or additional directories, and do not enable container networking for untrusted scripts.

Online/local LLM provider traffic originates from the host CLI and can include conversation history and explicitly saved context. Use only providers you trust. API credentials are read from environment variables and excluded from logs and error messages. Do not put credentials in prompts, notes, project context, or preferences.
