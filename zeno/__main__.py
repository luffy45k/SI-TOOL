"""Command-line interface for ZENO AI."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from .agent import run_task
from .brain import make_plan
from .memory import Memory
from .providers import ProviderError, ProviderRouter
from .sandbox import SandboxError, run_script
from .tools import git_info, project_builder, web_search

ROOT = Path(__file__).resolve().parent.parent


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="zeno", description="Local-first AI coding assistant CLI")
    cli.add_argument("--verbose", action="store_true", help="enable diagnostic logging (secrets are never logged)")
    commands = cli.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="print a transparent offline task plan")
    plan.add_argument("task")
    ask = commands.add_parser("ask", help="ask the configured online/local LLM")
    ask.add_argument("prompt")
    remember = commands.add_parser("remember", help="save a local note (never store secrets)")
    remember.add_argument("text")
    commands.add_parser("memory", help="show saved notes")
    run = commands.add_parser("run", help="run a Python or JavaScript workspace script in Docker")
    run.add_argument("runtime", choices=("python", "javascript"))
    run.add_argument("script", help="existing relative .py/.js/.mjs file in workspace")
    commands.add_parser("git", help="show Git status and diff summary for workspace")
    build = commands.add_parser("build", help="scaffold a minimal project in workspace")
    build.add_argument("name")
    search = commands.add_parser("search", help="query a configured external search endpoint")
    search.add_argument("query")
    agent = commands.add_parser("agent", help="show a bounded plan (does not execute actions)")
    agent.add_argument("task")
    agent.add_argument("--max-steps", type=int, default=3)
    return cli


def _ask(prompt: str, memory: Memory) -> int:
    if not prompt.strip():
        print("Prompt must not be empty.", file=sys.stderr)
        return 2
    messages = memory.context_messages() + memory.history(18) + [{"role": "user", "content": prompt}]
    try:
        answer = asyncio.run(ProviderRouter().chat(messages))
    except ProviderError as exc:
        print(f"AI provider unavailable: {exc}", file=sys.stderr)
        return 1
    memory.add_turn("user", prompt)
    memory.add_turn("assistant", answer)
    print(answer)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s: %(message)s")
    memory = Memory()
    try:
        if args.command == "plan":
            print(json.dumps(make_plan(args.task), indent=2))
        elif args.command == "ask":
            return _ask(args.prompt, memory)
        elif args.command == "remember":
            print(memory.add(args.text))
        elif args.command == "memory":
            print(json.dumps(memory.read(), indent=2))
        elif args.command == "run":
            return run_script(ROOT / "workspace", args.script, args.runtime)
        elif args.command == "git":
            print(json.dumps(git_info(ROOT / "workspace"), indent=2))
        elif args.command == "build":
            print(project_builder(args.name, ROOT / "workspace"))
        elif args.command == "search":
            print(json.dumps(web_search(args.query), indent=2))
        elif args.command == "agent":
            if not 1 <= args.max_steps <= 10:
                print("--max-steps must be between 1 and 10", file=sys.stderr)
                return 2
            print(json.dumps(run_task(args.task, args.max_steps), indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
