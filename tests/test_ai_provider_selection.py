"""Qt acceptance: Gemini/Claude never start unless user explicitly selects them."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from core.ai.remote_read_only_team import RemoteReadOnlyTeam
from ui.components.ai_panel import AIPage


class ProviderSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_ollama_selected_by_default(self):
        page = AIPage()
        self.assertEqual(page.model_selector.currentIndex(), 0)
        page.close()

    @patch("ui.components.ai_panel.AIWorker")
    def test_gemini_is_explicit_opt_in(self, worker):
        page = AIPage()
        page.task_input.setPlainText("Teknik riski açıkla")
        page.model_selector.setCurrentIndex(1)
        page._on_analyze_clicked()
        run_team = worker.call_args.kwargs["local_team"]
        self.assertIsInstance(run_team, RemoteReadOnlyTeam)
        self.assertEqual(run_team.role, "planner")
        worker.return_value.start.assert_called_once()
        page.close()

    @patch("ui.components.ai_panel.AIWorker")
    def test_claude_is_explicit_opt_in(self, worker):
        page = AIPage()
        page.task_input.setPlainText("Raporu denetle")
        page.model_selector.setCurrentIndex(2)
        page._on_analyze_clicked()
        run_team = worker.call_args.kwargs["local_team"]
        self.assertIsInstance(run_team, RemoteReadOnlyTeam)
        self.assertEqual(run_team.role, "reviewer")
        worker.return_value.start.assert_called_once()
        page.close()
