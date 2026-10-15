"""Automatic saved-local-analysis alerts through real Qt widgets and SQLite."""

from contextlib import ExitStack, closing
from dataclasses import replace
from datetime import datetime, timedelta
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtWidgets import QApplication, QPushButton

from core.offline_workbench import LocalStore, sample_bars
from ui.components.local_workbench import LocalWorkbenchPage, PaperPortfolioPage
from ui.main_window import MainWindow


def bars_at(price, days=0):
    return [replace(
        bar, time=(datetime.fromisoformat(bar.time) + timedelta(days=days)).isoformat(),
        open=price, high=price + 1, low=price - 1, close=price,
    ) for bar in sample_bars()]


class LocalAlertNoticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stack = ExitStack()
        self.directory = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.stack.enter_context(patch.dict(os.environ, {
            "ANKA_OFFLINE": "1", "ANKA_STATE_DIR": str(self.directory),
            "ANKA_LAYOUT_FILE": str(self.directory / "layout.ini"),
        }))
        self.path = self.directory / "research.sqlite"
        self.store = LocalStore(self.path)
        self.widgets = []

    def tearDown(self):
        for widget in self.widgets:
            widget.close()
            widget.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.processEvents()
        self.store.close()
        self.stack.close()

    def page(self):
        page = LocalWorkbenchPage()
        self.widgets.append(page)
        return page

    def window(self):
        window = MainWindow()
        self.widgets.append(window)
        window.show()
        self.app.processEvents()
        return window

    def run_price(self, page, symbol, price, days=1, origin="SAMPLE"):
        page.symbol.setText(symbol)
        page.run_bars(bars_at(price, days), origin)
        self.app.processEvents()

    def seed(self, symbol="LOCAL_A", threshold=110, previous=100):
        return self.store.add_alert(symbol, threshold, previous)

    def events(self):
        return self.store.connection.execute(
            "SELECT * FROM alert_events ORDER BY alert_id,bar_time"
        ).fetchall()

    def capture(self, page):
        messages = []
        page.local_alerts_created.connect(lambda *args: messages.append(args))
        return messages

    def paper_state(self):
        return {table: self.store.connection.execute(
            f"SELECT * FROM {table} ORDER BY rowid"
        ).fetchall() for table in ("account", "holdings", "trades")}

    def test_two_symbols_emit_only_their_new_crossings_with_saved_origin_and_count(self):
        self.seed()
        self.seed(threshold=112)
        self.seed("LOCAL_B", 210, 200)
        page = self.page()
        messages = self.capture(page)
        self.run_price(page, " local_a ", 115)
        self.assertEqual(messages, [("LOCAL_A", 2, "SAMPLE")])
        self.assertEqual({row["symbol"] for row in self.store.alert_history()}, {"LOCAL_A"})
        self.run_price(page, "LOCAL_B", 215, origin="LOCAL_CSV")
        self.assertEqual(messages[-1], ("LOCAL_B", 1, "LOCAL_CSV"))
        self.assertEqual(len(self.events()), 3)
        self.assertEqual(self.store.latest("LOCAL_B")["analysis"]["close"], 215)

    def test_repeat_older_and_reopened_pages_do_not_notify_or_rearm(self):
        self.seed()
        page = self.page()
        messages = self.capture(page)
        self.run_price(page, "LOCAL_A", 115)
        original = self.events()
        self.run_price(page, "LOCAL_A", 115)
        self.run_price(page, "LOCAL_A", 90, days=0)
        page.close()
        reopened = self.page()
        reopened_messages = self.capture(reopened)
        self.assertEqual(reopened_messages, [])
        self.run_price(reopened, "LOCAL_A", 90, days=1)
        self.run_price(reopened, "LOCAL_A", 116, days=2)
        self.assertEqual(messages, [("LOCAL_A", 1, "SAMPLE")])
        self.assertEqual(reopened_messages, [])
        self.assertEqual(self.events(), original)
        self.run_price(reopened, "LOCAL_A", 90, days=3)
        self.run_price(reopened, "LOCAL_A", 110, days=4)
        self.assertEqual(reopened_messages, [("LOCAL_A", 1, "SAMPLE")])
        self.assertEqual(len(self.events()), 2)

    def test_invalid_bars_origin_or_symbol_cannot_check_or_notify(self):
        self.seed()
        page = self.page()
        messages = self.capture(page)
        for bars, origin, symbol in (([], "SAMPLE", "LOCAL_A"),
                                     (bars_at(115), "LIVE", "LOCAL_A"),
                                     (bars_at(115), "SAMPLE", " ")):
            with self.subTest(origin=origin, symbol=symbol), patch.object(
                LocalStore, "check_alerts", side_effect=AssertionError("No invalid checks")
            ):
                page.symbol.setText(symbol)
                page.run_bars(bars, origin)
                self.assertIsNone(page.result)
                self.assertIn("Analiz başarısız", page.status.text())
        self.assertEqual(messages, [])
        self.assertEqual(self.events(), [])
        self.assertIsNone(self.store.latest())

    def test_failed_save_does_not_check_or_notify(self):
        self.seed()
        page = self.page()
        messages = self.capture(page)
        with patch.object(LocalStore, "execute", side_effect=sqlite3.OperationalError("disk full")), \
                patch.object(LocalStore, "check_alerts") as check:
            self.run_price(page, "LOCAL_A", 115)
        check.assert_not_called()
        self.assertIsNone(page.result)
        self.assertIn("disk full", page.status.text())
        self.assertEqual(messages, [])
        self.assertEqual(self.events(), [])
        self.assertIsNone(self.store.latest())

    def test_alert_check_failure_keeps_saved_analysis_and_reports_separate_failure(self):
        self.seed()
        page = self.page()
        messages = self.capture(page)
        with patch.object(LocalStore, "check_alerts", side_effect=sqlite3.OperationalError("check error")):
            self.run_price(page, "LOCAL_A", 115)
        self.assertEqual(page.result["digest"], self.store.latest()["digest"])
        self.assertEqual(page.chart.values[-1], 115)
        self.assertGreater(page.table.rowCount(), 0)
        self.assertIn("kalıcı kayda yazıldı", page.status.text())
        self.assertIn("Alarm kontrolü başarısız", page.status.text())
        self.assertIn("check error", page.status.text())
        self.assertNotIn("Analiz başarısız", page.status.text())
        self.assertEqual(messages, [])

    def test_database_is_closed_before_signal_and_handler_can_open_write_transaction(self):
        self.seed()
        connections, observed = [], []

        class TrackedStore(LocalStore):
            def __init__(inner_self, path):
                super().__init__(path)
                connections.append(inner_self.connection)

        page = self.page()

        def receive(*args):
            try:
                connections[-1].execute("SELECT 1")
                observed.append("still open")
            except sqlite3.ProgrammingError:
                observed.append("closed")
            with closing(sqlite3.connect(self.path, timeout=0)) as connection:
                connection.execute("BEGIN IMMEDIATE")
                observed.append(connection.execute("SELECT COUNT(*) FROM alert_events").fetchone()[0])

        page.local_alerts_created.connect(receive)
        with patch("ui.components.local_workbench.LocalStore", TrackedStore):
            self.run_price(page, "LOCAL_A", 115)
        self.assertEqual(observed, ["closed", 1])

    def test_main_sample_button_banner_remains_across_tabs_and_history_action_navigates(self):
        self.seed("DEMO1", 110, 100)
        window = self.window()
        page = window.workspace.widget(1)
        window.sidebar.setCurrentRow(1)
        next(button for button in page.findChildren(QPushButton)
             if button.text() == "Örnek veriyi analiz et").click()
        self.app.processEvents()
        self.assertTrue(window.local_alert_notice.isVisible())
        self.assertFalse(window.local_alert_notice.isWindow())
        self.assertIsNone(self.app.activeModalWidget())
        self.assertIn("DEMO1", window.local_alert_notice_label.text())
        self.assertIn("1 yeni alarm", window.local_alert_notice_label.text())
        self.assertIn("ÖRNEK", window.local_alert_notice_label.text())
        self.assertIn("canlı veri değil", window.local_alert_notice_label.text())
        self.assertIn("Cihaz/telefon bildirimi yok", window.local_alert_notice_label.text())
        self.assertEqual(window.workspace.currentIndex(), 1)
        for index in (0, 2, 3, 4, 5):
            window.sidebar.setCurrentRow(index)
            self.app.processEvents()
            self.assertTrue(window.local_alert_notice.isVisible())
        window.local_alert_history_button.click()
        self.assertEqual(window.workspace.currentIndex(), 4)
        self.assertEqual(window.sidebar.currentRow(), 4)
        self.assertEqual(window.workspace.widget(4).alert_history_table.rowCount(), 1)
        window.local_alert_dismiss_button.click()
        self.assertTrue(window.local_alert_notice.isHidden())
        self.assertEqual(len(self.events()), 1)

    def test_actual_csv_import_updates_hidden_history_without_fx_backlog_or_paper_mutation(self):
        self.store.execute(bars_at(200), "LOCAL_B", origin="LOCAL_CSV", currency="USD")
        self.store.trade("LOCAL_B", "BUY", 2, 200, currency="USD", fx_rates={"USD": 30})
        self.seed("LOCAL_B", 210, 200)
        self.seed("BACKLOG", 110, 100)
        self.store.execute(bars_at(115), "BACKLOG")
        before = self.paper_state()
        window = self.window()
        page, portfolio = window.workspace.widget(1), window.workspace.widget(4)
        selected = portfolio.symbol.currentData()
        page.symbol.setText("LOCAL_B")
        page.currency.setCurrentText("USD")
        window.sidebar.setCurrentRow(2)
        path = self.directory / "local.csv"
        data = bars_at(215, 1)
        path.write_text("time,open,high,low,close,volume\n" + "\n".join(
            f"{bar.time},{bar.open},{bar.high},{bar.low},{bar.close},{bar.volume}" for bar in data
        ), encoding="utf-8")
        with patch("ui.components.local_workbench.QFileDialog.getOpenFileName",
                   return_value=(str(path), "CSV")), \
                patch.object(PaperPortfolioPage, "refresh", side_effect=AssertionError("No refresh")), \
                patch.object(LocalStore, "portfolio", side_effect=AssertionError("No FX valuation")):
            page.import_csv()
            self.app.processEvents()
        self.assertEqual(window.workspace.currentIndex(), 2)
        self.assertEqual(portfolio.symbol.currentData(), selected)
        self.assertFalse(portfolio.isVisible())
        self.assertEqual(portfolio.alert_history_table.rowCount(), 1)
        self.assertEqual(portfolio.alert_history_table.item(0, 0).text(), "LOCAL_B")
        self.assertIn("YEREL CSV", window.local_alert_notice_label.text())
        self.assertTrue(window.local_alert_notice.isVisible())
        self.assertEqual({row["symbol"] for row in self.store.alert_history()}, {"LOCAL_B"})
        self.assertEqual(self.paper_state(), before)

    def test_dismissed_notice_does_not_reappear_for_duplicate_or_old_import(self):
        self.seed()
        window = self.window()
        page = window.workspace.widget(1)
        self.run_price(page, "LOCAL_A", 115)
        window.local_alert_dismiss_button.click()
        self.run_price(page, "LOCAL_A", 115)
        self.run_price(page, "LOCAL_A", 90, days=0)
        self.assertTrue(window.local_alert_notice.isHidden())
        self.assertEqual(window.workspace.widget(4).alert_history_table.rowCount(), 1)

    def test_reopen_loads_history_without_replaying_notice_or_evaluating_backlog(self):
        self.seed()
        window = self.window()
        self.run_price(window.workspace.widget(1), "LOCAL_A", 115)
        window.close()
        self.seed("BACKLOG", 110, 100)
        self.store.execute(bars_at(115), "BACKLOG")
        before = self.events()
        with patch.object(LocalStore, "check_alerts", side_effect=AssertionError("No reopen check")):
            reopened = self.window()
        self.assertTrue(reopened.local_alert_notice.isHidden())
        self.assertEqual(reopened.workspace.widget(4).alert_history_table.rowCount(), 1)
        self.assertEqual(self.events(), before)

    def test_banner_treats_user_symbol_as_plain_text(self):
        symbol = "<b>LOCAL_A</b>"
        self.seed(symbol.upper())
        window = self.window()
        self.run_price(window.workspace.widget(1), symbol, 115)
        self.assertEqual(window.local_alert_notice_label.textFormat(), Qt.TextFormat.PlainText)
        self.assertIn(symbol.upper(), window.local_alert_notice_label.text())

    def test_history_read_failure_still_delivers_notice_and_keeps_saved_result(self):
        self.seed()
        window = self.window()
        page = window.workspace.widget(1)
        with patch.object(LocalStore, "alert_history", side_effect=sqlite3.OperationalError("history error")):
            self.run_price(page, "LOCAL_A", 115)
        self.assertTrue(window.local_alert_notice.isVisible())
        self.assertIn("history error", window.workspace.widget(4).alert_history_status.text())
        self.assertEqual(page.result["digest"], self.store.latest()["digest"])
        self.assertNotIn("Analiz başarısız", page.status.text())
        self.assertEqual(len(self.events()), 1)

    def test_banner_render_failure_does_not_relabel_saved_analysis_as_failed(self):
        self.seed()
        window = self.window()
        page = window.workspace.widget(1)
        with patch.object(window.local_alert_notice_label, "setText",
                          side_effect=RuntimeError("display error")):
            self.run_price(page, "LOCAL_A", 115)
        self.assertEqual(page.result["digest"], self.store.latest()["digest"])
        self.assertIn("kalıcı kayda yazıldı", page.status.text())
        self.assertNotIn("Analiz başarısız", page.status.text())
        self.assertIn("bildirim gösterilemedi", window.statusBar().currentMessage())
        self.assertEqual(len(self.events()), 1)
