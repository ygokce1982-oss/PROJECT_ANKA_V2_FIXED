"""UI acceptance for a real Qt return / rolling Sharpe workstation."""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from scripts.anka_professional_toolchain_demo import Terminal, QSS


class MultiAssetQtAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(QSS)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.patch=patch.dict(os.environ,{"ANKA_LAYOUT_FILE":str(Path(self.tmp.name)/"layout.ini")})
        self.patch.start()
        self.win=Terminal()
        self.win.show()
        self.app.processEvents()

    def tearDown(self):
        self.win.close()
        self.app.processEvents()
        self.patch.stop()
        self.tmp.cleanup()

    def test_usable_terminal_tab_and_real_90d_charts(self):
        self.assertEqual(self.win.workspace_tabs.count(),2)
        self.win.workspace_tabs.setCurrentIndex(1)
        self.app.processEvents()
        panel=self.win.performance_panel
        self.assertEqual(panel.comparison.window,90)
        self.assertEqual(len(panel.comparison.series),5)
        self.assertEqual(len(panel.comparison.dates),523)
        self.assertTrue(panel.comparison.demo)
        self.assertTrue(panel.comparison.sources)
        self.assertFalse(panel.top_plot.grab().isNull())
        self.assertFalse(panel.bottom_plot.grab().isNull())

    def test_select_assets_updates_both_series(self):
        panel=self.win.performance_panel
        panel.checks["BIST100"].setChecked(False)
        self.assertEqual(len(panel.comparison.series),4)
        self.assertNotIn("BIST100",{x.symbol for x in panel.comparison.series})
        self.assertEqual(panel.top_plot.comparison,panel.bottom_plot.comparison)

    def test_dynamic_window_and_riskfree(self):
        panel=self.win.performance_panel
        panel.window.setCurrentText("60")
        panel.rf.setValue(6.0)
        self.assertEqual(panel.comparison.window,60)
        self.assertAlmostEqual(panel.comparison.risk_free_annual,.06)
        sharpe=panel.comparison.series[0].rolling_sharpe
        self.assertTrue(all(value is None for value in sharpe[:60]))
        self.assertIsNotNone(sharpe[60])

    def test_too_few_assets_disables_comparison(self):
        panel=self.win.performance_panel
        for symbol,checkbox in panel.checks.items():
            checkbox.setChecked(symbol=="GOLD")
        self.assertIsNone(panel.comparison)
        self.assertIn("en az iki",panel.summary.text())
        panel.checks["SP500"].setChecked(True)
        self.assertIsNotNone(panel.comparison)

    def test_period_switch_changes_sample_size(self):
        panel=self.win.performance_panel
        initial=len(panel.comparison.dates)
        panel.period.setCurrentText("1 yıl")
        self.assertLess(len(panel.comparison.dates),initial)
        panel.period.setCurrentText("Tüm tarih")
        self.assertGreater(len(panel.comparison.dates),initial)

    def test_local_csv_changes_real_chart_without_live_claim(self):
        file=Path(self.tmp.name)/"market.csv"
        file.write_text(
            """symbol,date,close,currency
AAA,2026-01-01,100,USD
AAA,2026-01-02,105,USD
AAA,2026-01-05,110,USD
BBB,2026-01-01,100,USD
BBB,2026-01-02,101,USD
BBB,2026-01-05,102,USD
""",
            encoding="utf-8",
        )
        panel=self.win.performance_panel
        self.assertTrue(panel.load_csv(file), msg=panel.summary.text())
        self.assertFalse(panel.comparison.demo)
        self.assertEqual(len(panel.comparison.series),2)
        self.assertIn("DOĞRULANMADI",panel.source_banner.text())
        self.assertIn("Kullanıcının yerel CSV",panel.notice.text())

    def test_navigation_back_to_existing_chart(self):
        self.win.workspace_tabs.setCurrentIndex(1)
        self.win.workspace_tabs.setCurrentIndex(0)
        self.assertEqual(self.win.chart.symbol,"THYAO")
        self.assertTrue(self.win._dock["Haber ve Araştırma"].isVisible())
        self.assertTrue(self.win.form.isVisible())


if __name__=="__main__":
    unittest.main()
