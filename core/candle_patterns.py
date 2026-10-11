"""Offline candle geometry recognition, without predictions or trading advice.

recognize requires at least 35 chronologically ordered, timezone-aware bars,
matching offline_workbench.validated. A result uses only its current bar and,
for engulfing, its immediately preceding bar. No trend confirmation is implied.

For each bar, body = abs(close - open), upper = high - max(open, close),
and lower = min(open, close) - low.

Bullish engulfing: previous close < previous open, current close > current
open, current open <= previous close, current close >= previous open, and
at least one containment boundary is strict. Bearish engulfing is the reverse.
Only real bodies are engulfed; wick containment is not required. Equal bodies
and doji candles do not qualify.

Hammer: body > 0, lower >= 2 * body, upper <= body / 2.
Shooting star: body > 0, upper >= 2 * body, lower <= body / 2.
These shape labels are independent of candle color and prior trend. Thresholds
are inclusive, use direct floating-point comparisons, and have no tolerance.
Volume is validated but does not affect recognition. Inputs must be closed
bars supplied by the caller; this module cannot determine whether a bar closed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from core.offline_workbench import Bar, validated


@dataclass(frozen=True)
class CandlePatterns:
    """Observed shapes at an input index; flags are not forecasts."""

    index: int
    time: str
    bullish_engulfing: bool
    bearish_engulfing: bool
    hammer: bool
    shooting_star: bool


def recognize(bars: Sequence[Bar]) -> list[CandlePatterns]:
    """Validate a snapshot and return one result per bar, in input order.

    Raises ValueError for invalid OHLCV, timestamps, or fewer than 35 bars,
    using the shared validator. The first bar has no engulfing classification.
    The input sequence and its immutable Bar objects are never modified.
    """
    snapshot = validated(list(bars))
    results = []
    for index, bar in enumerate(snapshot):
        body = abs(bar.close - bar.open)
        upper = bar.high - max(bar.open, bar.close)
        lower = min(bar.open, bar.close) - bar.low
        bullish = bearish = False
        if index:
            previous = snapshot[index - 1]
            bullish = (
                previous.close < previous.open
                and bar.close > bar.open
                and bar.open <= previous.close
                and bar.close >= previous.open
                and (bar.open < previous.close or bar.close > previous.open)
            )
            bearish = (
                previous.close > previous.open
                and bar.close < bar.open
                and bar.open >= previous.close
                and bar.close <= previous.open
                and (bar.open > previous.close or bar.close < previous.open)
            )
        results.append(
            CandlePatterns(
                index=index,
                time=bar.time,
                bullish_engulfing=bullish,
                bearish_engulfing=bearish,
                hammer=body > 0 and lower >= 2 * body and upper <= body / 2,
                shooting_star=body > 0 and upper >= 2 * body and lower <= body / 2,
            )
        )
    return results
