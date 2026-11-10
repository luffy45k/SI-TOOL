"""Transparent, deterministic planning primitives; no model/network calls."""

from __future__ import annotations


def make_plan(task: str) -> list[dict[str, str]]:
    task = " ".join(task.split())
    if not task:
        raise ValueError("task must not be empty")
    return [
        {"step": "clarify", "action": f"Confirm the desired outcome and constraints for: {task}"},
        {"step": "prepare", "action": "Inspect the workspace and identify the smallest safe change."},
        {"step": "execute", "action": "Perform one bounded action; review it before continuing."},
        {"step": "verify", "action": "Run relevant checks and report results and remaining risks."},
    ]
