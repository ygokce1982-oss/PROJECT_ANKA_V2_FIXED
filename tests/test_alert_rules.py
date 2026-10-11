import copy
import math
import unittest
from dataclasses import FrozenInstanceError

from core.alert_rules import evaluate_alerts


def rule(rule_id="up", symbol="DEMO1", comparison=">", threshold=100):
    return dict(rule_id=rule_id, symbol=symbol, comparison=comparison, threshold=threshold)


class AlertRulesTests(unittest.TestCase):
    def evaluate(self, rules=None, prices=None, **kwargs):
        return evaluate_alerts(
            [rule()] if rules is None else rules,
            {"DEMO1": 101} if prices is None else prices,
            observed_at=kwargs.pop("observed_at", 100),
            **kwargs,
        )

    def test_both_comparisons_and_equality(self):
        for comparison, price, expected in (
            (">", 101, True),
            (">", 99, False),
            (">", 100, False),
            ("<", 99, True),
            ("<", 101, False),
            ("<", 100, False),
        ):
            with self.subTest(comparison=comparison, price=price):
                result = self.evaluate([rule(comparison=comparison)], {"DEMO1": price})[0]
                self.assertEqual(result.matched, expected)
                self.assertEqual(result.fired, expected)
                self.assertEqual(result.fired_at, 100.0 if expected else None)
                self.assertEqual(
                    result.reason, "threshold_match" if expected else "threshold_not_met"
                )

    def test_dedup_even_with_zero_cooldown(self):
        result = self.evaluate(last_fired={"up": 100}, cooldown_seconds=0)[0]
        self.assertTrue(result.matched)
        self.assertFalse(result.fired)
        self.assertEqual(result.reason, "duplicate_timestamp")
        self.assertIsNone(result.fired_at)

    def test_cooldown_boundary(self):
        for now, fired in ((109.5, False), (110, True), (110.5, True)):
            with self.subTest(now=now):
                result = self.evaluate(
                    observed_at=now, last_fired={"up": 100}, cooldown_seconds=10
                )[0]
                self.assertEqual(result.fired, fired)
                self.assertTrue(result.matched)
                self.assertEqual(result.reason, "threshold_match" if fired else "cooldown_active")

    def test_history_is_explicit_and_per_rule(self):
        rules = [rule("a"), rule("b")]
        first = self.evaluate(rules)
        self.assertEqual(first, self.evaluate(rules))
        history = {r.rule_id: r.fired_at for r in first if r.fired}
        self.assertTrue(all(not r.fired for r in self.evaluate(rules, last_fired=history)))
        result = self.evaluate(rules, last_fired={"a": 100})
        self.assertEqual([r.fired for r in result], [False, True])
        self.assertTrue(self.evaluate(observed_at=101, last_fired={"up": 100})[0].fired)

    def test_missing_and_case_sensitive_symbols(self):
        result = self.evaluate(prices={"demo1": 101})[0]
        self.assertEqual(result.reason, "missing_symbol")
        self.assertIsNone(result.price)
        self.assertFalse(result.matched)
        self.assertFalse(result.fired)
        self.assertIsNone(result.fired_at)

    def test_stable_order_empty_rules_and_finite_nonpositive_prices(self):
        results = self.evaluate([rule("z"), rule("a")])
        self.assertEqual([r.rule_id for r in results], ["z", "a"])
        self.assertEqual(self.evaluate([]), ())
        for price in (0, -10):
            self.assertTrue(self.evaluate([rule(comparison="<")], {"DEMO1": price})[0].fired)
        self.assertTrue(self.evaluate(cooldown_seconds=1000)[0].fired)

    def test_malformed_rules(self):
        bad_rules = [
            None,
            {},
            {"rule_id": "a"},
            rule(rule_id=""),
            rule(rule_id=" a "),
            rule(rule_id=True),
            rule(symbol=" "),
            rule(symbol=None),
            rule(symbol=" DEMO1"),
            rule(comparison=">="),
            rule(comparison=[]),
            rule(threshold=0),
            rule(threshold=-1),
            rule(threshold=True),
            rule(threshold="100"),
            rule(threshold=math.nan),
            rule(threshold=math.inf),
            rule(threshold=10**1000),
            dict(rule(), extra=1),
        ]
        for bad in bad_rules:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.evaluate([bad])
        with self.assertRaises(ValueError):
            self.evaluate([rule(), rule()])
        for bad in ({}, "rules", None, iter([rule()])):
            with self.subTest(container=bad), self.assertRaises(ValueError):
                evaluate_alerts(bad, {}, observed_at=0)

    def test_invalid_prices_including_unused_symbols(self):
        for value in (True, False, None, "101", [], math.nan, math.inf, -math.inf, 10**1000):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.evaluate(prices={"DEMO1": 101, "UNUSED": value})
        for prices in ([], None, {"": 1}, {True: 1}, {" DEMO1": 1}):
            with self.subTest(prices=prices), self.assertRaises(ValueError):
                evaluate_alerts([rule()], prices, observed_at=100)

    def test_invalid_times_and_cooldowns(self):
        for value in (True, False, None, "100", -1, math.nan, math.inf, -math.inf, 10**1000):
            for field in ("observed_at", "cooldown_seconds"):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.evaluate(**{field: value})
            with self.subTest(history=value), self.assertRaises(ValueError):
                self.evaluate(last_fired={"up": value})
        for history in ([], "bad", {"unknown": 0}, {"": 0}, {True: 0}, {"up": 101}):
            with self.subTest(history=history), self.assertRaises(ValueError):
                self.evaluate(last_fired=history)
        result = self.evaluate(observed_at=0, last_fired={"up": 0})[0]
        self.assertEqual(result.reason, "duplicate_timestamp")

    def test_no_match_precedes_suppression(self):
        result = self.evaluate(prices={"DEMO1": 100}, last_fired={"up": 100})[0]
        self.assertEqual(result.reason, "threshold_not_met")
        result = self.evaluate(prices={}, last_fired={"up": 100})[0]
        self.assertEqual(result.reason, "missing_symbol")

    def test_input_immutability_and_frozen_results(self):
        rules = [rule("a"), rule("b")]
        prices = {"DEMO1": 101}
        history = {"a": 95}
        before = copy.deepcopy((rules, prices, history))
        result = self.evaluate(rules, prices, last_fired=history, cooldown_seconds=10)
        self.assertEqual((rules, prices, history), before)
        with self.assertRaises(FrozenInstanceError):
            result[0].fired = True
        rules.append(rule("a"))
        before = copy.deepcopy((rules, prices, history))
        with self.assertRaises(ValueError):
            self.evaluate(rules, prices, last_fired=history)
        self.assertEqual((rules, prices, history), before)


if __name__ == "__main__":
    unittest.main()
