"""Deterministic independent acceptance for professional ANKA EMA/RSI chart."""
from __future__ import annotations
import math
import unittest

from core.chart_indicators import ema_series, rsi_wilder_series, validate_ohlcv
from scripts.anka_professional_toolchain_demo import demo_candles


class FinancialIndicatorTests(unittest.TestCase):
    def test_ema_seeded_with_sma_and_next_iterations(self):
        result = ema_series([1, 2, 3, 4, 5], 3)
        self.assertEqual(result, [None, None, 2.0, 3.0, 4.0])

    def test_ema_valid_period_one_and_not_enough_data(self):
        self.assertEqual(ema_series([100, 105], 1), [100.0, 105.0])
        self.assertEqual(ema_series([100, 105], 3), [None, None])

    def test_rsi_first_valid_value_and_trending_prices(self):
        growing = rsi_wilder_series([float(n) for n in range(1, 25)], 14)
        falling = rsi_wilder_series([float(n) for n in range(25, 0, -1)], 14)
        flat = rsi_wilder_series([10.0] * 25, 14)
        self.assertEqual(growing[:14], [None] * 14)
        self.assertEqual(growing[14:], [100.0] * 10)
        self.assertEqual(falling[14:], [0.0] * (len(falling) - 14))
        self.assertEqual(flat[14:], [50.0] * (len(flat) - 14))

    def test_rsi_known_wilder_reference_series(self):
        # Wilder's 14-period textbook data, RSI value near 70.46.
        values = [
            44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,
            46.08,45.89,46.03,45.61,46.28,46.28,46.00,46.03,
        ]
        rsi = rsi_wilder_series(values,14)
        self.assertAlmostEqual(rsi[14],70.46,delta=0.12)
        self.assertEqual(len(rsi),len(values))
        self.assertTrue(all(v is None or 0 <= v <= 100 for v in rsi))

    def test_mixed_prices_remain_finite_in_range(self):
        values = [100.0 + 5 * math.sin(i / 4.0) + i / 10 for i in range(70)]
        a = rsi_wilder_series(values)
        self.assertTrue(all(v is None or (math.isfinite(v) and 0 <= v <= 100) for v in a))

    def test_no_input_mutation_or_history_dependent_on_viewport(self):
        candles = demo_candles("THYAO")
        original = [tuple(x) for x in candles]
        closes = validate_ohlcv(candles)
        full_ema = ema_series(closes, 26)
        full_rsi = rsi_wilder_series(closes)
        self.assertEqual(original, candles)
        self.assertEqual(full_ema[-78:], ema_series(closes, 26)[-78:])
        self.assertEqual(full_rsi[-78:], rsi_wilder_series(closes)[-78:])
        self.assertEqual(len(full_ema), len(candles))

    def test_ohlcv_validation_rejects_corrupt_rows(self):
        good = [(100,105,99,104,2000), (104,108,101,102,0)]
        self.assertEqual(validate_ohlcv(good),[104,102])
        for bad in (
            [], [(100, 98, 99, 101, 10)],
            [(100,105,103,102,10)],
            [(100,105,99,float("nan"),10)],
            [(100,105,99,104,-1)],
            [(100,105,99,float("inf"),10)],
            [(100,105,99,104)],
            [(0,5,1,3,10)],
            [("secret",5,1,3,10)],
        ):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_ohlcv(bad)

    def test_bad_indicator_inputs_are_rejected(self):
        for p in (0,-1,1.5,True,None):
            with self.subTest(period=p),self.assertRaises(ValueError):
                ema_series([1,2,3],p)
        for values in ([1,float("nan")], [1,float("inf")], [-1,2],[1,"bad"]):
            with self.subTest(values=values),self.assertRaises(ValueError):
                rsi_wilder_series(values,14)


if __name__ == "__main__":
    unittest.main()
