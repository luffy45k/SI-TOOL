"""Bounded task manager and self-critique for the prototype agent."""

from __future__ import annotations

from .brain import make_plan


def run_task(task: str, max_steps: int = 3) -> dict:
    if not 1 <= max_steps <= 10:
        raise ValueError("max_steps must be between 1 and 10")
    plan = make_plan(task)
    completed = plan[:max_steps]
    critique = {
        "ok": len(completed) == len(plan),
        "note": "Plan completed; verify any actual changes manually." if len(completed) == len(plan) else "Stopped at the configured step limit; no commands were executed.",
    }
    return {"task": task, "plan": plan, "completed_steps": completed, "critique": critique}
