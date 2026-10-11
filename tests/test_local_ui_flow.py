"""Exercise the desktop data-analysis-record-paper flow without any network."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.offline_workbench import LocalStore
from ui.main_window import MainWindow


class LocalUIFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_three_independent_desktop_windows_and_limit(self):
        with patch.dict(os.environ, {"ANKA_OFFLINE": "1"}):
            main = MainWindow()
            main.show()
            try:
                second = main.open_workspace_window()
                third = main.open_workspace_window()
                self.assertIsNotNone(second)
                self.assertIsNotNone(third)
                self.assertIsNone(main.open_workspace_window())
                second.workspace.setCurrentIndex(1)
                third.workspace.setCurrentIndex(4)
                self.assertEqual(main.workspace.currentIndex(), 0)
                self.assertEqual(second.workspace.currentIndex(), 1)
                self.assertEqual(third.workspace.currentIndex(), 4)
            finally:
                main.close()
            self.assertFalse(second.isVisible())
            self.assertFalse(third.isVisible())

    def test_sample_analysis_display_export_paper_trade_and_restart(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.dict(os.environ, {"ANKA_OFFLINE": "1", "ANKA_STATE_DIR": directory}),
            patch(
                "requests.sessions.Session.request", side_effect=AssertionError("NETWORK_FORBIDDEN")
            ),
        ):
            window = MainWindow()
            try:
                page = window.workspace.widget(1)
                page.run_sample()
                self.assertFalse(page.result["live"])
                self.assertEqual(len(page.chart.values), 120)
                self.assertIn("kalıcı kayda", page.status.text())
                self.assertEqual(page.table.item(0, 1).text(), "ÖRNEK")
                destination = Path(directory) / "export.json"
                with patch(
                    "ui.components.local_workbench.QFileDialog.getSaveFileName",
                    return_value=(str(destination), "JSON"),
                ):
                    page.export_result()
                exported = json.loads(destination.read_text(encoding="utf-8"))
                self.assertEqual(exported["digest"], page.result["digest"])
                portfolio = window.workspace.widget(4)
                portfolio.quantity.setValue(2)
                portfolio.trade("BUY")
                self.assertIn("DEMO1", portfolio.table.item(3, 0).text())
                portfolio.quantity.setValue(3)
                portfolio.trade("SELL")
                self.assertIn("yetersiz", portfolio.status.text())
                portfolio.add_alert()
                window.show()
                window.workspace.setCurrentIndex(1)
                self.app.processEvents()
                self.assertFalse(page.chart.grab().isNull())
            finally:
                window.close()
            second = MainWindow()
            try:
                second.workspace.widget(4).refresh()
                self.assertIn("DEMO1", second.workspace.widget(4).table.item(3, 0).text())
                store = LocalStore(Path(directory) / "research.sqlite")
                try:
                    self.assertEqual(
                        store.connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 1
                    )
                    self.assertEqual(
                        store.connection.execute("SELECT COUNT(*) FROM alerts").fetchone()[0], 1
                    )
                finally:
                    store.close()
            finally:
                second.close()
