# ZENO AI development plan

## Repository inspection

The existing repository already has a small Python CLI, Docker Compose sandbox, JSON note memory, utility functions, and four unit tests. The initial `agent` is only a static plan slicer; there is no LLM provider, and its command runner accepts arbitrary container commands. The existing Compose sandbox is non-root, has resource limits, drops capabilities, is read-only except for `workspace/`, and disables networking.

## Minimum working release (this change)

1. Keep the existing CLI and sandbox; constrain execution to Python/Node scripts inside the workspace, never host shell commands.
2. Add async OpenAI-compatible online and Ollama local chat providers, automatic online-first routing, and fallback. Read secrets only from environment variables and never print them.
3. Replace JSON notes with SQLite-backed notes, conversation history, project context, and preferences.
4. Add `zeno ask`; persist conversation turns and use the provider router. Keep planning usable offline and transparent.
5. Add tests for SQLite, routing/fallback, and sandbox input validation. Document setup and actual security boundaries.

## Follow-up milestones (not claimed as implemented)

- Model-driven task decomposition with explicit user approval between file edits and executions.
- Workspace-only file manager, static code analysis, and diagnostic/debug workflows.
- Iterative agent observation/critique with step budgets, cancellation, and audit history.
- Additional provider adapters and stronger egress filtering for any explicitly enabled network mode.

The follow-up work is intentionally not represented by placeholder implementations. Run the tests locally with `python -m unittest discover -s tests -v`; Docker execution also requires a working Docker Engine and Compose v2.
