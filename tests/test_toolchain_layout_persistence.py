"""Real persisted professional ANKA workspace acceptance (isolated settings)."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from scripts.anka_professional_toolchain_demo import Terminal, QSS


class SavedWorkspaceAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(QSS)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.filename = Path(self.tmp.name) / "layout.ini"
        self.environment = patch.dict(os.environ, {"ANKA_LAYOUT_FILE": str(self.filename)})
        self.environment.start()
        self.win = Terminal()
        self.win.show()
        self.app.processEvents()

    def tearDown(self):
        self.win.close()
        self.app.processEvents()
        self.environment.stop()
        self.tmp.cleanup()

    def test_layout_is_saved_and_restored_after_restart(self):
        self.win.choose_symbol("ASELS")
        self.win.set_chart_zoom(100)
        self.win.float_panels()
        self.app.processEvents()
        self.assertTrue(self.win._dock["Piyasa Derinliği"].isFloating())
        self.assertTrue(self.win.save_layout())
        self.assertTrue(self.filename.is_file())
        self.win.close()
        second = Terminal()
        second.show()
        self.app.processEvents()
        try:
            self.assertEqual(second.chart.symbol, "ASELS")
            self.assertEqual(second.chart.visible, 100)
            self.assertTrue(second._dock["Piyasa Derinliği"].isFloating())
            self.assertTrue(second._dock["Portföy ve Risk"].isFloating())
        finally:
            second.close()

    def test_no_file_without_explicit_save(self):
        self.assertFalse(self.filename.exists())

    def test_invalid_schema_safe_fallback(self):
        settings = QSettings(str(self.filename), QSettings.Format.IniFormat)
        settings.setValue("layout/schema", 999)
        settings.sync()
        other = Terminal()
        try:
            self.assertEqual(other.chart.symbol, "THYAO")
            self.assertFalse(other._dock["Piyasa Derinliği"].isFloating())
        finally:
            other.close()

    def test_reset_layout_clears_saved_file_and_restores_defaults(self):
        self.win.choose_symbol("GARAN")
        self.win.set_chart_zoom(100)
        self.win.float_panels()
        self.assertTrue(self.win.save_layout())
        self.assertTrue(self.filename.exists())
        self.assertTrue(self.win.restore_default())
        self.assertFalse(self.filename.exists())
        self.assertEqual(self.win.chart.symbol, "THYAO")
        self.assertEqual(self.win.chart.visible, 78)
        self.assertFalse(self.win._dock["Piyasa Derinliği"].isFloating())

    def test_corrupt_settings_file_does_not_crash(self):
        self.filename.write_text("NOT_A_VALID_INI_FILE[!!!", encoding="utf-8")
        other = Terminal()
        try:
            self.assertEqual(other.chart.symbol, "THYAO")
            self.assertFalse(other._dock["Piyasa Derinliği"].isFloating())
        finally:
            other.close()
