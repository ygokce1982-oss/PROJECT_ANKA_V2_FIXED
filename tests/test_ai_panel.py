import os
import unittest

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.ai.workflow import WorkflowResult
from ui.components.ai_panel import AIPage

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class FakeLocalAITeam:
    def __init__(self, result: WorkflowResult) -> None:
        self.result = result
        self.last_task: str | None = None

    def run(self, task: str) -> WorkflowResult:
        self.last_task = task
        return self.result


class AIPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if QApplication.instance() is None:
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def _wait_for_worker(self, page: AIPage) -> None:
        for _ in range(20):
            QTest.qWait(100)
            if page._worker is None:
                break
        if page._worker is not None:
            page._worker.wait(1000)

    def test_empty_task_shows_warning(self) -> None:
        local_team = FakeLocalAITeam(
            WorkflowResult(success=True, step_results=(), final_output="Tamam", errors=())
        )
        page = AIPage(local_team=local_team)
        page.task_input.setPlainText("   ")

        page._on_analyze_clicked()

        self.assertFalse(page.analyze_button.isEnabled() is False)
        self.assertIn("Görev boş olamaz", page.status_label.text())
        self.assertIsNone(page._worker)

    def test_successful_result_displays_final_output(self) -> None:
        expected_output = "Bu bir test sonucudur."
        local_team = FakeLocalAITeam(
            WorkflowResult(success=True, step_results=(), final_output=expected_output, errors=())
        )
        page = AIPage(local_team=local_team)
        page.task_input.setPlainText("Test görevi")

        page._on_analyze_clicked()

        self.assertFalse(page.analyze_button.isEnabled())
        self._wait_for_worker(page)

        self.assertTrue(page.analyze_button.isEnabled())
        self.assertEqual(page.result_output.toPlainText(), expected_output)
        self.assertIn("Analiz tamamlandı", page.status_label.text())
        self.assertEqual(local_team.last_task, "Test görevi")

    def test_ollama_unreachable_shows_error_without_crash(self) -> None:
        local_team = FakeLocalAITeam(
            WorkflowResult(
                success=False,
                step_results=(),
                final_output=None,
                errors=("Ollama servisine ulaşılamıyor veya bazı ajanlar sağlıksız",),
            )
        )
        page = AIPage(local_team=local_team)
        page.task_input.setPlainText("Ağ testi")

        page._on_analyze_clicked()
        self.assertFalse(page.analyze_button.isEnabled())

        self._wait_for_worker(page)

        self.assertTrue(page.analyze_button.isEnabled())
        self.assertIn("Ollama servisine ulaşılamıyor", page.result_output.toPlainText())
        self.assertIn("Analiz hatası", page.status_label.text())

    def test_error_in_worker_emits_safe_result(self) -> None:
        class BrokenTeam:
            def run(self, task: str) -> WorkflowResult:
                raise RuntimeError("Beklenmeyen hata")

        page = AIPage(local_team=BrokenTeam())  # type: ignore[arg-type]
        page.task_input.setPlainText("Hata testi")

        page._on_analyze_clicked()
        self._wait_for_worker(page)

        self.assertTrue(page.analyze_button.isEnabled())
        self.assertIn("Ollama işleminde beklenmeyen hata", page.result_output.toPlainText())
        self.assertIn("Analiz hatası", page.status_label.text())

    def test_button_disabled_during_processing_and_reenabled_after(self) -> None:
        expected_output = "Düğme durumu testi"
        local_team = FakeLocalAITeam(
            WorkflowResult(success=True, step_results=(), final_output=expected_output, errors=())
        )
        page = AIPage(local_team=local_team)
        page.task_input.setPlainText("Düğme testi")

        page._on_analyze_clicked()
        self.assertFalse(page.analyze_button.isEnabled())

        self._wait_for_worker(page)

        self.assertTrue(page.analyze_button.isEnabled())
        self.assertEqual(page.result_output.toPlainText(), expected_output)


if __name__ == "__main__":
    unittest.main()
