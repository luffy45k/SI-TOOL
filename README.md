# ZENO AI

ZENO AI is a local-first, modular assistant prototype with a CLI, task planner, persistent notes, and an isolated Docker execution sandbox. It is intentionally transparent: the initial brain is a small rule-based planner, not a secretly autonomous or self-modifying agent. Network access is disabled inside the execution container by default.

## Requirements

- Python 3.11+
- Docker Engine and Docker Compose v2 for sandboxed execution

## Quick start

```sh
python -m zeno --help
python -m zeno plan "Create a small Python project"
python -m zeno remember "The project uses Python"
python -m zeno memory
```

Run a command in the sandbox (Docker must be running):

```sh
python -m zeno run -- python -c 'print("hello from ZENO")'
```

The sandbox can only write to `./workspace`, runs as a non-root user, drops Linux capabilities, sets CPU/memory/process limits, and has no network access by default. It is a useful isolation layer, not a substitute for a hardened VM when running hostile code. See `SECURITY.md` before enabling network access or running untrusted tasks.

## Components

- **Brain:** replaceable planner/reasoning interface and local memory store.
- **Autonomous agent:** explicit task manager, bounded executor, and self-critique result check. No background loop; the user starts each run.
- **Secure sandbox:** Docker-backed terminal/code runner, workspace-only files, network disabled by default.
- **Tools:** Python runner and Git status/diff helpers; project scaffolding; optional web search adapter using an explicitly configured search endpoint.
- **Main:** CLI interface.

## Configuration

Set `ZENO_SEARCH_URL` to an HTTPS endpoint that accepts `q` as a query parameter and returns JSON to enable `zeno search`. Search requests are not sent unless this variable is configured. Use an endpoint you trust; returned content is untrusted input. Do not send secrets or private information in queries.

Memory is stored locally at `~/.zeno/memory.json`. It is plain text; do not save credentials or sensitive data there.

## Development

```sh
python -m unittest discover -s tests -v
```
