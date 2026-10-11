"""Validated, deterministic financial chart indicators without third-party packages.

EMA is seeded by the first full-period simple mean; Wilder RSI is seeded with
the first period's average positive/negative price differences, then smoothed.
No indicator value is emitted before its documented warm-up period.
"""
from __future__ import annotations

import math
from typing import Sequence


def validate_ohlcv(rows: Sequence[tuple[float, float, float, float, float]]) -> list[float]:
    """Validate strictly positive OHLC and nonnegative finite volume.

    Returns closing prices; rejects forged/inconsistent highs/lows or NaN/Inf.
    """
    if not rows:
        raise ValueError("OHLCV is empty")
    closes: list[float] = []
    for index, candle in enumerate(rows):
        if len(candle) != 5:
            raise ValueError(f"OHLCV candle {index} has wrong length")
        try:
            op, hi, lo, close, vol = tuple(float(x) for x in candle)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"OHLCV candle {index} is not numeric") from exc
        if not all(math.isfinite(x) for x in (op, hi, lo, close, vol)):
            raise ValueError(f"OHLCV candle {index} is non-finite")
        if min(op, hi, lo, close) <= 0 or vol < 0:
            raise ValueError(f"OHLCV candle {index} has invalid magnitude")
        if hi < max(op, close, lo) or lo > min(op, close, hi):
            raise ValueError(f"OHLCV candle {index} violates price bounds")
        closes.append(close)
    return closes


def _validate_closes(values: Sequence[float], period: int) -> list[float]:
    if isinstance(period, bool) or not isinstance(period, int) or period <= 0:
        raise ValueError("indicator period must be a positive integer")
    out = []
    for value in values:
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("closing prices must be numeric") from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError("closing prices must be positive and finite")
        out.append(number)
    return out


def ema_series(values: Sequence[float], period: int) -> list[float | None]:
    """EMA(period), initial SMA at index period-1; leading values None."""
    values_ = _validate_closes(values, period)
    result: list[float | None] = [None] * len(values_)
    if len(values_) < period:
        return result
    mean = sum(values_[:period]) / period
    result[period - 1] = mean
    alpha = 2.0 / (period + 1.0)
    for index in range(period, len(values_)):
        mean += alpha * (values_[index] - mean)
        result[index] = mean
    return result


def rsi_wilder_series(values: Sequence[float], period: int = 14) -> list[float | None]:
    """Wilder RSI; first valid point at index period, neutral flat prices RSI=50."""
    values_ = _validate_closes(values, period)
    result: list[float | None] = [None] * len(values_)
    if len(values_) <= period:
        return result
    changes = [values_[i] - values_[i - 1] for i in range(1, period + 1)]
    avg_up = sum(max(change, 0) for change in changes) / period
    avg_down = sum(max(-change, 0) for change in changes) / period

    def rsi(up: float, down: float) -> float:
        if down == 0.0:
            return 50.0 if up == 0.0 else 100.0
        if up == 0.0:
            return 0.0
        return 100.0 - (100.0 / (1.0 + up / down))

    result[period] = rsi(avg_up, avg_down)
    for index in range(period + 1, len(values_)):
        difference = values_[index] - values_[index - 1]
        avg_up = (avg_up * (period - 1) + max(difference, 0)) / period
        avg_down = (avg_down * (period - 1) + max(-difference, 0)) / period
        result[index] = rsi(avg_up, avg_down)
    return result
