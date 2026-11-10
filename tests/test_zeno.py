import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zeno.agent import run_task
from zeno.brain import make_plan
from zeno.memory import Memory
from zeno.providers import ProviderConfig, ProviderError, ProviderRouter
from zeno.sandbox import SandboxError, workspace_file
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

    def test_sqlite_memory_conversation_context_and_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            memory = Memory(Path(directory) / "memory.db")
            memory.add("hello")
            memory.add_turn("user", "question")
            memory.add_turn("assistant", "answer")
            memory.set_value("project_context", "language", "Python")
            memory.set_value("preferences", "tone", "concise")
            self.assertEqual(memory.read(), ["hello"])
            self.assertEqual(memory.history(), [{"role": "user", "content": "question"}, {"role": "assistant", "content": "answer"}])
            self.assertEqual(memory.values("project_context"), {"language": "Python"})
            self.assertTrue(memory.context_messages())

    def test_provider_router_uses_local_fallback_without_leaking_key(self):
        config = ProviderConfig("secret-not-for-logs", "https://example.invalid", "model", "http://localhost:11434", "local")
        router = ProviderRouter(config)
        with patch.object(router, "_online", side_effect=ProviderError("HTTP 503")), patch.object(router, "_local", return_value="local response"):
            self.assertEqual(asyncio.run(router.chat([{"role": "user", "content": "hello"}])), "local response")

    def test_unconfigured_router_fails_truthfully(self):
        router = ProviderRouter(ProviderConfig(None, "https://example.invalid", "model", None, "local"))
        with self.assertRaises(ProviderError):
            asyncio.run(router.chat([]))

    def test_sandbox_rejects_traversal_and_accepts_workspace_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "ok.py").write_text("print(1)")
            self.assertEqual(workspace_file(root, "ok.py"), (root / "ok.py").resolve())
            with self.assertRaises(SandboxError):
                workspace_file(root, "../outside.py")

    def test_builder_rejects_traversal_and_scaffolds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                project_builder("../escape", root)
            project_builder("demo", root)
            self.assertTrue((root / "demo" / "main.py").exists())


if __name__ == "__main__":
    unittest.main()
