"""Performance statistics for an equity curve, in caller-provided time order.

Accepts backtest()['equity_curve'] directly. Returns are fractions, not
percentages. Drawdown is nonpositive, matching offline_workbench.backtest.
No frequency is assumed, no annualization is performed, and no trades are
inferred. Equity must be finite and nonnegative; negative equity is outside
this long-only/cash model and raises ValueError.
"""

import math
from collections.abc import Iterable


def performance_metrics(equity_curve: Iterable[float]) -> dict:
    """Calculate transparent statistics without sorting or changing the curve.

    Adjacent arithmetic returns are current / previous - 1. A zero previous
    equity makes that return undefined, including a zero-to-zero transition.
    Counts include only defined returns and describe observations, not trades.
    Volatility is the population standard deviation of adjacent returns and
    requires at least two returns, with every adjacent return defined. Total
    return requires two equity observations and a strictly positive start.
    Undefined metrics are None, with reasons in ``issues``. An empty curve
    has no drawdown; an all-zero curve has drawdown 0.0 because no positive
    peak has been established. A fall from a positive peak to zero is -1.0.
    Nonfinite calculated returns raise ValueError rather than leaking Inf.
    """
    values = []
    for index, value in enumerate(equity_curve):
        try:
            if isinstance(value, (bool, str, bytes)):
                raise ValueError
            value = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"Equity observation {index} must be numeric") from exc
        if not math.isfinite(value):
            raise ValueError(f"Equity observation {index} must be finite")
        if value < 0:
            raise ValueError(f"Equity observation {index} must be nonnegative")
        values.append(value)

    issues = []
    total_return = None
    if len(values) < 2:
        issues.append("Total return requires at least two equity observations.")
    elif values[0] == 0:
        issues.append("Total return is undefined when initial equity is zero.")
    else:
        total_return = values[-1] / values[0] - 1.0
        if not math.isfinite(total_return):
            raise ValueError("Total return exceeds finite numeric range")

    returns = []
    undefined = 0
    for previous, current in zip(values, values[1:], strict=False):
        if previous == 0:
            undefined += 1
            continue
        observation_return = current / previous - 1.0
        if not math.isfinite(observation_return):
            raise ValueError("Observation return exceeds finite numeric range")
        returns.append(observation_return)

    volatility = None
    if undefined:
        issues.append(
            f"{undefined} adjacent return observation(s) are undefined due to "
            "zero previous equity; volatility is unavailable."
        )
    if len(returns) < 2:
        issues.append("Volatility requires at least two defined return observations.")
    elif not undefined:
        # Scale before squaring to avoid overflow for large finite returns.
        scale = max(abs(value) for value in returns)
        if scale == 0:
            volatility = 0.0
        else:
            scaled = [value / scale for value in returns]
            mean = math.fsum(scaled) / len(scaled)
            variance = math.fsum((value - mean) ** 2 for value in scaled) / len(scaled)
            volatility = math.sqrt(variance) * scale
            if not math.isfinite(volatility):
                raise ValueError("Volatility exceeds finite numeric range")

    drawdown = None
    if values:
        peak = 0.0
        drawdown = 0.0
        for value in values:
            peak = max(peak, value)
            if peak > 0:
                drawdown = min(drawdown, value / peak - 1.0)
    else:
        issues.append("Maximum drawdown requires an equity observation.")

    return {
        "observations": len(values),
        "return_observations": len(returns),
        "undefined_return_observations": undefined,
        "total_return": total_return,
        "maximum_drawdown": drawdown,
        "return_volatility": volatility,
        "positive_return_observations": sum(value > 0 for value in returns),
        "negative_return_observations": sum(value < 0 for value in returns),
        "zero_return_observations": sum(value == 0 for value in returns),
        "volatility_basis": "population standard deviation per observation; not annualized",
        "issues": issues,
    }
