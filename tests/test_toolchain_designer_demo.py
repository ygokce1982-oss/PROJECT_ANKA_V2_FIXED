"""Real desktop toolchain prototype acceptance: Qt .ui, docking and native drawing."""
from __future__ import annotations
import os
from pathlib import Path
import sys
import unittest

os.environ["QT_QPA_PLATFORM"]="offscreen"
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication
from scripts.anka_professional_toolchain_demo import Terminal, demo_candles, QSS


class ProfessionalToolchainDemoAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application=QApplication.instance() or QApplication([])
        cls.application.setStyleSheet(QSS)

    def setUp(self):
        self.window=Terminal()
        self.window.show()
        self.application.processEvents()

    def tearDown(self):
        self.window.close()
        self.application.processEvents()

    def test_designer_layout_is_really_loaded(self):
        self.assertEqual(self.window.form.objectName(),"ChartWorkbench")
        self.assertEqual(self.window.chart.parentWidget().objectName(),"chartSlot")
        self.assertEqual(len(self.window._dock),5)

    def test_watchlist_selection_changes_real_chart(self):
        self.window.select_row(1,0)
        self.assertEqual(self.window.chart.symbol,"ASELS")
        self.assertIn("ASELS",self.window.symbol_title.text())
        self.assertEqual(len(self.window.chart.series),125)

    def test_watch_filter(self):
        self.window.filter_watch("koç")
        self.assertFalse(self.window.watch.isRowHidden(7))
        self.assertTrue(self.window.watch.isRowHidden(0))
        self.window.filter_watch("")
        self.assertFalse(self.window.watch.isRowHidden(0))

    def test_panels_can_float_and_restore(self):
        depth=self.window._dock["Piyasa Derinliği"]
        self.window.float_panels()
        self.assertTrue(depth.isFloating())
        self.window.restore_default()
        self.assertFalse(depth.isFloating())

    def test_candles_are_deterministic_synthetic_and_grabbable(self):
        self.assertEqual(demo_candles("THYAO"),demo_candles("THYAO"))
        self.window.set_chart_zoom(100)
        self.assertEqual(self.window.chart.visible,100)
        self.assertFalse(self.window.chart.grab().isNull())

    def test_real_orders_disabled_and_demo_labeled(self):
        from PySide6.QtWidgets import QPushButton,QLabel
        risk=self.window._dock["Portföy ve Risk"]
        buttons=risk.findChildren(QPushButton)
        self.assertTrue(any("AL / SAT" in b.text() and not b.isEnabled() for b in buttons))
        self.assertIn("ÖRNEK VERİ", self.window.form.findChild(QLabel,"symbolDemo").text())


if __name__ == "__main__":
    unittest.main()
