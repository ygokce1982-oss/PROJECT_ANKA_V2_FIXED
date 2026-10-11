"""Pure Python, offline, long-only scenario valuation; no orders or forecasts.

Shocks are named scenarios: {scenario_name: {symbol: fractional_change}}.
Missing-symbol shocks default to zero and are reported explicitly. All prices
must share one quote currency. Percentage outputs use percent units (10 = 10%).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from numbers import Real


@dataclass(frozen=True)
class PositionScenario:
    """One hypothetical valuation; percentage is undefined for zero exposure."""

    symbol: str
    quantity: float
    unit_price: float
    shock: float
    shock_defaulted: bool
    scenario_price: float
    current_value: float
    scenario_value: float
    absolute_change: float
    percentage_change: float | None


@dataclass(frozen=True)
class ScenarioResult:
    """Positions sorted by symbol and their aggregate hypothetical valuation."""

    name: str
    positions: tuple[PositionScenario, ...]
    current_value: float
    scenario_value: float
    absolute_change: float
    percentage_change: float | None
    defaulted_symbols: tuple[str, ...]
    unused_shock_symbols: tuple[str, ...]
    issues: tuple[str, ...]


@dataclass(frozen=True)
class ScenarioAnalysis:
    """Immutable results sorted by scenario name; no external state is used."""

    scenarios: tuple[ScenarioResult, ...]
    assumptions: tuple[str, ...] = (
        "Missing-symbol shocks default to 0.0.",
        "All positions use one quote currency; quantities are long-only.",
        "Fees, taxes, FX, liquidity and cash are excluded.",
        "Hypothetical arithmetic only; no forecasts, live prices or orders.",
    )


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{label} must be a real number, not bool or text")
    try:
        result = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must fit a finite float") from exc
    return _finite(result, label)


def _finite(value: float, label: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{label} exceeds finite float range")
    return value


def _name(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be a nonempty string without edge whitespace")
    return value


def _sum(values: Iterable[float], label: str) -> float:
    try:
        return _finite(math.fsum(values), label)
    except OverflowError as exc:
        raise ValueError(f"{label} exceeds finite float range") from exc


def scenario_analysis(
    positions: Iterable[Mapping[str, object]],
    shocks: Mapping[str, Mapping[str, object]],
) -> ScenarioAnalysis:
    """Calculate deterministic position and portfolio P&L for named scenarios.

    Position fields are exactly symbol, quantity and unit_price. Symbols and
    scenario names are case-sensitive. Duplicate positions, extra fields,
    nonfinite numbers, negative quantities, nonpositive current prices and
    shocks below -1 raise ValueError. Unknown shock symbols are validated and
    reported, but contribute no exposure. Zero quantities are valid; their
    percentage change is None. A zero-value portfolio also has percentage None.

    P&L = current_value * shock; scenario_price = unit_price * (1 + shock).
    Portfolio percentage = total P&L / total current_value * 100. No internal
    rounding is applied. Float overflow raises ValueError; ordinary binary float
    precision and underflow limitations apply. Inputs are never mutated.
    """
    if isinstance(positions, (str, bytes, Mapping)):
        raise ValueError("positions must be an iterable of position mappings")
    try:
        iterator = iter(positions)
    except TypeError as exc:
        raise ValueError("positions must be iterable") from exc
    validated: dict[str, tuple[float, float, float]] = {}
    for position in iterator:
        if not isinstance(position, Mapping) or set(position) != {
            "symbol",
            "quantity",
            "unit_price",
        }:
            raise ValueError("Each position requires exactly symbol, quantity, unit_price")
        symbol = _name(position["symbol"], "symbol")
        if symbol in validated:
            raise ValueError(f"Duplicate symbol: {symbol}")
        quantity = _number(position["quantity"], f"{symbol} quantity")
        price = _number(position["unit_price"], f"{symbol} unit_price")
        if quantity < 0 or price <= 0:
            raise ValueError("Quantity must be nonnegative and current price positive")
        validated[symbol] = (quantity, price, _finite(quantity * price, "current value"))
    if not isinstance(shocks, Mapping):
        raise ValueError("shocks must map scenario names to symbol shock mappings")
    normalized: dict[str, dict[str, float]] = {}
    for raw_name, raw_shocks in shocks.items():
        name = _name(raw_name, "scenario name")
        if not isinstance(raw_shocks, Mapping):
            raise ValueError("Each scenario must be a symbol shock mapping")
        changes: dict[str, float] = {}
        for raw_symbol, raw_change in raw_shocks.items():
            symbol = _name(raw_symbol, "shock symbol")
            change = _number(raw_change, f"{name}/{symbol} shock")
            if change < -1:
                raise ValueError("Shock must be at least -1")
            changes[symbol] = change
        normalized[name] = changes
    current_total = _sum((row[2] for row in validated.values()), "portfolio current value")
    results = []
    for name in sorted(normalized):
        changes = normalized[name]
        rows = []
        issues = []
        for symbol in sorted(validated):
            quantity, price, current = validated[symbol]
            defaulted = symbol not in changes
            shock = changes.get(symbol, 0.0)
            scenario_price = _finite(price * (1.0 + shock), "scenario price")
            pnl = _finite(current * shock, "position P&L")
            scenario_value = _finite(current + pnl, "scenario value")
            percentage = _finite(shock * 100.0, "position percentage") if current else None
            if percentage is None:
                issues.append(f"{symbol}: percentage undefined because current exposure is zero.")
            rows.append(
                PositionScenario(
                    symbol,
                    quantity,
                    price,
                    shock,
                    defaulted,
                    scenario_price,
                    current,
                    scenario_value,
                    pnl,
                    percentage,
                )
            )
        defaulted_symbols = tuple(row.symbol for row in rows if row.shock_defaulted)
        if defaulted_symbols:
            issues.append("Missing-symbol shocks defaulted to 0.0: " + ", ".join(defaulted_symbols))
        pnl_total = _sum((row.absolute_change for row in rows), "portfolio P&L")
        scenario_total = _sum((row.scenario_value for row in rows), "portfolio scenario value")
        percentage_total = (
            _finite((pnl_total / current_total) * 100.0, "portfolio percentage")
            if current_total
            else None
        )
        if percentage_total is None:
            issues.append("Portfolio percentage undefined because current exposure is zero.")
        unused = tuple(sorted(set(changes) - set(validated)))
        if unused:
            issues.append("Shock symbols without positions: " + ", ".join(unused))
        results.append(
            ScenarioResult(
                name,
                tuple(rows),
                current_total,
                scenario_total,
                pnl_total,
                percentage_total,
                defaulted_symbols,
                unused,
                tuple(issues),
            )
        )
    return ScenarioAnalysis(tuple(results))
