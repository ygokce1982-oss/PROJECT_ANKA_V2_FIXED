"""Offscreen ANKA Finans visible shell acceptance without live providers."""
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


class TerminalShellAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_window_title_sections_and_frame_capture(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"ANKA_OFFLINE": "1", "ANKA_DISABLE_LIVE": "1", "ANKA_STATE_DIR": directory}
        ):
            window = MainWindow()
            try:
                self.assertEqual(
                    window.windowTitle(), "ANKA Finans | Profesyonel Piyasa Terminali"
                )
                self.assertEqual(window.workspace.count(), 6)
                window.show()
                self.app.processEvents()
                self.assertFalse(window.grab().isNull())
            finally:
                window.close()
