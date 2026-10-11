"""Tests of retrospective geometry labels on explicit offline fixtures."""

import unittest
from dataclasses import replace
from datetime import UTC, datetime, timedelta

from core.candle_patterns import recognize
from core.offline_workbench import Bar, validated


def fixture(count=35):
    start = datetime(2025, 1, 1, tzinfo=UTC)
    return [
        Bar((start + timedelta(days=i)).isoformat(), 10.0, 11.0, 9.0, 10.0, 100.0)
        for i in range(count)
    ]


def with_shape(bar, open_, high, low, close):
    return replace(bar, open=open_, high=high, low=low, close=close)


class CandlePatternsTests(unittest.TestCase):
    def test_fixture_and_output_alignment(self):
        bars = fixture()
        self.assertIs(validated(bars), bars)
        before = list(bars)
        results = recognize(tuple(bars))
        self.assertEqual(bars, before)
        self.assertEqual(len(results), 35)
        for index, result in enumerate(results):
            self.assertEqual((result.index, result.time), (index, bars[index].time))
            self.assertFalse(result.bullish_engulfing)
            self.assertFalse(result.bearish_engulfing)
            self.assertFalse(result.hammer)
            self.assertFalse(result.shooting_star)

    def test_minimum_length(self):
        for count in (0, 1, 2, 34):
            with self.subTest(count=count), self.assertRaises(ValueError):
                recognize(fixture(count))
        self.assertEqual(len(recognize(fixture(35))), 35)

    def test_engulfing_body_definitions(self):
        cases = [
            # Previous wicks need not be contained.
            ((12, 20, 5, 10), (9, 13, 9, 13), True, False),
            ((10, 20, 5, 12), (13, 13, 9, 9), False, True),
            # One equal boundary and one strict boundary qualify.
            ((12, 12, 10, 10), (10, 13, 10, 13), True, False),
            ((10, 12, 10, 12), (12, 12, 9, 9), False, True),
            # Exact matching bodies, partial overlaps, same colors and dojis.
            ((12, 12, 10, 10), (10, 12, 10, 12), False, False),
            ((10, 12, 10, 12), (12, 12, 10, 10), False, False),
            ((12, 12, 10, 10), (11, 13, 11, 13), False, False),
            ((10, 12, 10, 12), (11, 11, 9, 9), False, False),
            ((10, 12, 10, 12), (9, 13, 9, 13), False, False),
            ((10, 11, 9, 10), (9, 12, 9, 12), False, False),
            ((12, 12, 10, 10), (11, 12, 10, 11), False, False),
        ]
        for previous, current, bullish, bearish in cases:
            with self.subTest(previous=previous, current=current):
                bars = fixture()
                bars[-2] = with_shape(bars[-2], *previous)
                bars[-1] = with_shape(bars[-1], *current)
                result = recognize(bars)[-1]
                self.assertEqual(result.bullish_engulfing, bullish)
                self.assertEqual(result.bearish_engulfing, bearish)

    def test_shapes_and_inclusive_thresholds(self):
        cases = [
            ((10, 11.5, 8, 11), True, False),
            ((11, 11.5, 8, 10), True, False),
            ((10, 13, 9.5, 11), False, True),
            ((11, 13, 9.5, 10), False, True),
            ((10, 11, 7, 11), True, False),
            ((10, 14, 10, 11), False, True),
            ((10, 11.5, 8.01, 11), False, False),
            ((10, 11.51, 8, 11), False, False),
            ((10, 12.99, 9.5, 11), False, False),
            ((10, 13, 9.49, 11), False, False),
            ((10, 12, 8, 10), False, False),
            ((10, 10, 10, 10), False, False),
        ]
        for shape, hammer, star in cases:
            with self.subTest(shape=shape):
                bars = fixture()
                bars[-1] = with_shape(bars[-1], *shape)
                result = recognize(bars)[-1]
                self.assertEqual(result.hammer, hammer)
                self.assertEqual(result.shooting_star, star)

    def test_first_bar_has_no_engulfing_but_can_have_shape(self):
        bars = fixture()
        bars[0] = with_shape(bars[0], 10, 11.5, 8, 11)
        result = recognize(bars)[0]
        self.assertTrue(result.hammer)
        self.assertFalse(result.bullish_engulfing)
        self.assertFalse(result.bearish_engulfing)

    def test_finite_numbers_required_in_every_field_and_bar(self):
        for field in ('open', 'high', 'low', 'close', 'volume'):
            for value in (float('nan'), float('inf'), float('-inf')):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    bars = fixture()
                    bars[0] = replace(bars[0], **{field: value})
                    recognize(bars)

    def test_invalid_geometry_prices_and_volume(self):
        cases = [
            {'low': 10.5}, {'high': 9.5}, {'low': 12, 'high': 8},
            {'open': 12}, {'close': 8}, {'low': 0}, {'low': -1},
            {'volume': -1},
        ]
        for changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                bars = fixture()
                bars[17] = replace(bars[17], **changes)
                recognize(bars)

    def test_timestamp_validation(self):
        for timestamp in ('invalid', '2025-01-18T00:00:00', fixture()[16].time):
            with self.subTest(timestamp=timestamp), self.assertRaises(ValueError):
                bars = fixture()
                bars[17] = replace(bars[17], time=timestamp)
                recognize(bars)
        bars = fixture()
        bars[16], bars[17] = bars[17], bars[16]
        with self.assertRaises(ValueError):
            recognize(bars)

    def test_zero_volume_allowed_and_volume_does_not_change_labels(self):
        bars = fixture()
        bars[-1] = with_shape(bars[-1], 10, 11.5, 8, 11)
        expected = recognize(bars)
        self.assertEqual(recognize([replace(bar, volume=0) for bar in bars]), expected)

    def test_no_lookahead_on_valid_extensions_and_future_changes(self):
        bars = fixture(40)
        bars[33] = with_shape(bars[33], 12, 12, 10, 10)
        bars[34] = with_shape(bars[34], 9, 13, 9, 13)
        prefix = recognize(bars[:35])
        self.assertTrue(prefix[-1].bullish_engulfing)
        self.assertEqual(recognize(bars)[:35], prefix)
        for index in range(35, len(bars)):
            bars[index] = with_shape(bars[index], 10, 13, 9.5, 11)
        self.assertEqual(recognize(bars)[:35], prefix)


if __name__ == '__main__':
    unittest.main()
