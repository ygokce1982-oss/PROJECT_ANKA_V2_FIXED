"""Offline CodexAdapter tests, including Windows process-tree timeout cleanup."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from core.agent_hub.adapters.codex_adapter import CodexAdapter, _stop_process_tree


class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        (self.workspace / ".git").write_text("gitdir: external", encoding="utf-8")
        self.adapter = CodexAdapter("codex-developer", "developer", workspace=self.workspace)

    def tearDown(self):
        self.temp.cleanup()

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex.cmd")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.Popen")
    def test_default_read_only_and_no_shell(self, popen, _which):
        process = popen.return_value
        process.communicate.return_value = ("Short, validated summary", "")
        process.returncode = 0
        result = self.adapter.run("Read codebase")
        self.assertTrue(result.success)
        self.assertEqual(result.output, "Short, validated summary")
        args, opts = popen.call_args
        self.assertIn("read-only", args[0])
        self.assertFalse(opts["shell"])
        self.assertEqual(process.communicate.call_args.kwargs["input"], "Read codebase")
        self.assertIn("timeout", process.communicate.call_args.kwargs)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex.cmd")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.Popen")
    def test_explicit_write_mode(self, popen, _which):
        process = popen.return_value
        process.communicate.return_value = ("candidate", "")
        process.returncode = 0
        adapter = CodexAdapter("dev", "developer", workspace=self.workspace, allow_writes=True)
        self.assertTrue(adapter.run("Unit-tested fix").success)
        self.assertIn("workspace-write", popen.call_args.args[0])

    @patch("core.agent_hub.adapters.codex_adapter._stop_process_tree")
    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex.cmd")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.Popen")
    def test_timeout_terminates_process_tree(self, popen, _which, stop):
        process = popen.return_value
        process.communicate.side_effect = subprocess.TimeoutExpired("codex", 5)
        result = self.adapter.run("Review")
        self.assertFalse(result.success)
        self.assertIn("timed out", result.error)
        stop.assert_called_once_with(process)

    @patch("core.agent_hub.adapters.codex_adapter.os.name", "nt")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.run")
    def test_windows_taskkill_targets_child_pid(self, run):
        process = Mock()
        process.pid = 4088
        process.poll.return_value = None
        _stop_process_tree(process)
        self.assertEqual(
            run.call_args.args[0],
            ["taskkill", "/PID", "4088", "/T", "/F"],
        )
        self.assertFalse(run.call_args.kwargs["shell"])
        process.kill.assert_called_once()

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex")
    @patch("core.agent_hub.adapters.codex_adapter.subprocess.Popen")
    def test_nonzero_code_is_failure(self, popen, _which):
        process = popen.return_value
        process.communicate.return_value = ("", "sensitive stderr")
        process.returncode = 17
        result = self.adapter.run("Read files")
        self.assertFalse(result.success)
        self.assertIn("exit 17", result.error)
        self.assertNotIn("sensitive", result.error)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value=None)
    def test_missing_cli(self, _which):
        self.assertFalse(self.adapter.run("Task").success)

    @patch("core.agent_hub.adapters.codex_adapter.shutil.which", return_value="codex.cmd")
    def test_not_a_git_worktree(self, _which):
        (self.workspace / ".git").unlink()
        self.assertFalse(self.adapter.run("Task").success)

    @patch("core.agent_hub.adapters.codex_adapter.subprocess.Popen")
    def test_empty_task_and_unsupported_kwargs(self, popen):
        self.assertFalse(self.adapter.run("  ").success)
        self.assertFalse(self.adapter.run("Task", bypass_permissions=True).success)
        popen.assert_not_called()

    def test_environment_secrets_do_not_pass(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "secret", "PATH": "ok"}, clear=True):
            data = self.adapter._minimal_environment()
        self.assertNotIn("OPENAI_API_KEY", data)
        self.assertEqual(data["PATH"], "ok")

    def test_timeout_limits(self):
        for seconds in (0, 901):
            with self.assertRaises(ValueError):
                CodexAdapter("x", "developer", timeout_seconds=seconds)
