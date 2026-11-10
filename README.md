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
python -m unittest discover -s tests -v
```

Conversation history, notes, project context, and preferences are stored in `~/.zeno/memory.sqlite3`. No API key is stored there. `zeno plan` works offline. Chat needs at least one configured provider.

## Sandbox security

`zeno run` accepts only an existing `.py`, `.js`, or `.mjs` script path relative to `workspace/`; it invokes only a fixed Docker Compose command and never a host shell. Docker mounts only the dedicated workspace, runs as non-root, drops capabilities, denies privilege escalation, sets CPU/memory/process limits, makes the container root filesystem read-only, and disables container networking. There are no published ports. Keep Docker patched. A container is not a hardened VM; do not run hostile code if you need a strong isolation boundary. The local model endpoint and online API run outside the execution container.

See `PLAN.md` for implemented scope and follow-up work, and `SECURITY.md` for security details.
