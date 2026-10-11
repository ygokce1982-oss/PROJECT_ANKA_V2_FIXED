"""Deterministic, offline trade risk planner; never submits orders.

The plan is based on user-provided prices, not live market data or a signal.
One-way capital exposure is capped at equity (no leverage). Both LONG and
SHORT are hypothetical analysis only; the paper portfolio remains long-only.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal, InvalidOperation


@dataclass(frozen=True)
class RiskPlan:
    side: str
    entry: float
    stop: float
    target: float
    equity: float
    risk_fraction: float
    fee_rate: float
    lot_step: float
    quantity: float
    risk_budget: float
    risk_per_unit: float
    potential_loss: float
    potential_reward: float
    reward_risk_ratio: float
    notional: float
    live: bool = False
    sends_orders: bool = False


def _number(name: str, value: float, *, minimum: Decimal | None = None) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{name} sayisal olmali")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{name} sayisal olmali") from exc
    if not result.is_finite() or (minimum is not None and result <= minimum):
        raise ValueError(f"{name} sonlu ve {minimum} degerinden buyuk olmali")
    return result


def calculate_risk_plan(
    *,
    side: str,
    entry: float,
    stop: float,
    target: float,
    equity: float,
    risk_fraction: float = 0.01,
    fee_rate: float = 0.001,
    lot_step: float = 1,
) -> RiskPlan:
    """Calculate a non-leveraged position plan for hypothetical LONG/SHORT.

    Fees are conservatively included at both entry and stop/target. Prices,
    fees, equity and lot sizes all use the same declared quote currency.
    A risk fraction above 10% is rejected. Returns zero live/order actions.
    """
    if side not in ("LONG", "SHORT"):
        raise ValueError("Yon LONG veya SHORT olmali")

    zero = Decimal(0)
    e = _number("entry", entry, minimum=zero)
    s = _number("stop", stop, minimum=zero)
    t = _number("target", target, minimum=zero)
    c = _number("equity", equity, minimum=zero)
    r = _number("risk_fraction", risk_fraction, minimum=zero)
    fee = _number("fee_rate", fee_rate)
    step = _number("lot_step", lot_step, minimum=zero)

    if r > Decimal("0.1"):
        raise ValueError("Risk orani %10 u asamaz")
    if fee < 0 or fee > Decimal("0.05"):
        raise ValueError("Komisyon 0 ile %5 arasinda olmali")
    if (side == "LONG" and not s < e < t) or (side == "SHORT" and not t < e < s):
        raise ValueError("Giris, stop ve hedef yonle uyusmuyor")

    risk_per_unit = abs(e - s) + (e + s) * fee
    reward_per_unit = abs(t - e) - (e + t) * fee
    budget = c * r
    risk_limited = budget / risk_per_unit
    capital_limited = c / (e * (Decimal(1) + fee))
    units = (min(risk_limited, capital_limited) / step).to_integral_value(
        rounding=ROUND_FLOOR
    ) * step

    if units <= 0:
        raise ValueError("Sermaye ve risk sinirlariyla asgari lot alinamiyor")

    return RiskPlan(
        side=side,
        entry=float(e),
        stop=float(s),
        target=float(t),
        equity=float(c),
        risk_fraction=float(r),
        fee_rate=float(fee),
        lot_step=float(step),
        quantity=float(units),
        risk_budget=float(budget),
        risk_per_unit=float(risk_per_unit),
        potential_loss=float(units * risk_per_unit),
        potential_reward=float(units * reward_per_unit),
        reward_risk_ratio=float(reward_per_unit / risk_per_unit),
        notional=float(units * e),
    )
