"""Persisted local alert history and real Qt manual refresh acceptance."""

import math
import os
import tempfile
import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QAbstractItemView, QApplication, QLabel, QPushButton

from core.offline_workbench import LocalStore, sample_bars
from ui.components.local_workbench import PaperPortfolioPage


def alert_state(store):
    return (
        store.connection.execute("SELECT * FROM alerts ORDER BY id").fetchall(),
        store.connection.execute(
            "SELECT * FROM alert_events ORDER BY alert_id,bar_time"
        ).fetchall(),
    )


def fixed_bars(price, days=0):
    return [
        replace(
            bar,
            time=(datetime.fromisoformat(bar.time) + timedelta(days=days)).isoformat(),
            open=price, high=price + 1, low=price - 1, close=price,
        )
        for bar in sample_bars()
    ]


class AlertHistoryStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "research.sqlite"
        self.store = LocalStore(self.path)

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def test_empty_history_is_read_only_and_omits_untriggered_alerts(self):
        self.assertEqual(self.store.alert_history(), [])
        self.store.add_alert("LOCAL_A", 110, 100)
        before = alert_state(self.store)
        changes = self.store.connection.total_changes
        self.assertEqual(self.store.alert_history(), [])
        self.assertEqual(alert_state(self.store), before)
        self.assertEqual(self.store.connection.total_changes, changes)

    def test_two_symbols_return_threshold_price_and_deterministic_ties(self):
        first = self.store.add_alert("LOCAL_A", 110, 100)
        second = self.store.add_alert("LOCAL_B", 210, 200)
        timestamp = "2026-01-02T00:00:00+00:00"
        self.assertEqual(self.store.check_alerts("LOCAL_A", 115, timestamp), 1)
        self.assertEqual(self.store.check_alerts("LOCAL_B", 220, timestamp), 1)
        expected = [
            {"alert_id": second, "symbol": "LOCAL_B", "threshold": 210,
             "price": 220, "bar_time": timestamp},
            {"alert_id": first, "symbol": "LOCAL_A", "threshold": 110,
             "price": 115, "bar_time": timestamp},
        ]
        self.assertEqual(self.store.alert_history(), expected)
        self.assertEqual(self.store.alert_history(1), expected[:1])

    def test_sort_uses_actual_instants_for_offsets_compact_iso_and_microseconds(self):
        stamps = [
            ("OFFSET", "2026-01-02T04:00:00+03:00"),
            ("UTC", "2026-01-02T01:30:00+00:00"),
            ("COMPACT", "20260102T020000+0000"),
            ("MICRO", "2026-01-02T02:00:00.000001+00:00"),
        ]
        for symbol, timestamp in reversed(stamps):
            self.store.add_alert(symbol, 110, 100)
            self.store.check_alerts(symbol, 111, timestamp)
        self.assertEqual(
            [row["symbol"] for row in self.store.alert_history()],
            ["MICRO", "COMPACT", "UTC", "OFFSET"],
        )

    def test_history_is_bounded_and_invalid_limits_preserve_records(self):
        identifier = self.store.add_alert("LOCAL_A", 110, 100)
        start = datetime(2026, 1, 1, tzinfo=UTC)
        with self.store.connection:
            self.store.connection.executemany(
                "INSERT INTO alert_events VALUES(?,?,?)",
                [(identifier, (start + timedelta(days=index)).isoformat(), 111)
                 for index in range(503)],
            )
        before = alert_state(self.store)
        self.assertEqual(len(self.store.alert_history()), 100)
        self.assertEqual(len(self.store.alert_history(500)), 500)
        self.assertEqual(
            [row["bar_time"] for row in self.store.alert_history(3)],
            [(start + timedelta(days=index)).isoformat() for index in (502, 501, 500)],
        )
        for invalid in (0, -1, 501, 1.5, True, "2", None):
            with self.subTest(limit=invalid), self.assertRaises(ValueError):
                self.store.alert_history(invalid)
        self.assertEqual(alert_state(self.store), before)

    def test_restart_repeated_equivalent_and_older_bars_do_not_duplicate_events(self):
        self.store.add_alert("LOCAL_A", 110, 100)
        self.assertEqual(self.store.check_alerts("LOCAL_A", 115, "2026-01-02T00:00:00Z"), 1)
        expected = self.store.alert_history()
        self.store.close()
        self.store = LocalStore(self.path)
        for price, timestamp in (
            (100, "2026-01-01T00:00:00Z"),
            (100, "2026-01-02T00:00:00Z"),
            (100, "2026-01-02T03:00:00+03:00"),
            (115, "2026-01-03T00:00:00Z"),
        ):
            self.assertEqual(self.store.check_alerts("LOCAL_A", price, timestamp), 0)
        self.assertEqual(self.store.alert_history(), expected)
        self.assertEqual(self.store.check_alerts("LOCAL_A", 100, "2026-01-04T00:00:00Z"), 0)
        self.assertEqual(self.store.check_alerts("LOCAL_A", 110, "2026-01-05T00:00:00Z"), 1)
        self.assertEqual(len(self.store.alert_history()), 2)

    def test_invalid_alert_inputs_preserve_history_and_crossing_state(self):
        self.store.add_alert("LOCAL_A", 110, 100)
        self.store.check_alerts("LOCAL_A", 115, "2026-01-02T00:00:00Z")
        before = alert_state(self.store)
        for price in (0, -1, math.nan, math.inf):
            with self.subTest(price=price), self.assertRaises(ValueError):
                self.store.check_alerts("LOCAL_A", price, "2026-01-03T00:00:00Z")
            with self.assertRaises(ValueError):
                self.store.add_alert("LOCAL_A", price, 100)
        for timestamp in ("", "invalid", "2026-01-03T00:00:00"):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                self.store.check_alerts("LOCAL_A", 100, timestamp)
        self.assertEqual(alert_state(self.store), before)
        self.assertEqual(self.store.check_alerts("LOCAL_A", 120, "2026-01-04T00:00:00Z"), 0)
        self.assertEqual(len(self.store.alert_history()), 1)

    def test_history_leaves_paper_trade_balances_and_constraints_unchanged(self):
        self.store.trade("LOCAL_A", "BUY", 10, 100)
        self.store.trade("LOCAL_A", "SELL", 5, 110)
        with self.assertRaises(ValueError):
            self.store.trade("LOCAL_A", "SELL", 6, 110)
        before = self.store.portfolio({"LOCAL_A": 110})
        self.store.add_alert("LOCAL_A", 110, 100)
        self.store.check_alerts("LOCAL_A", 115, "2026-01-02T00:00:00Z")
        self.store.alert_history()
        self.assertEqual(self.store.portfolio({"LOCAL_A": 110}), before)
        self.assertEqual(before["known_equity"], 100100)
        self.assertTrue(before["paper_only"])
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 2)


class AlertHistoryQtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.environment = patch.dict(
            os.environ, {"ANKA_STATE_DIR": self.temporary.name, "ANKA_OFFLINE": "1"}
        )
        self.environment.start()
        self.store = LocalStore(Path(self.temporary.name) / "research.sqlite")
        self.pages = []

    def tearDown(self):
        for page in self.pages:
            page.close()
            page.deleteLater()
        self.app.processEvents()
        self.store.close()
        self.environment.stop()
        self.temporary.cleanup()

    def page(self):
        page = PaperPortfolioPage()
        self.pages.append(page)
        page.resize(1100, 700)
        page.show()
        self.app.processEvents()
        return page

    def seed_two_symbols(self):
        self.store.execute(fixed_bars(100), "LOCAL_A")
        self.store.execute(fixed_bars(200), "LOCAL_B", origin="LOCAL_CSV")
        self.store.add_alert("LOCAL_A", 110, 100)
        self.store.add_alert("LOCAL_B", 210, 200)

    def click_refresh(self, page):
        button = next(
            item for item in page.findChildren(QPushButton)
            if item.text() == "Portföyü ve alarmları kontrol et"
        )
        button.click()
        self.app.processEvents()

    def table_rows(self, page):
        table = page.alert_history_table
        return [
            [table.item(row, column).text() for column in range(table.columnCount())]
            for row in range(table.rowCount())
        ]

    def test_empty_page_and_manual_refresh_show_read_only_history(self):
        page = self.page()
        self.click_refresh(page)
        self.assertEqual(page.alert_history_table.rowCount(), 0)
        self.assertEqual(page.alert_history_table.columnCount(), 4)
        self.assertEqual(
            page.alert_history_table.editTriggers(), QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.assertIn("Henüz tetiklenen alarm yok", page.alert_history_status.text())
        self.assertIn("Yeni alarm: 0", page.status.text())
        labels = " ".join(item.text() for item in page.findChildren(QLabel))
        self.assertIn("Örnek / yerel CSV", labels)
        self.assertIn("Gerçek hesap veya emir bağlantısı yok", labels)
        self.assertFalse(page.grab().isNull())

    def test_manual_refresh_checks_two_symbols_regardless_of_selection_and_reloads(self):
        self.seed_two_symbols()
        page = self.page()
        self.click_refresh(page)
        page.symbol.setCurrentIndex(page.symbol.findData("LOCAL_A"))
        self.store.execute(fixed_bars(115, 1), "LOCAL_A")
        self.store.execute(fixed_bars(215, 1), "LOCAL_B", origin="LOCAL_CSV")
        self.click_refresh(page)
        self.assertEqual(page.symbol.currentData(), "LOCAL_A")
        self.assertIn("Yeni alarm: 2", page.status.text())
        rows = self.table_rows(page)
        self.assertEqual({row[0] for row in rows}, {"LOCAL_A", "LOCAL_B"})
        self.assertEqual(rows[0][1:3], ["210.0000", "215.0000"])
        self.assertEqual(rows[0][3], fixed_bars(215, 1)[-1].time)
        page.symbol.setCurrentIndex(page.symbol.findData("LOCAL_B"))
        self.click_refresh(page)
        self.assertIn("Yeni alarm: 0", page.status.text())
        self.assertEqual(self.table_rows(page), rows)
        before = alert_state(self.store)
        page.close()
        reopened = self.page()
        self.assertEqual(self.table_rows(reopened), rows)
        self.assertEqual(alert_state(self.store), before)
        self.click_refresh(reopened)
        self.assertIn("Yeni alarm: 0", reopened.status.text())
        self.assertEqual(self.table_rows(reopened), rows)

    def test_older_import_after_restart_cannot_rearm_alerts(self):
        self.seed_two_symbols()
        self.store.execute(fixed_bars(115, 1), "LOCAL_A")
        self.store.execute(fixed_bars(215, 1), "LOCAL_B", origin="LOCAL_CSV")
        page = self.page()
        self.click_refresh(page)
        rows = self.table_rows(page)
        page.close()
        self.store.execute(fixed_bars(99, -1), "LOCAL_A")
        self.store.execute(fixed_bars(199, -1), "LOCAL_B", origin="LOCAL_CSV")
        reopened = self.page()
        self.click_refresh(reopened)
        self.assertIn("Yeni alarm: 0", reopened.status.text())
        self.assertEqual(self.table_rows(reopened), rows)
        self.store.execute(fixed_bars(116, 2), "LOCAL_A")
        self.store.execute(fixed_bars(216, 2), "LOCAL_B", origin="LOCAL_CSV")
        self.click_refresh(reopened)
        self.assertIn("Yeni alarm: 0", reopened.status.text())
        self.assertEqual(self.table_rows(reopened), rows)

    def test_loading_history_does_not_automatically_check_new_prices(self):
        self.seed_two_symbols()
        self.store.execute(fixed_bars(115, 1), "LOCAL_A")
        self.store.execute(fixed_bars(215, 1), "LOCAL_B", origin="LOCAL_CSV")
        before = alert_state(self.store)
        page = self.page()
        self.assertEqual(page.alert_history_table.rowCount(), 0)
        self.assertEqual(alert_state(self.store), before)
        self.app.processEvents()
        self.assertEqual(alert_state(self.store), before)
        self.click_refresh(page)
        self.assertEqual(page.alert_history_table.rowCount(), 2)

    def test_refresh_and_history_preserve_paper_account_and_rejected_trade(self):
        self.seed_two_symbols()
        self.store.trade("LOCAL_A", "BUY", 2, 100)
        page = self.page()
        self.click_refresh(page)
        page.symbol.setCurrentIndex(page.symbol.findData("LOCAL_A"))
        before = self.store.portfolio({"LOCAL_A": 100})
        page.quantity.setValue(3)
        page.trade("SELL")
        self.assertIn("yetersiz", page.status.text())
        self.click_refresh(page)
        self.assertEqual(self.store.portfolio({"LOCAL_A": 100}), before)
        self.assertEqual(page.table.item(0, 1).text(), "99800.0000")
        self.assertEqual(page.table.item(1, 1).text(), "100000.0000")
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 1)
