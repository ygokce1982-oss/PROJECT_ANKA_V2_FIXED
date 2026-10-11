"""No-network tests for the opt-in controlled cloud AI providers."""
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.ai.remote_read_only_team import RemoteReadOnlyTeam


class RemoteReadOnlyAITests(unittest.TestCase):
    def setUp(self):
        self.workspace = Path(__file__).resolve().parents[1]

    def test_unsupported_model_rejected(self):
        with self.assertRaises(ValueError):
            RemoteReadOnlyTeam("trader", self.workspace)

    @patch("core.ai.remote_read_only_team.AntigravityAdapter")
    def test_gemini_planning_success_is_research_only(self, adapter):
        adapter.return_value.run.return_value = SimpleNamespace(
            success=True, output="Taslak hazır.", error=None
        )
        team = RemoteReadOnlyTeam("planner", self.workspace)
        answer = team.run("BIST risk ölçütlerini sırala")
        self.assertTrue(answer.success)
        self.assertEqual(answer.final_output, "Taslak hazır.")
        sent = adapter.return_value.run.call_args.args[0]
        self.assertIn("gerçek emir", sent)
        self.assertIn("BIST risk", sent)
        self.assertEqual(adapter.call_args.kwargs["timeout_seconds"], 65)

    @patch("core.ai.remote_read_only_team.AntigravityAdapter")
    def test_claude_reviewer_failure_is_not_pass(self, adapter):
        adapter.return_value.run.return_value = SimpleNamespace(
            success=False, output=None, error="provider unavailable"
        )
        answer = RemoteReadOnlyTeam("reviewer", self.workspace).run("Raporu incele")
        self.assertFalse(answer.success)
        self.assertIn("provider unavailable", answer.errors)

    @patch("core.ai.remote_read_only_team.AntigravityAdapter")
    def test_reject_invalid_prompt_without_model_call(self, adapter):
        team = RemoteReadOnlyTeam("reviewer", self.workspace)
        for prompt in (" ", "x" * 4001):
            self.assertFalse(team.run(prompt).success)
        adapter.assert_not_called()
