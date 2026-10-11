"""Acceptance: real dashboard navigation, no fabricated offline quotes."""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from core.market_data import MarketData
from ui.main_window import MainWindow


class DashboardNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(
            os.environ, {
                "ANKA_OFFLINE": "1", "ANKA_DISABLE_LIVE": "1",
                "ANKA_STATE_DIR": self.tmp.name,
            },
        )
        self.env.start()
        self.window = MainWindow()

    def tearDown(self):
        self.window.close()
        self.env.stop()
        self.tmp.cleanup()

    def test_navigation_buttons_change_real_pages_and_sidebar(self):
        dashboard = self.window.workspace.dashboard
        for index in (1, 2, 3, 4):
            self.window.workspace.setCurrentIndex(0)
            dashboard.quick_buttons[index].click()
            self.assertEqual(self.window.workspace.currentIndex(), index)
            self.assertEqual(self.window.sidebar.currentRow(), index)

    def test_offline_dashboard_wont_fetch_network_prices(self):
        with patch.object(MarketData, "get_snapshot", side_effect=AssertionError("live request")):
            self.window.workspace.dashboard.refresh()
        self.assertIn(
            "Çevrimdışı", self.window.workspace.dashboard.status_label.text()
        )

    def test_cards_do_not_invent_live_data(self):
        self.assertEqual(
            set(self.window.workspace.dashboard.cards),
            {"xu100", "usdtry", "eurtry", "gold", "btc"},
        )
        self.assertTrue(all(
            card.value_label.text() == "—"
            for card in self.window.workspace.dashboard.cards.values()
        ))
