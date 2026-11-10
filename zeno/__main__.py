"""Command-line interface for ZENO AI."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

from .agent import run_task
from .brain import make_plan
from .memory import Memory
from .tools import git_info, project_builder, web_search

ROOT = Path(__file__).resolve().parent.parent


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="zeno", description="Local-first AI assistant prototype")
    commands = cli.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="make a simple, reviewable task plan")
    plan.add_argument("task")
    remember = commands.add_parser("remember", help="save a local note (never store secrets)")
    remember.add_argument("text")
    commands.add_parser("memory", help="show saved notes")
    run = commands.add_parser("run", help="run a command in the restricted Docker sandbox")
    run.add_argument("args", nargs=argparse.REMAINDER, help="command after --")
    commands.add_parser("git", help="show Git status and diff summary for the workspace")
    build = commands.add_parser("build", help="scaffold a minimal project in workspace")
    build.add_argument("name")
    search = commands.add_parser("search", help="query a configured external search endpoint")
    search.add_argument("query")
    agent = commands.add_parser("agent", help="run a bounded plan/execute/review task")
    agent.add_argument("task")
    agent.add_argument("--max-steps", type=int, default=3)
    return cli


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    memory = Memory()
    if args.command == "plan":
        print(json.dumps(make_plan(args.task), indent=2))
    elif args.command == "remember":
        print(memory.add(args.text))
    elif args.command == "memory":
        print(json.dumps(memory.read(), indent=2))
    elif args.command == "run":
        command = args.args[1:] if args.args[:1] == ["--"] else args.args
        if not command:
            print("Provide a command, e.g. zeno run -- python -c 'print(1)'", file=sys.stderr)
            return 2
        proc = subprocess.run(["docker", "compose", "-f", str(ROOT / "compose.yaml"), "run", "--rm", "sandbox", *command], cwd=ROOT, check=False)
        return proc.returncode
    elif args.command == "git":
        print(json.dumps(git_info(ROOT / "workspace"), indent=2))
    elif args.command == "build":
        print(project_builder(args.name, ROOT / "workspace"))
    elif args.command == "search":
        try:
            print(json.dumps(web_search(args.query), indent=2))
        except (ValueError, OSError) as exc:
            print(f"Search unavailable: {exc}", file=sys.stderr)
            return 1
    elif args.command == "agent":
        if not 1 <= args.max_steps <= 10:
            print("--max-steps must be between 1 and 10", file=sys.stderr)
            return 2
        result = run_task(args.task, args.max_steps)
        print(json.dumps(result, indent=2))
        return 0 if result["critique"]["ok"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
