"""Explicit offline fixtures for the bounded data-quality checker."""

import unittest
from copy import deepcopy
from dataclasses import FrozenInstanceError, dataclass
from datetime import UTC, datetime

from core.local_data_quality import check_bars


def candle(timestamp="2025-01-01T00:00:00+00:00", **changes):
    result = dict(timestamp=timestamp, open=10, high=11, low=9, close=10, volume=100)
    result.update(changes)
    return result


@dataclass(frozen=True)
class Bar:
    time: str
    open: float = 10
    high: float = 11
    low: float = 9
    close: float = 10
    volume: float = 100


class DataQualityTests(unittest.TestCase):
    def codes(self, rows, **kwargs):
        return [finding.code for finding in check_bars(rows, **kwargs).findings]

    def test_valid_empty_and_typed_rows(self):
        for rows in ([], [candle()], (Bar("2025-01-01T00:00:00Z"),)):
            with self.subTest(rows=rows):
                result = check_bars(rows)
                self.assertTrue(result.ok)
                self.assertTrue(result.complete)
                self.assertEqual(result.rows_checked, len(rows))
        self.assertTrue(check_bars([candle(open=0, high=0, low=0, close=0, volume=0)]).ok)
        self.assertTrue(check_bars([candle(datetime(2025, 1, 1, tzinfo=UTC))]).ok)

    def test_missing_fields_and_invalid_entries(self):
        result = check_bars([{}, None])
        self.assertEqual(len(result.findings), 12)
        self.assertEqual([f.row for f in result.findings], [1] * 6 + [2] * 6)
        self.assertTrue(
            all(f.code == "missing_field" and f.severity == "error" for f in result.findings)
        )
        for field in ("timestamp", "open", "high", "low", "close", "volume"):
            row = candle()
            del row[field]
            self.assertEqual(self.codes([row]), ["missing_field"])

    def test_numeric_types_nonfinite_and_negatives(self):
        for field in ("open", "high", "low", "close", "volume"):
            for value in (float("nan"), float("inf"), -float("inf")):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.codes([candle(**{field: value})]), ["non_finite"])
            for value in (True, None, "10", complex(10)):
                with self.subTest(field=field, value=value):
                    self.assertEqual(self.codes([candle(**{field: value})]), ["invalid_number"])
            result = check_bars([candle(**{field: -1})])
            self.assertIn((field, "negative_value"), [(f.field, f.code) for f in result.findings])
        huge = 10**1000
        self.assertTrue(check_bars([candle(open=huge, high=huge, low=huge, close=huge)]).ok)

    def test_bounds_including_crossed_high_low(self):
        self.assertEqual(self.codes([candle(high=9)]), ["high_bounds"])
        self.assertEqual(self.codes([candle(low=11)]), ["low_bounds"])
        self.assertEqual(self.codes([candle(high=8, low=12)]), ["high_bounds", "low_bounds"])
        self.assertTrue(check_bars([candle(high=10, low=10)]).ok)
        self.assertEqual(
            self.codes([candle(volume=None, high=9)]), ["invalid_number", "high_bounds"]
        )

    def test_timestamp_validation_and_alias_precedence(self):
        for value in (None, True, 123, "", "bad", "2025-01-01", datetime(2025, 1, 1), "x" * 129):
            with self.subTest(value=value):
                self.assertEqual(self.codes([candle(value)]), ["invalid_timestamp"])
        row = candle()
        row["time"] = row.pop("timestamp")
        self.assertTrue(check_bars([row]).ok)
        row["timestamp"] = None
        self.assertEqual(self.codes([row]), ["invalid_timestamp"])

    def test_order_duplicates_and_timezone_normalization(self):
        rows = [
            candle("2025-01-02T00:00:00Z"),
            candle("2025-01-01T00:00:00Z"),
            candle("2025-01-02T03:00:00+03:00"),
        ]
        result = check_bars(rows)
        self.assertEqual(
            [(f.row, f.code) for f in result.findings],
            [(2, "timestamp_order"), (3, "duplicate_timestamp")],
        )
        self.assertIn("row 1", result.findings[-1].message)
        self.assertEqual(self.codes([candle(), candle()]), ["duplicate_timestamp"])
        self.assertEqual(
            self.codes([candle("2025-01-02T00:00:00Z"), candle("bad"), candle()]),
            ["invalid_timestamp", "timestamp_order"],
        )

    def test_determinism_no_mutation_and_immutable_results(self):
        rows = [candle(high=8), {}]
        before = deepcopy(rows)
        first = check_bars(rows)
        self.assertEqual(first, check_bars(rows))
        self.assertEqual(rows, before)
        with self.assertRaises(FrozenInstanceError):
            first.rows_checked = 0
        with self.assertRaises(FrozenInstanceError):
            first.findings[0].row = 0

    def test_row_limits(self):
        rows = [candle(), {}, {}]
        result = check_bars(rows, max_rows=1)
        self.assertEqual((result.rows_checked, result.total_rows), (1, 3))
        self.assertEqual(result.findings, ())
        self.assertTrue(result.row_limit_reached)
        self.assertFalse(result.complete)
        self.assertFalse(result.ok)
        self.assertTrue(check_bars([candle()], max_rows=1).complete)

    def test_findings_limit_stops_before_later_rows(self):
        class Explosive:
            def __getattribute__(self, name):
                raise AssertionError("Later row must not be read")

        result = check_bars([{}, Explosive()], max_findings=2)
        self.assertEqual(len(result.findings), 2)
        self.assertEqual(result.rows_checked, 1)
        self.assertTrue(result.finding_limit_reached)
        self.assertFalse(result.complete)
        self.assertFalse(result.ok)
        self.assertFalse(check_bars([candle(volume=-1)], max_findings=1).complete)

    def test_large_malformed_input_is_bounded(self):
        result = check_bars([None] * 100_000, max_rows=5, max_findings=7)
        self.assertEqual(len(result.findings), 7)
        self.assertEqual(result.rows_checked, 2)
        self.assertTrue(result.row_limit_reached)
        self.assertTrue(result.finding_limit_reached)

    def test_bad_limits_and_containers(self):
        for option in ("max_rows", "max_findings"):
            for value in (0, -1, True, 1.5, None):
                with self.subTest(option=option, value=value), self.assertRaises(ValueError):
                    check_bars([], **{option: value})
        for rows in (None, {}, "abc", iter([])):
            with self.subTest(rows=rows), self.assertRaises(TypeError):
                check_bars(rows)

    def test_attribute_access_failure_is_structured(self):
        class Broken:
            time = "2025-01-01T00:00:00Z"
            high = 11
            low = 9
            close = 10
            volume = 100

            @property
            def open(self):
                raise RuntimeError("untrusted detail")

        result = check_bars([Broken()])
        self.assertEqual([(f.field, f.code) for f in result.findings], [("open", "field_access")])
        self.assertNotIn("untrusted detail", result.findings[0].message)


if __name__ == "__main__":
    unittest.main()
