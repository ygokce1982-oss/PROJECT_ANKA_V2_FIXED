"""Multi-asset comparison: strict calendar and currency alignment, no silent fill.

Returns are percentages for charts. Risk-free rate is an *effective annual*
rate; it becomes an effective per-observation rate using periods_per_year.
Sharpe is annualized (sqrt(periods_per_year)) with sample standard deviation.
A window of N means N matched daily return observations, not N price points.
Undefined zero-volatility Sharpe is None, never infinity or artificial zero.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from collections.abc import Sequence
import math


@dataclass(frozen=True)
class AssetHistory:
    symbol: str
    currency: str
    observations: tuple[tuple[str, float], ...]  # (ISO calendar day, adjusted close)
    source: str
    asof_utc: str
    demo: bool = False


@dataclass(frozen=True)
class AssetResult:
    symbol: str
    cumulative_percent: tuple[float, ...]
    rolling_sharpe: tuple[float | None, ...]


@dataclass(frozen=True)
class Comparison:
    dates: tuple[str, ...]
    currency: str
    series: tuple[AssetResult, ...]
    window: int
    risk_free_annual: float
    periods_per_year: int
    sources: tuple[str, ...]
    demo: bool
    warnings: tuple[str, ...]


def compare_assets(
    histories: Sequence[AssetHistory],
    *,
    window: int = 90,
    risk_free_annual: float = 0.03,
    periods_per_year: int = 252,
) -> Comparison:
    if isinstance(window, bool) or not isinstance(window, int) or window < 2:
        raise ValueError("window must be at least two daily returns")
    if isinstance(periods_per_year, bool) or not isinstance(periods_per_year, int) or periods_per_year < 2:
        raise ValueError("periods_per_year must be an integer >= 2")
    if isinstance(risk_free_annual, bool) or not isinstance(risk_free_annual, (int, float)):
        raise ValueError("risk_free_annual must be numeric")
    if not math.isfinite(risk_free_annual) or risk_free_annual <= -1:
        raise ValueError("risk_free_annual must be finite and greater than -100%")
    if len(histories) < 2:
        raise ValueError("at least two assets are required")

    names, currencies, clean = set(), set(), []
    for item in histories:
        if not isinstance(item, AssetHistory):
            raise ValueError("all series must be AssetHistory")
        if not item.symbol or item.symbol in names:
            raise ValueError("asset identifiers must be nonempty and unique")
        if not item.currency or not item.source or not item.asof_utc:
            raise ValueError("currency, source and asof_utc must be declared")
        names.add(item.symbol)
        currencies.add(item.currency.upper())
        try:
            parsed_ts = datetime.fromisoformat(item.asof_utc.replace("Z", "+00:00"))
            if parsed_ts.tzinfo is None or parsed_ts.utcoffset() is None:
                raise ValueError
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{item.symbol}: asof_utc must include a timezone") from exc
        if parsed_ts.astimezone(timezone.utc) > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ValueError(f"{item.symbol}: FUTURE_SOURCE_TIMESTAMP")

        checked = {}
        last_day = None
        for raw_day, raw_price in item.observations:
            try:
                day = date.fromisoformat(raw_day)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{item.symbol}: invalid ISO date") from exc
            if last_day is not None and day <= last_day:
                raise ValueError(f"{item.symbol}: dates must be strictly increasing")
            if isinstance(raw_price, bool) or not isinstance(raw_price, (int, float)):
                raise ValueError(f"{item.symbol}: price must be numeric")
            price = float(raw_price)
            if not math.isfinite(price) or price <= 0:
                raise ValueError(f"{item.symbol}: close must be finite and positive")
            checked[day] = price
            last_day = day
        clean.append(checked)

    if len(currencies) != 1:
        raise ValueError("MIXED_CURRENCY_REQUIRES_FX_CONVERSION")

    common = set(clean[0])
    for mapping in clean[1:]:
        common.intersection_update(mapping)
    aligned = tuple(sorted(common))
    if len(aligned) < 2:
        raise ValueError("NO_COMMON_RETURN_INTERVAL")

    # If any other asset traded between two matched closes, the change
    # spans multiple known observations and is not one daily Sharpe return.
    # Real exchange calendars still require separate source verification.
    union_days = sorted(set().union(*(set(mapping) for mapping in clean)))
    session_index = {day: i for i, day in enumerate(union_days)}
    valid_intervals = tuple(
        session_index[right] - session_index[left] == 1
        for left, right in zip(aligned, aligned[1:])
    )

    daily_rf = math.expm1(math.log1p(risk_free_annual) / periods_per_year)
    annualizer = math.sqrt(periods_per_year)
    output = []
    for item, mapping in zip(histories, clean, strict=True):
        prices = [mapping[day] for day in aligned]
        first = prices[0]
        cumulative = []
        for price in prices:
            value = (price / first - 1.0) * 100.0
            if not math.isfinite(value):
                raise ValueError("cumulative return not representable")
            cumulative.append(value)
        excess: list[float | None] = []
        for valid, previous, current in zip(valid_intervals, prices[:-1], prices[1:], strict=True):
            if not valid:
                excess.append(None)
                continue
            daily = current / previous - 1.0
            if not math.isfinite(daily):
                raise ValueError("daily return not representable")
            excess.append(daily - daily_rf)
        sharpe: list[float | None] = [None] * len(prices)
        for end in range(window, len(prices)):
            block = excess[end-window:end]
            if any(value is None for value in block):
                continue
            mean = math.fsum(block) / window
            squares = math.fsum((value - mean)**2 for value in block)
            std = math.sqrt(squares / (window - 1))
            if std > 1e-15:
                result = mean / std * annualizer
                if not math.isfinite(result):
                    raise ValueError("Sharpe ratio not representable")
                sharpe[end] = result
        output.append(AssetResult(item.symbol, tuple(cumulative), tuple(sharpe)))
    warnings = [
        "Matched dates only: missing sessions are excluded globally; no forward-filling.",
        "Same displayed currency; currency conversion must happen upstream.",
        f"Rolling Sharpe: {window} common daily returns; sample volatility; {periods_per_year} trading sessions/year.",
    ]
    if not all(valid_intervals):
        warnings.append("KNOWN_MISSING_SESSIONS: rolling Sharpe remains undefined for windows spanning observed calendar gaps.")
    warnings.append("Exchange calendar and adjusted-close provenance are not independently verified.")
    if len(aligned) <= window:
        warnings.append(f"Insufficient aligned history: Sharpe needs {window + 1} common closes.")
    if any(item.demo for item in histories):
        warnings.append("DEMO: synthetic data must not be presented as live market prices.")
    return Comparison(
        dates=tuple(day.isoformat() for day in aligned),
        currency=next(iter(currencies)),
        series=tuple(output),
        window=window,
        risk_free_annual=float(risk_free_annual),
        periods_per_year=periods_per_year,
        sources=tuple(item.source for item in histories),
        demo=any(item.demo for item in histories),
        warnings=tuple(warnings),
    )
