"""Offline acceptance tests for safe Codex process integration."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from core.agent_hub.adapters.codex_adapter import CodexAdapter


class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        (self.workspace / ".git").write_text("gitdir: test", encoding="utf-8")
        self.adapter = CodexAdapter("codex-developer", "developer", workspace=self.workspace)

    def tearDown(self):
        self.tmp.cleanup()

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex.cmd")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.run")
    def test_readonly_is_default(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, stdout="Summary", stderr="")
        r = self.adapter.run("Review architecture")
        self.assertTrue(r.success)
        self.assertEqual(r.output, "Summary")
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--sandbox") + 1], "read-only")
        self.assertEqual(argv[-1], "-")
        self.assertEqual(run.call_args.kwargs["input"], "Review architecture")
        self.assertNotIn("shell", run.call_args.kwargs)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.run")
    def test_write_mode_requires_explicit_configuration(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 0, stdout="candidate", stderr="")
        adapter = CodexAdapter("dev", "developer", workspace=self.workspace, allow_writes=True)
        self.assertTrue(adapter.run("Implement unit-tested change").success)
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--sandbox") + 1], "workspace-write")

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.run", side_effect=subprocess.TimeoutExpired("codex", 5))
    def test_timeout_is_a_failure(self, _run, _which):
        r = self.adapter.run("Read status")
        self.assertFalse(r.success)
        self.assertIn("timed out", r.error)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.run")
    def test_nonzero_exit_is_not_pass(self, run, _which):
        run.return_value = subprocess.CompletedProcess([], 9, stdout="", stderr="redacted")
        r = self.adapter.run("Read status")
        self.assertFalse(r.success)
        self.assertIn("exit 9", r.error)
        self.assertNotIn("redacted", r.error)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value=None)
    def test_missing_executable_is_failure(self, _which):
        self.assertFalse(self.adapter.run("Read status").success)

    def test_requires_valid_git_worktree(self):
        (self.workspace / ".git").unlink()
        with patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex"):
            self.assertFalse(self.adapter.run("Read status").success)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.run")
    def test_reject_injected_kwargs_and_empty_prompt(self, run, _which):
        self.assertFalse(self.adapter.run(" ").success)
        self.assertFalse(self.adapter.run("Task", unsafe_override=True).success)
        run.assert_not_called()

    def test_environment_does_not_forward_keys(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "private", "PATH": "custom"}, clear=True):
            clean = self.adapter._minimal_environment()
        self.assertNotIn("OPENAI_API_KEY", clean)
        self.assertEqual(clean["PATH"], "custom")

    def test_timeout_bounds(self):
        with self.assertRaises(ValueError):
            CodexAdapter("x", "developer", timeout_seconds=0)
