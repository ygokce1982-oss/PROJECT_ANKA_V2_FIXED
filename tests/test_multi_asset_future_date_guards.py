"""Frozen UTC regression tests for fail-closed observation calendar dates."""
import os
import unittest
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from core.multi_asset_comparison import AssetHistory, compare_assets
from core.multi_asset_csv import load_price_csv


NOW_UTC = datetime(2026, 10, 12, 23, 58, tzinfo=timezone.utc)
ASOF_UTC = (NOW_UTC - timedelta(days=1)).isoformat()
HISTORICAL_DAYS = ("2026-10-09", "2026-10-10", "2026-10-11")


class FuturePriceDateTests(unittest.TestCase):
    def setUp(self):
        self.clock = self.enterContext(
            patch("core.multi_asset_comparison.datetime", wraps=datetime)
        )
        self.clock.now.return_value = NOW_UTC

    def make(self, symbol, days, *, asof=ASOF_UTC):
        return AssetHistory(
            symbol,
            "USD",
            tuple((day, 100.0 + i * (i + 1)) for i, day in enumerate(days)),
            "TEST_UNVERIFIED_NO_MARKET_DATA",
            asof,
            True,
        )

    def compare(self, days):
        return compare_assets(
            [self.make("A", days), self.make("B", days)],
            window=2,
            risk_free_annual=0,
        )

    def write_csv(self, path, days_a, days_b):
        rows = ["symbol,date,close,currency"]
        for symbol, days in (("A", days_a), ("B", days_b)):
            rows.extend(f"{symbol},{day},{100 + i},USD" for i, day in enumerate(days))
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        # Fix provenance metadata too; observations may validly postdate file mtime.
        timestamp = (NOW_UTC - timedelta(days=2)).timestamp()
        os.utime(path, (timestamp, timestamp))

    def test_comparison_samples_current_utc_time_once(self):
        self.compare(HISTORICAL_DAYS)
        self.clock.now.assert_called_once_with(timezone.utc)

    def test_tomorrow_rejected_even_near_utc_midnight(self):
        days = (*HISTORICAL_DAYS, "2026-10-13")
        with self.assertRaisesRegex(ValueError, "FUTURE_PRICE_DATE"):
            self.compare(days)

    def test_later_future_observation_rejected(self):
        days = (*HISTORICAL_DAYS, "2026-10-14")
        with self.assertRaisesRegex(ValueError, "FUTURE_PRICE_DATE"):
            self.compare(days)

    def test_future_non_common_observation_rejected_in_every_asset(self):
        for future_symbol in ("A", "B"):
            with self.subTest(future_symbol=future_symbol):
                assets = [
                    self.make(
                        symbol,
                        (*HISTORICAL_DAYS, "2026-10-13")
                        if symbol == future_symbol else HISTORICAL_DAYS,
                    )
                    for symbol in ("A", "B")
                ]
                with self.assertRaisesRegex(ValueError, "FUTURE_PRICE_DATE"):
                    compare_assets(assets, window=2)

    def test_historical_observations_still_compute(self):
        result = self.compare(HISTORICAL_DAYS)
        self.assertEqual(result.dates, HISTORICAL_DAYS)
        self.assertIsNotNone(result.series[0].rolling_sharpe[-1])

    def test_today_accepted_even_with_earlier_source_timestamp(self):
        days = (*HISTORICAL_DAYS, NOW_UTC.date().isoformat())
        result = self.compare(days)
        self.assertEqual(result.dates, days)

    def test_noncanonical_basic_iso_date_rejected(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            self.compare(("2026-10-09", "20261010", "2026-10-11"))

    def test_noncanonical_extended_week_date_rejected(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            self.compare(("2026-10-09", "2026-W41-6", "2026-10-11"))

    def test_noncanonical_basic_week_date_rejected(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            self.compare(("2026-10-09", "2026W416", "2026-10-11"))

    def test_nonstring_observation_dates_rejected(self):
        for value in (None, 20261010, True, date(2026, 10, 10)):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid ISO date"):
                    self.compare(("2026-10-09", value, "2026-10-11"))

    def test_invalid_observation_dates_rejected(self):
        for value in (
            "2026-02-30", "2026-10-00", "2026-13-01", "",
            "2026-10-10T00:00:00Z", " 2026-10-10", "2026-10-10 ",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "invalid ISO date"):
                    self.compare(("2026-10-09", value, "2026-10-11"))

    def test_csv_rejects_future_non_common_observation(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            self.write_csv(path, (*HISTORICAL_DAYS, "2026-10-13"), HISTORICAL_DAYS)
            with self.assertRaisesRegex(ValueError, "FUTURE_PRICE_DATE"):
                load_price_csv(path)

    def test_csv_rejects_noncanonical_basic_iso_date(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            days = ("2026-10-09", "20261010", "2026-10-11")
            self.write_csv(path, days, HISTORICAL_DAYS)
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                load_price_csv(path)

    def test_csv_rejects_noncanonical_week_date(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            days = ("2026-10-09", "2026-W41-6", "2026-10-11")
            self.write_csv(path, days, HISTORICAL_DAYS)
            with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
                load_price_csv(path)

    def test_csv_accepts_today_after_file_mtime(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "prices.csv"
            days = (*HISTORICAL_DAYS, NOW_UTC.date().isoformat())
            self.write_csv(path, days, days)
            assets = load_price_csv(path)
            self.assertEqual(assets[0].observations[-1][0], "2026-10-12")
            self.assertEqual(
                datetime.fromisoformat(assets[0].asof_utc), NOW_UTC - timedelta(days=2)
            )

    def test_asof_exactly_five_minutes_ahead_accepted_across_midnight(self):
        asof = (NOW_UTC + timedelta(minutes=5)).isoformat()
        result = compare_assets(
            [self.make("A", HISTORICAL_DAYS, asof=asof),
             self.make("B", HISTORICAL_DAYS, asof=asof)],
            window=2,
        )
        self.assertEqual(result.dates, HISTORICAL_DAYS)

    def test_asof_more_than_five_minutes_ahead_rejected(self):
        asof = (NOW_UTC + timedelta(minutes=5, microseconds=1)).isoformat()
        assets = [self.make("A", HISTORICAL_DAYS), self.make("B", HISTORICAL_DAYS)]
        with self.assertRaisesRegex(ValueError, "FUTURE_SOURCE_TIMESTAMP"):
            compare_assets([assets[0], replace(assets[1], asof_utc=asof)], window=2)

    def test_asof_tolerance_preserved_for_timezone_offsets(self):
        offset = timezone(timedelta(hours=3))
        boundary = NOW_UTC + timedelta(minutes=5)
        accepted = boundary.astimezone(offset).isoformat()
        rejected = (boundary + timedelta(microseconds=1)).astimezone(offset).isoformat()
        a = self.make("A", HISTORICAL_DAYS)
        b = self.make("B", HISTORICAL_DAYS, asof=accepted)
        self.assertEqual(compare_assets([a, b], window=2).dates, HISTORICAL_DAYS)
        with self.assertRaisesRegex(ValueError, "FUTURE_SOURCE_TIMESTAMP"):
            compare_assets([a, replace(b, asof_utc=rejected)], window=2)


if __name__ == "__main__":
    unittest.main()
