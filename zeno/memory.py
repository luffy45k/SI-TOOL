"""Small local JSON note store."""

from __future__ import annotations

import json
from pathlib import Path


class Memory:
    def __init__(self, path: Path | None = None):
        self.path = path or Path.home() / ".zeno" / "memory.json"

    def read(self) -> list[str]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read memory file: {exc}") from exc
        if not isinstance(data, list) or not all(isinstance(item, str) for item in data):
            raise ValueError("memory file must contain a JSON list of strings")
        return data

    def add(self, note: str) -> str:
        note = note.strip()
        if not note:
            raise ValueError("note must not be empty")
        notes = self.read()
        notes.append(note)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(notes, indent=2) + "\n", encoding="utf-8")
        return f"Saved note {len(notes)} to {self.path}"
