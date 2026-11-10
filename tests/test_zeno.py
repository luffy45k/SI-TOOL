import json
import tempfile
import unittest
from pathlib import Path

from zeno.agent import run_task
from zeno.brain import make_plan
from zeno.memory import Memory
from zeno.tools import project_builder


class ZenoTests(unittest.TestCase):
    def test_plan_is_reviewable(self):
        plan = make_plan("make a demo")
        self.assertEqual(len(plan), 4)
        self.assertEqual(plan[-1]["step"], "verify")

    def test_agent_has_bounded_steps_and_does_not_execute(self):
        result = run_task("test", max_steps=2)
        self.assertEqual(len(result["completed_steps"]), 2)
        self.assertFalse(result["critique"]["ok"])
        with self.assertRaises(ValueError):
            run_task("test", max_steps=100)

    def test_memory_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Memory(Path(directory) / "memory.json")
            memory.add("hello")
            self.assertEqual(memory.read(), ["hello"])

    def test_builder_rejects_traversal_and_scaffolds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                project_builder("../escape", root)
            project_builder("demo", root)
            self.assertTrue((root / "demo" / "main.py").exists())


if __name__ == "__main__":
    unittest.main()
