"""Deterministic, bounded OHLCV inspection; no I/O or data repair."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class Finding:
    row: int
    field: str
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class QualityReport:
    findings: tuple[Finding, ...]
    rows_checked: int
    total_rows: int
    row_limit_reached: bool
    finding_limit_reached: bool

    @property
    def complete(self) -> bool:
        return not (self.row_limit_reached or self.finding_limit_reached)

    @property
    def ok(self) -> bool:
        return self.complete and not self.findings


_MISSING = object()
_FIELDS = ("open", "high", "low", "close", "volume")


def check_bars(
    rows: list | tuple, *, max_rows: int = 20_000, max_findings: int = 1_000
) -> QualityReport:
    """Inspect dicts or attribute-based bars without modifying them.

    Row numbers are one-based. Timestamp accepts an aware datetime or ISO
    string (at most 128 characters); 'time' is a fallback for absent
    'timestamp', matching offline_workbench.Bar. Numeric fields accept only
    built-in int/float, excluding bool. Zero prices are permitted.
    Reaching the findings cap stops immediately and conservatively marks
    the report incomplete, even if that finding would have been the last.
    """
    if type(rows) not in (list, tuple):
        raise TypeError("rows must be a built-in list or tuple")
    for name, value in (("max_rows", max_rows), ("max_findings", max_findings)):
        if type(value) is not int or value <= 0:
            raise ValueError(f"{name} must be a positive integer")

    findings: list[Finding] = []
    seen: dict[datetime, int] = {}
    previous: datetime | None = None
    checked = 0
    total = len(rows)

    def add(row: int, field: str, code: str, message: str) -> bool:
        findings.append(Finding(row, field, code, "error", message))
        return len(findings) >= max_findings

    def report() -> QualityReport:
        return QualityReport(
            tuple(findings),
            checked,
            total,
            total > max_rows,
            len(findings) >= max_findings,
        )

    for index in range(min(total, max_rows)):
        row_number = index + 1
        checked = row_number
        entry = rows[index]
        values: dict[str, object] = {}
        for field in ("timestamp", *_FIELDS):
            try:
                if type(entry) is dict:
                    value = entry.get(field, _MISSING)
                    if field == "timestamp" and value is _MISSING:
                        value = entry.get("time", _MISSING)
                else:
                    value = getattr(entry, field, _MISSING)
                    if field == "timestamp" and value is _MISSING:
                        value = getattr(entry, "time", _MISSING)
            except Exception:
                if add(row_number, field, "field_access", "Field could not be read."):
                    return report()
                continue
            if value is _MISSING:
                if add(row_number, field, "missing_field", "Required field is absent."):
                    return report()
            else:
                values[field] = value

        if "timestamp" in values:
            raw = values["timestamp"]
            try:
                if type(raw) is datetime:
                    timestamp = raw
                elif type(raw) is str and len(raw) <= 128:
                    timestamp = datetime.fromisoformat(raw)
                else:
                    raise ValueError("Unsupported timestamp")
                if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    raise ValueError("Timezone required")
                timestamp = timestamp.astimezone(UTC)
            except (ValueError, TypeError, OverflowError):
                if add(
                    row_number,
                    "timestamp",
                    "invalid_timestamp",
                    "Expected a timezone-aware ISO timestamp or datetime.",
                ):
                    return report()
            else:
                if timestamp in seen:
                    if add(
                        row_number,
                        "timestamp",
                        "duplicate_timestamp",
                        f"Timestamp duplicates row {seen[timestamp]}.",
                    ):
                        return report()
                else:
                    seen[timestamp] = row_number
                if previous is not None and timestamp < previous:
                    if add(
                        row_number,
                        "timestamp",
                        "timestamp_order",
                        "Timestamp precedes the previous valid timestamp.",
                    ):
                        return report()
                previous = timestamp

        numeric: dict[str, int | float] = {}
        for field in _FIELDS:
            if field not in values:
                continue
            value = values[field]
            if type(value) not in (int, float):
                if add(
                    row_number, field, "invalid_number", "Expected an int or float, excluding bool."
                ):
                    return report()
                continue
            # Integers are finite without converting potentially enormous ints.
            if type(value) is float and not math.isfinite(value):
                if add(row_number, field, "non_finite", "Numeric field is not finite."):
                    return report()
                continue
            numeric[field] = value
            if value < 0:
                if add(row_number, field, "negative_value", "Numeric field is negative."):
                    return report()

        if all(field in numeric for field in _FIELDS[:4]):
            open_, high, low, close = (numeric[field] for field in _FIELDS[:4])
            if high < max(open_, close, low):
                if add(row_number, "high", "high_bounds", "High is below an OHLC value."):
                    return report()
            if low > min(open_, close, high):
                if add(row_number, "low", "low_bounds", "Low is above an OHLC value."):
                    return report()

    return report()
