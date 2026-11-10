import asyncio
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from zeno.agent import run_task
from zeno.brain import make_plan
from zeno.memory import Memory
from zeno.providers import ProviderConfig, ProviderError, ProviderRouter
from zeno.sandbox import SandboxError, SandboxTimeout, run_script, workspace_file
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

    def test_workspace_rejects_invalid_paths_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            workspace = base / "workspace"
            workspace.mkdir()
            outside = base / "outside.py"
            outside.write_text("print('outside')")
            inside = workspace / "ok.py"
            inside.write_text("print('inside')")
            self.assertEqual(workspace_file(workspace, "ok.py"), inside.resolve())
            for invalid in ("../outside.py", str(outside), "missing.py"):
                with self.subTest(path=invalid), self.assertRaises(SandboxError):
                    workspace_file(workspace, invalid)
            try:
                (workspace / "escape.py").symlink_to(outside)
            except OSError:
                self.skipTest("symlinks are unavailable on this platform")
            with self.assertRaises(SandboxError):
                workspace_file(workspace, "escape.py")

    def test_docker_unavailable_is_reported_without_host_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "hello.py").write_text("raise RuntimeError('must not run on host')")
            with patch("zeno.sandbox.subprocess.run", side_effect=FileNotFoundError):
                with self.assertRaisesRegex(SandboxError, "Docker CLI was not found"):
                    run_script(workspace, "hello.py", "python")

    def test_host_docker_client_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            (workspace / "hello.py").write_text("pass")
            with patch("zeno.sandbox.subprocess.run", side_effect=subprocess.TimeoutExpired("docker", 61)) as docker_run:
                with self.assertRaises(SandboxTimeout):
                    run_script(workspace, "hello.py", "python", timeout=1)
            self.assertEqual(docker_run.call_args.kwargs["timeout"], 61)

    def test_compose_isolation_settings_and_workspace_mount(self):
        root = Path(__file__).resolve().parent.parent
        compose = (root / "compose.yaml").read_text(encoding="utf-8")
        self.assertIn("privileged: false", compose)
        self.assertIn("read_only: true", compose)
        self.assertIn("cap_drop:\n      - ALL", compose)
        self.assertIn("network_mode: none", compose)
        self.assertIn("mem_limit: 1g", compose)
        self.assertIn("cpus: 1.0", compose)
        self.assertEqual(compose.count(":/workspace"), 1)

    def test_builder_rejects_traversal_and_scaffolds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                project_builder("../escape", root)
            project_builder("demo", root)
            self.assertTrue((root / "demo" / "main.py").exists())


class DockerSandboxIntegrationTests(unittest.TestCase):
    """Real runtime checks; skipped unless Docker Engine and Compose are usable."""

    @classmethod
    def setUpClass(cls):
        if shutil.which("docker") is None:
            raise unittest.SkipTest("Docker CLI is not installed")
        try:
            compose = subprocess.run(["docker", "compose", "version"], capture_output=True, timeout=5, check=False)
            engine = subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise unittest.SkipTest("Docker Engine/Compose is not available") from None
        if compose.returncode or engine.returncode:
            raise unittest.SkipTest("Docker Engine/Compose is not available")

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self._temp.name)

    def tearDown(self):
        self._temp.cleanup()

    def test_python_script_executes_only_in_container_workspace(self):
        (self.workspace / "main.py").write_text("from pathlib import Path\nPath('python.ok').write_text('ok')\n", encoding="utf-8")
        self.assertEqual(run_script(self.workspace, "main.py", "python", timeout=60), 0)
        self.assertEqual((self.workspace / "python.ok").read_text(), "ok")

    def test_javascript_script_executes_only_in_container_workspace(self):
        (self.workspace / "main.js").write_text("require('node:fs').writeFileSync('javascript.ok', 'ok');\n", encoding="utf-8")
        self.assertEqual(run_script(self.workspace, "main.js", "javascript", timeout=60), 0)
        self.assertEqual((self.workspace / "javascript.ok").read_text(), "ok")

    def test_script_timeout_is_enforced_inside_container(self):
        (self.workspace / "slow.py").write_text("while True: pass\n", encoding="utf-8")
        with self.assertRaises(SandboxTimeout):
            run_script(self.workspace, "slow.py", "python", timeout=1)


if __name__ == "__main__":
    unittest.main()
