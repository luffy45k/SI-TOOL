# ZENO AI

CLI-only local-first AI coding assistant starter. This first working slice provides OpenAI-compatible online chat, optional local Ollama chat, automatic online-first fallback, SQLite memory, transparent offline planning, and Python/JavaScript execution of workspace scripts in Docker. It does **not** claim a fully autonomous coding loop: autonomous file editing, approval workflows, code analysis, and iterative execution are follow-up milestones in `PLAN.md`.

## Requirements and setup

- Python 3.11+ (runtime uses only the standard library)
- Docker Engine and Docker Compose v2 for running scripts
- Ollama installed and a model pulled for local inference (optional)

Set `OPENAI_API_KEY` in your shell to enable the OpenAI-compatible online provider. The default endpoint/model are `https://api.openai.com/v1/chat/completions` and `gpt-4o-mini`; override with `ZENO_ONLINE_URL` and `ZENO_ONLINE_MODEL` for a compatible API. For local Ollama, set `ZENO_LOCAL_URL` (for example `http://127.0.0.1:11434`) and optionally `ZENO_LOCAL_MODEL` (default `llama3.2`). The router attempts online first when configured and falls back to local after a provider failure. Credentials are only read from environment and are never printed. Do not commit keys or place them in prompts/memory.

## Commands

```sh
python -m zeno --help
python -m zeno plan "Add a feature"
python -m zeno ask "Explain this project"
python -m zeno remember "Project uses Python"
python -m zeno memory
python -m zeno build demo
# Create workspace/hello.py first, then:
python -m zeno run python hello.py
python -m zeno run javascript app.js
python -m zeno run --help
python -m unittest discover -s tests -v
```

Conversation history, notes, project context, and preferences are stored in `~/.zeno/memory.sqlite3`. No API key is stored there. `zeno plan` works offline. Chat needs at least one configured provider.

## Sandboxed execution

`zeno run` accepts an existing `.py`, `.js`, or `.mjs` script path relative to `workspace/` and runs it in Docker; user code is never executed by a host shell or directly on the host. Python 3.12 and Debian's Node.js runtime are installed in the image. Docker Compose mounts only the selected workspace directory at `/workspace`.

The container runs as UID/GID 1000, is explicitly not privileged, drops all Linux capabilities, disables privilege escalation, uses a read-only root filesystem, disables networking, and limits CPU, memory, processes, and temporary storage. A GNU `timeout` process enforces a default 30-second execution limit in the container; the host also bounds a stuck Docker/Compose client. Override the script limit with `--timeout` only if the CLI supports it; otherwise use the Python API's `run_script(..., timeout=seconds)` (maximum one hour). Exit status 124 is treated as a sandbox timeout.

Real Python/JavaScript/timeout integration tests run when Docker Engine and Compose v2 are available; they are skipped otherwise. Unit tests cover path escape rejection, Docker CLI absence, host-client timeout, and Compose security settings without requiring Docker. Run all tests with `python -m unittest discover -s tests -v`.

See `PLAN.md` for implemented scope and follow-up work, and `SECURITY.md` for security details.
