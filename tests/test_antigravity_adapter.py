"""Deterministic tests for Antigravity CLI Gemini/Claude adapter."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from core.agent_hub.adapters.antigravity_adapter import AntigravityAdapter


class AntigravityAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name)
        (self.workspace / ".git").write_text("gitdir: stub", encoding="utf-8")
        self.adapter = AntigravityAdapter("ai-reviewer", "reviewer", workspace=self.workspace)

    def tearDown(self):
        self.tmp.cleanup()

    @patch("core.agent_hub.adapters.antigravity_adapter.shutil.which", return_value="agy.exe")
    @patch("core.agent_hub.adapters.antigravity_adapter.subprocess.Popen")
    def test_claude_reviewer_runs_readonly(self, popen, _which):
        process = popen.return_value
        process.communicate.return_value = ("ANKA_REVIEW_PASS", "")
        process.returncode = 0
        result = self.adapter.run("Review code only")
        self.assertTrue(result.success)
        argv = popen.call_args.args[0]
        self.assertIn("--model=claude-sonnet-4-6", argv)
        self.assertIn("--mode=plan", argv)
        self.assertNotIn("--dangerously-skip-permissions", argv)
        self.assertFalse(popen.call_args.kwargs["shell"])
        self.assertEqual(argv[-1], "Review code only")

    @patch("core.agent_hub.adapters.antigravity_adapter.shutil.which", return_value="agy.exe")
    @patch("core.agent_hub.adapters.antigravity_adapter.subprocess.Popen")
    def test_gemini_planner_model(self, popen, _which):
        process = popen.return_value
        process.communicate.return_value = ("ANKA_PLAN", "")
        process.returncode = 0
        a = AntigravityAdapter("planner", "planner", workspace=self.workspace)
        self.assertTrue(a.run("Plan feature").success)
        self.assertIn("--model=gemini-3.8-flash-low", popen.call_args.args[0])

    @patch("core.agent_hub.adapters.antigravity_adapter.shutil.which", return_value="agy.exe")
    @patch("core.agent_hub.adapters.antigravity_adapter.subprocess.Popen")
    @patch("core.agent_hub.adapters.antigravity_adapter._stop_process_tree")
    def test_timeout_kills_subtree(self, stop, popen, _which):
        process = popen.return_value
        process.communicate.side_effect = subprocess.TimeoutExpired("agy", 75)
        result = self.adapter.run("Review")
        self.assertFalse(result.success)
        stop.assert_called_once_with(process)

    @patch("core.agent_hub.adapters.antigravity_adapter.shutil.which", return_value="agy.exe")
    @patch("core.agent_hub.adapters.antigravity_adapter.subprocess.Popen")
    def test_nonzero_cannot_pass(self, popen, _which):
        process = popen.return_value
        process.returncode = 3
        process.communicate.return_value = ("", "private")
        r = self.adapter.run("Review")
        self.assertFalse(r.success)
        self.assertNotIn("private", r.error)

    def test_worktree_and_secret_validation(self):
        with patch("core.agent_hub.adapters.antigravity_adapter.shutil.which", return_value="agy.exe"):
            (self.workspace / ".git").unlink()
            self.assertFalse(self.adapter.run("Review").success)
        with patch.dict(os.environ, {"PATH":"bin", "GEMINI_API_KEY":"secret"}, clear=True):
            env = self.adapter._minimal_environment()
        self.assertNotIn("GEMINI_API_KEY", env)

    def test_unknown_model_rejected(self):
        with self.assertRaises(ValueError):
            AntigravityAdapter("x", "planner", workspace=self.workspace, model="--yolo true")

    def test_empty_and_invalid_timeout(self):
        self.assertFalse(self.adapter.run(" ").success)
        with self.assertRaises(ValueError):
            AntigravityAdapter("x", "planner", workspace=self.workspace, timeout_seconds=0)
