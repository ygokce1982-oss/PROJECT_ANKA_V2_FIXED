"""Deterministic offline scenario tests, with no providers or GUI dependency."""

import copy
import math
import unittest
from dataclasses import FrozenInstanceError

from core.scenario_analysis import scenario_analysis


def position(symbol="AAA", quantity=2, unit_price=100):
    return dict(symbol=symbol, quantity=quantity, unit_price=unit_price)


class ScenarioAnalysisTests(unittest.TestCase):
    def test_positive_negative_and_portfolio(self):
        result = scenario_analysis(
            [position("BBB", 1, 100), position()],
            {"up": {"AAA": 0.1, "BBB": 0.2}, "down": {"AAA": -0.5, "BBB": -1}},
        )
        down, up = result.scenarios
        self.assertEqual([down.name, up.name], ["down", "up"])
        self.assertEqual([p.symbol for p in up.positions], ["AAA", "BBB"])
        self.assertEqual(up.current_value, 300)
        self.assertEqual(up.absolute_change, 40)
        self.assertEqual(up.scenario_value, 340)
        self.assertAlmostEqual(up.percentage_change, 40 / 300 * 100)
        self.assertEqual(up.positions[0].absolute_change, 20)
        self.assertEqual(up.positions[0].percentage_change, 10)
        self.assertAlmostEqual(up.positions[0].scenario_price, 110)
        self.assertEqual(down.absolute_change, -200)
        self.assertEqual(down.scenario_value, 100)
        self.assertEqual(down.positions[1].scenario_price, 0)
        self.assertEqual(down.positions[1].percentage_change, -100)

    def test_defaults_unknown_symbols_and_empty_shock(self):
        result = scenario_analysis([position()], {"flat": {}, "unused": {"ZZZ": 0.5}})
        for row in result.scenarios:
            self.assertEqual(row.absolute_change, 0)
            self.assertEqual(row.percentage_change, 0)
            self.assertEqual(row.defaulted_symbols, ("AAA",))
            self.assertTrue(row.positions[0].shock_defaulted)
            self.assertTrue(any("defaulted to 0.0" in issue for issue in row.issues))
        self.assertEqual(result.scenarios[1].unused_shock_symbols, ("ZZZ",))

    def test_empty_inputs(self):
        self.assertEqual(scenario_analysis([], {}).scenarios, ())
        row = scenario_analysis([], {"empty": {}}).scenarios[0]
        self.assertEqual(row.positions, ())
        self.assertEqual((row.current_value, row.scenario_value, row.absolute_change), (0, 0, 0))
        self.assertIsNone(row.percentage_change)
        self.assertTrue(row.issues)

    def test_zero_and_mixed_exposure(self):
        zero = position("ZERO", 0)
        row = scenario_analysis([zero], {"loss": {"ZERO": -1}}).scenarios[0]
        self.assertIsNone(row.percentage_change)
        self.assertIsNone(row.positions[0].percentage_change)
        self.assertEqual(row.absolute_change, 0)
        mixed = scenario_analysis([zero, position()], {"up": {"AAA": 0.25}}).scenarios[0]
        self.assertEqual(mixed.percentage_change, 25)
        self.assertIsNone(mixed.positions[1].percentage_change)

    def test_stable_sorting_immutability_and_generator(self):
        positions = [position("BBB"), position("AAA")]
        shocks = {"z": {"BBB": -0.1}, "a": {"AAA": 0.3}}
        before = copy.deepcopy((positions, shocks))
        result = scenario_analysis(positions, shocks)
        reversed_result = scenario_analysis(
            (p for p in reversed(positions)), dict(reversed(list(shocks.items())))
        )
        self.assertEqual(result, reversed_result)
        self.assertEqual((positions, shocks), before)
        with self.assertRaises(FrozenInstanceError):
            result.scenarios = ()

    def test_invalid_position_fields_and_duplicates(self):
        invalid = [
            None,
            {},
            {"symbol": "AAA"},
            dict(position(), extra=1),
            position(""),
            position(" AAA"),
            position(123),
            position(quantity=-1),
            position(unit_price=0),
            position(unit_price=-1),
        ]
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                scenario_analysis([item], {})
        with self.assertRaises(ValueError):
            scenario_analysis([position(), position()], {})
        for container in (None, 1, "text", {}, b"text"):
            with self.subTest(container=container), self.assertRaises(ValueError):
                scenario_analysis(container, {})

    def test_invalid_numbers_in_every_numeric_field(self):
        for value in (True, False, "1", None, complex(1), math.nan, math.inf, -math.inf, 10**400):
            for field in ("quantity", "unit_price"):
                item = position()
                item[field] = value
                with self.subTest(value=value, field=field), self.assertRaises(ValueError):
                    scenario_analysis([item], {})
            with self.subTest(value=value, field="shock"), self.assertRaises(ValueError):
                scenario_analysis([position()], {"x": {"AAA": value}})

    def test_invalid_scenario_structure_and_unknown_shocks(self):
        for shocks in (
            None,
            [],
            {"": {}},
            {" x": {}},
            {1: {}},
            {"x": []},
            {"x": {"": 0}},
            {"x": {1: 0}},
            {"x": {"AAA": -1.00001}},
            {"x": {"UNKNOWN": math.nan}},
            {"x": {"UNKNOWN": -2}},
        ):
            with self.subTest(shocks=shocks), self.assertRaises(ValueError):
                scenario_analysis([], shocks)

    def test_limits_and_no_rounding(self):
        row = scenario_analysis(
            [position(quantity=1, unit_price=1)], {"x": {"AAA": 0.123456789}}
        ).scenarios[0]
        self.assertEqual(row.absolute_change, 0.123456789)
        self.assertEqual(row.percentage_change, 0.123456789 * 100)
        self.assertEqual(
            scenario_analysis([position()], {"x": {"AAA": 2}}).scenarios[0].percentage_change, 200
        )
        self.assertEqual(
            scenario_analysis([position(unit_price=1e-300)], {"x": {}})
            .scenarios[0]
            .absolute_change,
            0,
        )
        overflow_cases = [
            ([position(quantity=1e308, unit_price=2)], {}),
            ([position("A", 1, 1e308), position("B", 1, 1e308)], {}),
            ([position(unit_price=1e308)], {"x": {"AAA": 1}}),
            ([position(quantity=0, unit_price=1e308)], {"x": {"AAA": 2}}),
            ([position(quantity=1, unit_price=1)], {"x": {"AAA": 1e308}}),
            ([position("A", 1, 4e307), position("B", 1, 4e307)], {"x": {"A": 2, "B": 2}}),
        ]
        for positions, shocks in overflow_cases:
            with self.subTest(positions=positions, shocks=shocks), self.assertRaises(ValueError):
                scenario_analysis(positions, shocks)


if __name__ == "__main__":
    unittest.main()
