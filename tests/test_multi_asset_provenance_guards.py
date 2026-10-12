"""Regression cases for fail-closed price provenance and Sharpe session gaps."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from core.multi_asset_comparison import AssetHistory, compare_assets

ASOF = "2026-10-11T18:00:00Z"


def asset(symbol, days, prices):
    return AssetHistory(
        symbol=symbol,
        currency="USD",
        observations=tuple(zip(days, prices, strict=True)),
        source="TEST_SYNTHETIC_NO_MARKET_DATA",
        asof_utc=ASOF,
        demo=True,
    )


class MultiAssetProvenanceGuardTests(unittest.TestCase):
    def test_future_asof_rejected_even_with_valid_timezone_offset(self):
        days = ["2026-01-02", "2026-01-05", "2026-01-06"]
        a = asset("A", days, [100, 102, 106])
        b = asset("B", days, [100, 101, 104])
        future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        for value in (future, (datetime.now(timezone.utc) + timedelta(days=2)).astimezone(timezone(timedelta(hours=3))).isoformat()):
            with self.subTest(asof=value):
                with self.assertRaisesRegex(ValueError, "FUTURE_SOURCE_TIMESTAMP"):
                    compare_assets([a, replace(b, asof_utc=value)], window=2)

    def test_one_missing_session_does_not_become_one_daily_return(self):
        a = asset("A", ["2026-01-05","2026-01-06","2026-01-07","2026-01-08","2026-01-09"],
                  [100, 110, 120, 135, 160])
        b = asset("B", ["2026-01-05","2026-01-07","2026-01-08","2026-01-09"],
                  [100, 125, 140, 155])
        result = compare_assets([a, b], window=2, risk_free_annual=0)
        self.assertEqual(result.dates, ("2026-01-05","2026-01-07","2026-01-08","2026-01-09"))
        self.assertAlmostEqual(result.series[0].cumulative_percent[-1], 60)
        self.assertIsNone(result.series[0].rolling_sharpe[2])
        self.assertIsNone(result.series[1].rolling_sharpe[2])
        self.assertIsNotNone(result.series[0].rolling_sharpe[3])
        self.assertTrue(any("KNOWN_MISSING_SESSIONS" in warning for warning in result.warnings))

    def test_weekend_without_observed_session_does_not_falsely_create_gap(self):
        days = ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"]
        a = asset("A", days, [100, 101, 103, 106])
        b = asset("B", days, [200, 199, 200, 205])
        result = compare_assets([a, b], window=2, risk_free_annual=0)
        self.assertIsNotNone(result.series[0].rolling_sharpe[-1])
        self.assertFalse(any("KNOWN_MISSING_SESSIONS" in w for w in result.warnings))

    def test_unverified_adjusted_close_and_calendar_disclosed(self):
        days = ["2026-01-02", "2026-01-05", "2026-01-06"]
        result = compare_assets([
            asset("A", days, [100,102,105]), asset("B", days, [200,201,203])
        ], window=2)
        self.assertTrue(any("adjusted-close provenance" in warning for warning in result.warnings))


if __name__ == "__main__":
    unittest.main()
