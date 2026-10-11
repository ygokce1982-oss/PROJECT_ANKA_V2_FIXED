"""Offline UI coverage using explicitly supplied hypothetical test values."""

import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from core.trade_risk import calculate_risk_plan
from ui.components.local_workbench import LocalWorkbenchPage
from ui.components.risk_planner import RiskPlannerWidget


class RiskPlannerUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = RiskPlannerWidget()
        self.addCleanup(self.widget.close)

    def fill(self, side="LONG", **overrides):
        values = dict(entry="100", stop="95", target="110", equity="10000",
                      risk_percent="1", fee_percent="0.1", lot_step="1")
        if side == "SHORT":
            values.update(stop="105", target="90")
        values.update(overrides)
        self.widget.side.setCurrentText(side)
        for key, value in values.items():
            self.widget.inputs[key].setText(value)

    def test_both_sides_call_core_and_display_results_without_network_or_trades(self):
        for side in ("LONG", "SHORT"):
            with self.subTest(side=side):
                self.fill(side)
                with (
                    patch("ui.components.risk_planner.calculate_risk_plan",
                          wraps=calculate_risk_plan) as calculate,
                    patch("socket.socket", side_effect=AssertionError("NETWORK_FORBIDDEN")),
                    patch("core.offline_workbench.LocalStore.trade",
                          side_effect=AssertionError("TRADE_FORBIDDEN")),
                ):
                    self.widget.calculate_button.click()
                calculate.assert_called_once_with(
                    side=side, entry=100.0,
                    stop=95.0 if side == "LONG" else 105.0,
                    target=110.0 if side == "LONG" else 90.0,
                    equity=10000.0, risk_fraction=0.01, fee_rate=0.001, lot_step=1.0,
                )
                plan = self.widget.plan
                self.assertIsNotNone(plan)
                self.assertFalse(plan.live)
                self.assertFalse(plan.sends_orders)
                self.assertLessEqual(plan.potential_loss, plan.risk_budget)
                for key, label in self.widget.results.items():
                    self.assertEqual(label.text(), format(getattr(plan, key), ".12g"))

    def test_invalid_inputs_clear_results_and_explain_problem(self):
        cases = [
            ({"entry": ""}, "geçerli bir sayı"),
            ({"entry": "abc"}, "geçerli bir sayı"),
            ({"entry": "nan"}, "sonlu"),
            ({"equity": "inf"}, "sonlu"),
            ({"stop": "0"}, "sıfırdan büyük"),
            ({"lot_step": "-1"}, "sıfırdan büyük"),
            ({"risk_percent": "0"}, "sıfırdan büyük"),
            ({"risk_percent": "11"}, "%10"),
            ({"fee_percent": "-1"}, "Komisyon"),
            ({"fee_percent": "6"}, "Komisyon"),
            ({"stop": "101"}, "LONG için"),
            ({"target": "100"}, "LONG için"),
            ({"equity": "1"}, "yetersiz"),
        ]
        for overrides, message in cases:
            with self.subTest(overrides=overrides):
                self.fill()
                self.widget.calculate_button.click()
                self.assertIsNotNone(self.widget.plan)
                self.fill(**overrides)
                self.widget.calculate_button.click()
                self.assertIsNone(self.widget.plan)
                self.assertIn(message, self.widget.status.text())
                self.assertTrue(all(label.text() == "—" for label in self.widget.results.values()))
        self.fill("SHORT", stop="95")
        self.widget.calculate_button.click()
        self.assertIn("SHORT için", self.widget.status.text())

    def test_edit_or_side_change_invalidates_previous_plan(self):
        self.fill()
        self.widget.calculate_button.click()
        self.widget.inputs["entry"].setText("101")
        self.assertIsNone(self.widget.plan)
        self.assertTrue(all(label.text() == "—" for label in self.widget.results.values()))
        self.fill()
        self.widget.calculate_button.click()
        self.widget.side.setCurrentText("SHORT")
        self.assertIsNone(self.widget.plan)
        self.assertTrue(all(label.text() == "—" for label in self.widget.results.values()))

    def test_decimal_comma_fractional_lots_and_nonpositive_reward(self):
        self.fill(fee_percent="0,1", lot_step="0,5")
        self.widget.calculate_button.click()
        self.assertIsNotNone(self.widget.plan)
        self.assertEqual(self.widget.plan.lot_step, 0.5)
        self.fill(target="100.01", fee_percent="1")
        self.widget.calculate_button.click()
        self.assertIsNotNone(self.widget.plan)
        self.assertLess(self.widget.plan.reward_risk_ratio, 0)
        self.assertIn("negatif", self.widget.status.text())

    def test_workbench_contains_independent_planner(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {"ANKA_STATE_DIR": directory, "ANKA_OFFLINE": "1"}):
                page = LocalWorkbenchPage()
                try:
                    self.assertIsInstance(page.risk_planner, RiskPlannerWidget)
                    self.assertGreaterEqual(page.layout().indexOf(page.risk_planner), 0)
                    self.assertIsNone(page.result)
                    self.assertIsNone(page.risk_planner.plan)
                    self.assertTrue(
                        all(not field.text() for field in page.risk_planner.inputs.values())
                    )
                finally:
                    page.close()


if __name__ == "__main__":
    unittest.main()
