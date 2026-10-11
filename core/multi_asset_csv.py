"""Strict local CSV importer for multi-asset adjusted closing prices.

CSV required columns: symbol,date,close,currency
Market provenance is USER-SUPPLIED FILE, not independently verified live data.
No HTTP/network credentials; no automatic trade or external file mutation.
"""
from __future__ import annotations
from collections import defaultdict
import csv
from datetime import datetime, timezone
from pathlib import Path
from core.multi_asset_comparison import AssetHistory, compare_assets


def load_price_csv(path: str | Path) -> tuple[AssetHistory, ...]:
    file = Path(path)
    if not file.is_file() or file.suffix.lower() != ".csv":
        raise ValueError("SOURCE_MUST_BE_EXISTING_CSV")
    if file.stat().st_size > 12_000_000:
        raise ValueError("SOURCE_CSV_TOO_LARGE")
    grouped: dict[str, list[tuple[str, float]]] = defaultdict(list)
    currencies: dict[str, str] = {}
    try:
        with file.open("r", encoding="utf-8-sig", newline="") as stream:
            reader=csv.DictReader(stream, strict=True)
            expected={"symbol","date","close","currency"}
            if reader.fieldnames is None or set(reader.fieldnames) != expected:
                raise ValueError("REQUIRED_COLUMNS=symbol,date,close,currency")
            for index,row in enumerate(reader, start=2):
                if index>100_001:
                    raise ValueError("SOURCE_CSV_TOO_MANY_ROWS")
                if None in row or any(value is None for value in row.values()):
                    raise ValueError(f"CSV_ROW_MALFORMED={index}")
                symbol=row["symbol"].strip().upper()
                currency=row["currency"].strip().upper()
                if not symbol or not currency:
                    raise ValueError(f"CSV_ROW_MISSING_SYMBOL_OR_CURRENCY={index}")
                if symbol in currencies and currencies[symbol] != currency:
                    raise ValueError("CURRENCY_CHANGED_WITHIN_ASSET")
                currencies[symbol]=currency
                try:
                    close=float(row["close"])
                except ValueError as exc:
                    raise ValueError(f"CSV_BAD_CLOSE_ROW={index}") from exc
                grouped[symbol].append((row["date"].strip(),close))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ValueError("CSV_READ_FAILED") from exc
    if len(grouped)<2:
        raise ValueError("CSV_NEEDS_AT_LEAST_TWO_SYMBOLS")
    asof=datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).isoformat()
    output=tuple(
        AssetHistory(symbol,currencies[symbol],tuple(rows),
                     "YEREL CSV: KULLANICI KAYNAĞI DOĞRULANMADI",asof,False)
        for symbol,rows in grouped.items()
    )
    # Validate every row and cross-asset date+currency before showing any output.
    compare_assets(output, window=2, risk_free_annual=0)
    return output
