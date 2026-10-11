import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from core.offline_workbench import Bar, LocalStore, analysis, backtest, read_csv, sample_bars


class OfflineWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "research.sqlite"
        self.store = LocalStore(self.path)

    def tearDown(self):
        self.store.close()
        self.temporary.cleanup()

    def test_analysis_roundtrip_idempotence_and_restart(self):
        result = self.store.execute(sample_bars())
        self.assertFalse(result["live"])
        self.assertEqual(result["origin"], "SAMPLE")
        self.assertEqual(self.store.execute(sample_bars())["digest"], result["digest"])
        self.assertEqual(
            self.store.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0], 1
        )
        other = LocalStore(self.path)
        try:
            self.assertEqual(other.latest()["digest"], result["digest"])
            self.assertEqual(other.latest()["analysis"], result["analysis"])
        finally:
            other.close()

    def test_bad_bar_never_persists(self):
        for bad in (
            replace(sample_bars()[5], close=math.nan),
            replace(sample_bars()[5], low=100000),
            replace(sample_bars()[5], volume=-1),
            replace(sample_bars()[5], time=sample_bars()[4].time),
        ):
            bars = sample_bars()
            bars[5] = bad
            with self.assertRaises(ValueError):
                self.store.execute(bars)
        self.assertIsNone(self.store.latest())

    def test_offline_origin_cannot_claim_live(self):
        with self.assertRaises(ValueError):
            self.store.execute(sample_bars(), origin="LIVE")

    def test_flat_series_rsi_and_drawdown(self):
        bars = [replace(bar, open=100, high=101, low=99, close=100) for bar in sample_bars()]
        result = analysis(bars)
        self.assertEqual(result["rsi14_simple"], 50)
        self.assertEqual(result["maximum_drawdown"], 0)
        self.assertEqual(result["bar_volatility"], 0)
        self.assertEqual(result["regime"], "yatay")

    def test_backtest_executes_next_open_and_cost_reduces_equity(self):
        bars = [
            Bar(bar.time, 100 + i, 101 + i, 99 + i, 100 + i, 1)
            for i, bar in enumerate(sample_bars()[:35])
        ]
        result = backtest(bars, 0)
        self.assertEqual(result["orders"], 1)
        self.assertAlmostEqual(result["equity"], 10000 * 134 / 120)
        self.assertLess(backtest(bars, 0.01)["equity"], result["equity"])

    def test_future_data_does_not_change_previous_equity(self):
        bars = sample_bars()
        before = backtest(bars)["equity_curve"]
        changed = bars[:]
        for i in range(100, len(changed)):
            changed[i] = replace(changed[i], open=200, close=200, high=201, low=199)
        after = backtest(changed)["equity_curve"]
        self.assertEqual(before[:81], after[:81])

    def test_paper_trade_constraints_and_restart(self):
        self.store.trade("DEMO1", "BUY", 10, 100)
        with self.assertRaises(ValueError):
            self.store.trade("DEMO1", "SELL", 11, 100)
        with self.assertRaises(ValueError):
            self.store.trade("DEMO1", "BUY", 100000, 100)
        self.store.trade("DEMO1", "SELL", 5, 110)
        report = self.store.portfolio({"DEMO1": 110})
        self.assertEqual(report["cash"], 99550)
        self.assertEqual(report["known_equity"], 100100)
        self.assertEqual(report["stress_equity"], 99990)
        self.assertEqual(
            self.store.connection.execute("SELECT COUNT(*) FROM trades").fetchone()[0], 2
        )

    def test_missing_price_does_not_claim_complete_valuation(self):
        self.store.trade("MISSING", "BUY", 1, 100)
        report = self.store.portfolio({})
        self.assertEqual(report["unpriced"], ["MISSING"])
        self.assertFalse(report["valuation_complete"])

    def test_alert_is_persistent_edge_triggered_and_time_ordered(self):
        self.store.add_alert("DEMO1", 110, 100)
        self.assertEqual(self.store.check_alerts("DEMO1", 115, "2026-01-02T00:00:00+00:00"), 1)
        self.assertEqual(self.store.check_alerts("DEMO1", 100, "2026-01-01T00:00:00+00:00"), 0)
        self.assertEqual(self.store.check_alerts("DEMO1", 115, "2026-01-03T00:00:00+00:00"), 0)
        other = LocalStore(self.path)
        try:
            self.assertEqual(other.check_alerts("DEMO1", 120, "2026-01-03T00:00:00+00:00"), 0)
            self.assertEqual(
                other.connection.execute("SELECT COUNT(*) FROM alert_events").fetchone()[0], 1
            )
        finally:
            other.close()

    def test_csv_headers_and_malformed_rows_rejected(self):
        path = Path(self.temporary.name) / "input.csv"
        for content in ("foo,bar\n1,2", "time,open,high,low,close,volume\n2026-01-01,1,2"):
            path.write_text(content)
            with self.assertRaises(ValueError):
                read_csv(path)
