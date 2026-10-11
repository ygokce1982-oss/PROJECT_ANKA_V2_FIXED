"""Offline acceptance tests for the deterministic risk planner."""

import math
import unittest

from core.trade_risk import calculate_risk_plan


class TradeRiskTests(unittest.TestCase):
    def test_long_plan_includes_fees_and_respects_risk(self):
        p = calculate_risk_plan(side="LONG", entry=100, stop=95, target=110, equity=10000)
        self.assertEqual(p.quantity, 19)
        self.assertLessEqual(p.potential_loss, p.risk_budget)
        self.assertAlmostEqual(p.risk_per_unit, 5.195)
        self.assertAlmostEqual(p.potential_reward, 19 * 9.79)
        self.assertGreater(p.reward_risk_ratio, 1)
        self.assertFalse(p.live)
        self.assertFalse(p.sends_orders)

    def test_short_is_hypothetical_and_has_correct_geometry(self):
        p = calculate_risk_plan(side="SHORT", entry=100, stop=105, target=90, equity=10000)
        self.assertEqual(p.quantity, 19)
        self.assertLessEqual(p.potential_loss, p.risk_budget)
        self.assertFalse(p.sends_orders)

    def test_capital_cap_prevents_leverage(self):
        p = calculate_risk_plan(
            side="LONG", entry=100, stop=99, target=110,
            equity=1000, risk_fraction=0.1,
        )
        self.assertEqual(p.quantity, 9)
        self.assertLessEqual(p.notional * (1 + p.fee_rate), p.equity)

    def test_fractional_lot_support(self):
        p = calculate_risk_plan(
            side="LONG", entry=100, stop=90, target=120,
            equity=1000, lot_step=0.001,
        )
        self.assertGreater(p.quantity, 0)
        self.assertLessEqual(p.potential_loss, p.risk_budget + 1e-10)
        self.assertAlmostEqual(p.quantity * 1000, round(p.quantity * 1000))

    def test_tiny_risk_budget_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "asgari lot"):
            calculate_risk_plan(
                side="LONG", entry=100, stop=50, target=200,
                equity=1000, risk_fraction=0.001,
            )

    def test_wrong_stop_target_direction_rejected(self):
        for side, stop, target in [
            ("LONG", 101, 110), ("LONG", 90, 99),
            ("SHORT", 99, 90), ("SHORT", 110, 105),
        ]:
            with self.subTest(side=side, stop=stop, target=target):
                with self.assertRaises(ValueError):
                    calculate_risk_plan(
                        side=side, entry=100, stop=stop,
                        target=target, equity=10000,
                    )

    def test_invalid_side_rejected(self):
        with self.assertRaises(ValueError):
            calculate_risk_plan(
                side="BUY", entry=100, stop=90, target=120, equity=10000
            )

    def test_nonfinite_or_boolean_values_rejected(self):
        for bad in [math.nan, math.inf, -math.inf, True, "bad"]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    calculate_risk_plan(
                        side="LONG", entry=bad, stop=90, target=120, equity=10000
                    )

    def test_invalid_fees_and_risk_limits_rejected(self):
        for field, value in [
            ("fee_rate", -0.01), ("fee_rate", 0.06),
            ("risk_fraction", 0), ("risk_fraction", 0.2),
            ("lot_step", 0), ("equity", 0),
        ]:
            with self.subTest(field=field, value=value):
                kwargs = {"side": "LONG", "entry": 100, "stop": 90,
                          "target": 120, "equity": 10000}
                kwargs[field] = value
                with self.assertRaises(ValueError):
                    calculate_risk_plan(**kwargs)

    def test_fee_can_turn_small_target_into_net_loss(self):
        p = calculate_risk_plan(
            side="LONG", entry=100, stop=99, target=100.1,
            equity=10000, fee_rate=0.01,
        )
        self.assertLess(p.potential_reward, 0)
        self.assertLess(p.reward_risk_ratio, 0)
