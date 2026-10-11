"""Tests for equity-based statistics; no market access or trade inference."""

import math
import unittest

from core.performance_metrics import performance_metrics


class PerformanceMetricsTests(unittest.TestCase):
    def test_backtest_equity_curve_compatibility(self):
        # Same list-of-equity-values shape supplied by backtest().
        backtest_result = {"equity_curve": [10000.0, 11000.0, 9900.0]}
        result = performance_metrics(backtest_result["equity_curve"])
        self.assertAlmostEqual(result["total_return"], -0.01)
        self.assertAlmostEqual(result["maximum_drawdown"], -0.1)
        self.assertAlmostEqual(result["return_volatility"], 0.1)
        self.assertEqual(result["positive_return_observations"], 1)
        self.assertEqual(result["negative_return_observations"], 1)
        self.assertEqual(result["issues"], [])
        self.assertNotIn("trades", result)
        self.assertNotIn("annualized_return", result)

    def test_significant_drawdown_uses_running_peak(self):
        result = performance_metrics([100, 200, 50, 150])
        self.assertAlmostEqual(result["total_return"], 0.5)
        self.assertAlmostEqual(result["maximum_drawdown"], -0.75)
        self.assertEqual(result["positive_return_observations"], 2)
        self.assertEqual(result["negative_return_observations"], 1)
        self.assertAlmostEqual(result["return_volatility"], math.sqrt(31 / 24))

    def test_flat_curve(self):
        result = performance_metrics([100, 100, 100])
        self.assertEqual(result["total_return"], 0.0)
        self.assertEqual(result["maximum_drawdown"], 0.0)
        self.assertEqual(result["return_volatility"], 0.0)
        self.assertEqual(result["zero_return_observations"], 2)
        self.assertEqual(result["positive_return_observations"], 0)
        self.assertEqual(result["negative_return_observations"], 0)

    def test_one_row(self):
        result = performance_metrics([100])
        self.assertIsNone(result["total_return"])
        self.assertIsNone(result["return_volatility"])
        self.assertEqual(result["maximum_drawdown"], 0.0)
        self.assertEqual(result["return_observations"], 0)
        self.assertTrue(result["issues"])

    def test_two_rows_insufficient_for_volatility(self):
        result = performance_metrics([100, 120])
        self.assertAlmostEqual(result["total_return"], 0.2)
        self.assertIsNone(result["return_volatility"])

    def test_empty_curve(self):
        result = performance_metrics([])
        self.assertIsNone(result["total_return"])
        self.assertIsNone(result["maximum_drawdown"])
        self.assertIsNone(result["return_volatility"])
        self.assertEqual(result["observations"], 0)
        self.assertTrue(result["issues"])

    def test_zero_terminal_equity_is_full_loss(self):
        result = performance_metrics([100, 50, 0])
        self.assertEqual(result["total_return"], -1.0)
        self.assertEqual(result["maximum_drawdown"], -1.0)
        self.assertAlmostEqual(result["return_volatility"], 0.25)
        self.assertEqual(result["negative_return_observations"], 2)

    def test_zero_initial_equity(self):
        result = performance_metrics([0, 100, 110, 99])
        self.assertIsNone(result["total_return"])
        self.assertIsNone(result["return_volatility"])
        self.assertEqual(result["undefined_return_observations"], 1)
        self.assertEqual(result["return_observations"], 2)
        self.assertEqual(result["positive_return_observations"], 1)
        self.assertEqual(result["negative_return_observations"], 1)
        self.assertTrue(result["issues"])

    def test_all_zero_curve(self):
        result = performance_metrics([0, 0, 0])
        self.assertIsNone(result["total_return"])
        self.assertIsNone(result["return_volatility"])
        self.assertEqual(result["maximum_drawdown"], 0.0)
        self.assertEqual(result["undefined_return_observations"], 2)
        self.assertEqual(result["zero_return_observations"], 0)

    def test_zero_in_middle_does_not_fabricate_recovery_return(self):
        result = performance_metrics([100, 0, 100])
        self.assertEqual(result["total_return"], 0.0)
        self.assertEqual(result["maximum_drawdown"], -1.0)
        self.assertIsNone(result["return_volatility"])
        self.assertEqual(result["negative_return_observations"], 1)
        self.assertEqual(result["positive_return_observations"], 0)
        self.assertEqual(result["undefined_return_observations"], 1)

    def test_negative_and_nonfinite_equity_rejected(self):
        for invalid in (-1, math.nan, math.inf, -math.inf):
            for curve in ([invalid], [100, invalid], [invalid, 100]):
                with self.subTest(curve=curve):
                    with self.assertRaises(ValueError):
                        performance_metrics(curve)

    def test_invalid_types_rejected(self):
        for invalid in (None, "100", True, object()):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    performance_metrics([100, invalid])

    def test_overflowing_return_rejected(self):
        with self.assertRaises(ValueError):
            performance_metrics([1e-300, 1e300])

    def test_large_finite_returns_have_finite_volatility(self):
        result = performance_metrics([1e-200, 1, 1])
        self.assertTrue(math.isfinite(result["return_volatility"]))
        self.assertAlmostEqual(result["return_volatility"] / 1e200, 0.5)

    def test_preserves_input_and_accepts_iterable(self):
        curve = [100, 200, 50]
        result = performance_metrics(iter(curve))
        self.assertEqual(curve, [100, 200, 50])
        self.assertEqual(result["maximum_drawdown"], -0.75)


if __name__ == "__main__":
    unittest.main()
