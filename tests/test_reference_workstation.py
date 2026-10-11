"""Reference layout, financial demo honesty, and real interaction acceptance."""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QSplitter, QLabel, QScrollArea

from core.market_data import MarketData
from ui.main_window import MainWindow


class ReferenceWorkstationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "ANKA_OFFLINE": "1", "ANKA_DISABLE_LIVE": "1",
            "ANKA_STATE_DIR": self.temp.name,
        })
        self.env.start()
        self.window = MainWindow()
        self.dashboard = self.window.workspace.dashboard

    def tearDown(self):
        self.window.close()
        self.env.stop()
        self.temp.cleanup()

    def test_reference_has_three_resizable_columns_and_panels(self):
        dividers = self.dashboard.findChildren(QSplitter)
        self.assertEqual(len(dividers), 3)
        self.assertEqual(sorted(s.count() for s in dividers), [2, 2, 3])
        self.assertGreaterEqual(self.dashboard.watch.rowCount(), 10)
        self.assertGreaterEqual(self.dashboard.screener.rowCount(), 2)
        self.assertGreaterEqual(self.dashboard.movers.rowCount(), 5)
        self.assertEqual(
            len([w for w in self.dashboard.findChildren(QScrollArea)
                 if w.objectName() == "NewsScrollArea"]), 1
        )

    def test_stock_selection_updates_quote(self):
        self.dashboard.select_symbol("ASELS")
        self.assertEqual(self.dashboard.symbol_label.text(), "ASELS")
        self.assertEqual(self.dashboard.last_label.text(), "168,40")
        self.dashboard.select_symbol("TUPRS")
        self.assertEqual(self.dashboard.change_label.text(), "-0,63%")

    def test_search_filters_actual_watchlist(self):
        self.dashboard.search.setText("Pegasus")
        self.assertFalse(self.dashboard.watch.isRowHidden(10))
        self.assertTrue(self.dashboard.watch.isRowHidden(1))
        self.dashboard.search.clear()
        self.assertFalse(self.dashboard.watch.isRowHidden(1))

    def test_scan_modes_change_real_table_rows(self):
        self.dashboard.set_scan_mode("Gerileyenler")
        self.assertEqual(self.dashboard.screener.rowCount(), 4)
        self.assertTrue(all(
            self.dashboard.screener.item(i, 2).text().startswith("-")
            for i in range(self.dashboard.screener.rowCount())
        ))
        self.dashboard.set_scan_mode("Momentum")
        self.assertEqual(self.dashboard.screener.rowCount(), 5)

    def test_offline_never_fetches_live_data(self):
        with patch.object(MarketData, "get_snapshot", side_effect=AssertionError("live request")):
            self.dashboard.refresh_button.click()
        self.assertIn("Çevrimdışı", self.dashboard.status_label.text())
        self.assertTrue(any("ÖRNEK VERİ" in widget.text() for widget in self.dashboard.findChildren(QLabel)))
