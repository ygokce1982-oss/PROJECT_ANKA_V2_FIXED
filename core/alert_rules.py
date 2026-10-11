"""Deterministic offline threshold evaluation; no I/O or implicit clock."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AlertResult:
    rule_id: str
    symbol: str
    price: float | None
    matched: bool
    fired: bool
    reason: str
    fired_at: float | None


def _number(
    value: object, field: str, *, positive: bool = False, nonnegative: bool = False
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field}: int veya float gerekli")
    try:
        number = float(value)
    except (OverflowError, ValueError) as error:
        raise ValueError(f"{field}: sonlu sayı gerekli") from error
    if not math.isfinite(number):
        raise ValueError(f"{field}: sonlu sayı gerekli")
    if positive and number <= 0:
        raise ValueError(f"{field}: pozitif sayı gerekli")
    if nonnegative and number < 0:
        raise ValueError(f"{field}: negatif olmayan sayı gerekli")
    return number


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field}: boş olmayan metin gerekli")
    if value != value.strip():
        raise ValueError(f"{field}: başta veya sonda boşluk olmamalı")
    return value


def evaluate_alerts(
    rules: list[Mapping[str, object]] | tuple[Mapping[str, object], ...],
    prices: Mapping[str, object],
    *,
    observed_at: int | float,
    last_fired: Mapping[str, object] | None = None,
    cooldown_seconds: int | float = 0,
) -> tuple[AlertResult, ...]:
    """Evaluate one observation batch in rule order without mutating inputs.

    Timestamps are finite, nonnegative seconds on one caller-defined timeline.
    A matching rule fires unless its last-fired timestamp equals observed_at
    (dedup), or elapsed seconds are strictly less than cooldown_seconds.
    Equality never matches. Missing prices never match. All inputs, including
    unused prices and history entries, are validated before evaluation.
    History keys must refer to current rule IDs; future history is rejected.
    No state is retained: callers must explicitly pass history on every call.
    """
    if not isinstance(rules, (list, tuple)):
        raise ValueError("rules: liste veya tuple gerekli")
    if not isinstance(prices, Mapping):
        raise ValueError("prices: eşleme gerekli")
    if last_fired is not None and not isinstance(last_fired, Mapping):
        raise ValueError("last_fired: eşleme gerekli")
    now = _number(observed_at, "observed_at", nonnegative=True)
    cooldown = _number(cooldown_seconds, "cooldown_seconds", nonnegative=True)
    validated = []
    ids = set()
    required = {"symbol", "comparison", "threshold", "rule_id"}
    for rule in rules:
        if not isinstance(rule, Mapping) or set(rule) != required:
            raise ValueError("Kural tam olarak symbol, comparison, threshold, rule_id içermeli")
        rule_id = _text(rule["rule_id"], "rule_id")
        symbol = _text(rule["symbol"], "symbol")
        comparison = rule["comparison"]
        if not isinstance(comparison, str) or comparison not in (">", "<"):
            raise ValueError("comparison: > veya < gerekli")
        threshold = _number(rule["threshold"], "threshold", positive=True)
        if rule_id in ids:
            raise ValueError("rule_id benzersiz olmalı")
        ids.add(rule_id)
        validated.append((rule_id, symbol, comparison, threshold))
    observations = {
        _text(symbol, "prices symbol"): _number(price, "price") for symbol, price in prices.items()
    }
    history = {}
    for rule_id, stamp in ({} if last_fired is None else last_fired).items():
        key = _text(rule_id, "last_fired rule_id")
        if key not in ids:
            raise ValueError("last_fired bilinmeyen rule_id içeriyor")
        timestamp = _number(stamp, "last_fired timestamp", nonnegative=True)
        if timestamp > now:
            raise ValueError("last_fired observed_at sonrasında olamaz")
        history[key] = timestamp
    results = []
    for rule_id, symbol, comparison, threshold in validated:
        price = observations.get(symbol)
        matched = False
        fired = False
        if price is None:
            reason = "missing_symbol"
        else:
            matched = price > threshold if comparison == ">" else price < threshold
            previous = history.get(rule_id)
            if not matched:
                reason = "threshold_not_met"
            elif previous is not None and previous == now:
                reason = "duplicate_timestamp"
            elif previous is not None and now - previous < cooldown:
                reason = "cooldown_active"
            else:
                fired = True
                reason = "threshold_match"
        results.append(
            AlertResult(rule_id, symbol, price, matched, fired, reason, now if fired else None)
        )
    return tuple(results)
