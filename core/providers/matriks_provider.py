"""Read-only Matriks Analist REST adapter for the time-limited test environment.

No trading, order, account or balance operations are implemented.
Official references: https://analistdocs.matriksdata.com/ and
https://analistdocs.matriksdata.com/tarihsel-tick-veriler/bar
"""

from __future__ import annotations

import math
import os
import re
from datetime import date
from typing import Any

import requests

from .base_provider import BaseProvider


class MatriksConfigurationError(RuntimeError):
    """Missing test credentials or an explicitly required test parameter."""


class MatriksProvider(BaseProvider):
    """Fetch authenticated OHLCV bars and public discovery metadata."""

    DISCOVERY_URL = "https://apitest.matriksdata.com/disco-v2.json"
    BAR_URL = "https://apitest.matriksdata.com/dumrul/v1/tick/bar.gz"
    PERIODS = frozenset({"1min", "5min", "1hour", "1day"})
    SYMBOL_PATTERN = re.compile(r"^[A-Z0-9._-]{1,32}$")

    def __init__(
        self,
        *,
        token: str | None = None,
        issuer: str | None = None,
        session: requests.Session | None = None,
        timeout: float = 10.0,
        symbol: str | None = None,
        start: str | None = None,
        end: str | None = None,
        period: str = "1day",
    ) -> None:
        self._token = token if token is not None else os.getenv("MATRIKS_TEST_TOKEN", "")
        self.issuer = issuer if issuer is not None else os.getenv("MATRIKS_ISSUER", "")
        self.session = session
        self.timeout = timeout
        self.default_query = (symbol, start, end, period)

    def connect(self) -> None:
        """Create an HTTP session; does not activate or consume a test token."""
        if self.session is None:
            self.session = requests.Session()

    def discover(self) -> dict[str, Any]:
        """Query the public discovery endpoint using Matriks-issued project issuer."""
        if not self.issuer.strip():
            raise MatriksConfigurationError("MATRIKS_ISSUER is required for discovery")
        self.connect()
        assert self.session is not None
        response = self.session.get(
            self.DISCOVERY_URL,
            params={"issuer": self.issuer.strip()},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("rest"), dict):
            raise ValueError("Unexpected Matriks discovery response")
        return payload

    def _auth_headers(self) -> dict[str, str]:
        token = self._token.strip()
        if not token:
            raise MatriksConfigurationError(
                "MATRIKS_TEST_TOKEN is missing; request activation only after test readiness"
            )
        return {"Authorization": f"jwt {token}", "Accept": "application/json"}

    @staticmethod
    def _validate_date(value: str) -> date:
        try:
            parsed = date.fromisoformat(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Dates must use YYYY-MM-DD") from exc
        if parsed.isoformat() != value:
            raise ValueError("Dates must use YYYY-MM-DD")
        return parsed

    def fetch_bars(
        self,
        *,
        symbol: str,
        start: str,
        end: str,
        period: str = "1day",
    ) -> list[dict[str, Any]]:
        """Fetch licensed historical bars; never send an order or account request."""
        if not isinstance(symbol, str) or not self.SYMBOL_PATTERN.fullmatch(symbol):
            raise ValueError("Invalid Matriks symbol")
        if period not in self.PERIODS:
            raise ValueError("Unsupported Matriks bar period")
        if self._validate_date(start) > self._validate_date(end):
            raise ValueError("Start date must be on or before end date")
        headers = self._auth_headers()  # Fail locally before any network call.
        self.connect()
        assert self.session is not None
        response = self.session.get(
            self.BAR_URL,
            params={"symbol": symbol, "start": start, "end": end, "period": period},
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        parsed = self.parse(response.json(), symbol=symbol)
        if not self.validate(parsed):
            raise ValueError("Invalid or inconsistent Matriks bar response")
        return parsed

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch the optional default bar query configured at initialization."""
        symbol, start, end, period = self.default_query
        if not all((symbol, start, end)):
            raise MatriksConfigurationError("Configure symbol, start and end or use fetch_bars")
        return self.fetch_bars(symbol=symbol, start=start, end=end, period=period)

    def parse(self, raw_data: Any, *, symbol: str | None = None) -> list[dict[str, Any]]:
        """Map Matriks bar fields into a normalized, timestamped series.

        totalQuantity is share volume; Matriks 'volume' is retained as turnover.
        """
        if not isinstance(raw_data, list):
            raise TypeError("Matriks bar response must be a list")
        result = []
        for item in raw_data:
            if not isinstance(item, dict):
                raise TypeError("Matriks bar entry must be an object")
            result.append(
                {
                    "symbol": symbol or item.get("symbol"),
                    "timestamp_ms": int(item["time"]),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "volume": float(item["totalQuantity"]),
                    "turnover": float(item["volume"]),
                }
            )
        return result

    def validate(self, parsed_data: Any) -> bool:
        if not isinstance(parsed_data, list):
            return False
        try:
            previous_timestamp = 0
            for bar in parsed_data:
                if bar["timestamp_ms"] <= previous_timestamp:
                    return False
                previous_timestamp = bar["timestamp_ms"]
                values = [
                    bar["open"], bar["high"], bar["low"], bar["close"],
                    bar["volume"], bar["turnover"],
                ]
                if not all(math.isfinite(value) for value in values):
                    return False
                if min(values[:4]) <= 0 or min(values[4:]) < 0:
                    return False
                if bar["high"] < max(bar["open"], bar["low"], bar["close"]):
                    return False
                if bar["low"] > min(bar["open"], bar["high"], bar["close"]):
                    return False
                if bar["timestamp_ms"] <= 0:
                    return False
        except (TypeError, KeyError, ValueError):
            return False
        return True
