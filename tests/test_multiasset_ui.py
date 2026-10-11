"""Real Qt multi-asset paper flow, using local records only."""

import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.components.local_workbench import LocalWorkbenchPage, PaperPortfolioPage


class MultiassetUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_chart_aggregation_controls_and_error_clear(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"ANKA_STATE_DIR": directory, "ANKA_OFFLINE": "1"}),
        ):
            page = LocalWorkbenchPage()
            try:
                page.run_sample()
                original = page.chart.bars[:5]
                page.chart_group.setCurrentIndex(1)
                first = page.chart.display_bars()[0]
                self.assertEqual(first.open, original[0].open)
                self.assertEqual(first.close, original[-1].close)
                self.assertEqual(first.high, max(bar.high for bar in original))
                self.assertEqual(first.volume, sum(bar.volume for bar in original))
                page.chart_mode.setCurrentText("Çizgi")
                page.sma_overlay.setChecked(False)
                self.assertEqual(page.chart.mode, "Çizgi")
                self.assertFalse(page.chart.show_sma)
                self.assertFalse(page.chart.grab().isNull())
                page.run_bars([], "CSV")
                self.assertIsNone(page.result)
                self.assertEqual(page.chart.bars, [])
                self.assertEqual(page.table.rowCount(), 0)
            finally:
                page.close()

    def test_workspace_settings_and_restore_refresh(self):
        from ui.workspace import Workspace

        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"ANKA_STATE_DIR": directory, "ANKA_OFFLINE": "1"}
        ), patch("requests.sessions.Session.request", side_effect=AssertionError("NO_NETWORK")):
            workspace = Workspace()
            try:
                settings = workspace.widget(5)
                settings.symbol.setText("SAVEDUSD")
                settings.currency.setCurrentText("USD")
                settings.save_settings()
                analysis = workspace.widget(1)
                self.assertEqual(analysis.symbol.text(), "SAVEDUSD")
                self.assertEqual(analysis.currency.currentText(), "USD")
                reopened = LocalWorkbenchPage()
                self.assertEqual(reopened.symbol.text(), "SAVEDUSD")
                reopened.close()
                analysis.run_sample()
                self.assertIsNotNone(analysis.result)
                settings.database_restored.emit()
                self.assertIsNone(analysis.result)
            finally:
                workspace.close()

    def test_two_symbols_currency_and_missing_fx(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"ANKA_STATE_DIR": directory, "ANKA_OFFLINE": "1"}),
            patch("requests.sessions.Session.request", side_effect=AssertionError("NO_NETWORK")),
        ):
            analysis = LocalWorkbenchPage()
            portfolio = PaperPortfolioPage()
            try:
                analysis.symbol.setText("LOCALTRY")
                analysis.run_sample()
                self.assertEqual(analysis.result["symbol"], "LOCALTRY")
                analysis.symbol.setText("LOCALUSD")
                analysis.currency.setCurrentText("USD")
                analysis.run_sample()
                self.assertEqual(analysis.result["currency"], "USD")
                portfolio.refresh()
                self.assertEqual(portfolio.symbol.count(), 2)
                portfolio.symbol.setCurrentIndex(portfolio.symbol.findData("LOCALUSD"))
                portfolio.trade("BUY")
                self.assertIn("kur", portfolio.status.text().lower())
                portfolio.fx_inputs["USD"].setValue(35)
                portfolio.trade("BUY")
                portfolio.symbol.setCurrentIndex(portfolio.symbol.findData("LOCALTRY"))
                portfolio.trade("BUY")
                labels = [
                    portfolio.table.item(row, 0).text() for row in range(portfolio.table.rowCount())
                ]
                self.assertTrue(any("LOCALUSD" in label for label in labels))
                self.assertTrue(any("LOCALTRY" in label for label in labels))
                other = PaperPortfolioPage()
                try:
                    other.refresh()
                    self.assertIn("LOCALUSD", other.status.text())
                    other.fx_inputs["USD"].setValue(35)
                    other.refresh()
                    self.assertIn("Kuru eksik: yok", other.status.text())
                finally:
                    other.close()
            finally:
                analysis.close()
                portfolio.close()
