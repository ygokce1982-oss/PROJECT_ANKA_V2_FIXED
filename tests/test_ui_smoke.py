"""Offscreen smoke test for the ANKA Finans desktop shell."""

import os
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from ui.components.dashboard import Dashboard
from ui.main_window import MainWindow


class MainWindowSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_all_six_sections_construct_without_network(self) -> None:
        with patch.object(Dashboard, "refresh", return_value=None):
            window = MainWindow()
            try:
                self.assertEqual(window.workspace.count(), 6)
                self.assertIsNotNone(window.centralWidget())
                self.assertIsNotNone(window.statusBar())
            finally:
                window.close()


if __name__ == "__main__":
    unittest.main()
