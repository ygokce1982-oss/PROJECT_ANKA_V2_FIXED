"""PROJECT ANKA piyasa veri işlemleri."""

import logging
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import requests

from core.providers.crypto_provider import CryptoProvider
from core.providers.forex_provider import ForexProvider

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MarketSnapshot:
    """Arayüzde gösterilecek piyasa değerleri."""

    values: dict[str, str]
    errors: tuple[str, ...] = ()


class MarketData:
    EXCHANGE_RATES_URL = "https://open.er-api.com/v6/latest/USD"

    COINGECKO_BTC_URL = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd"
    )

    BINANCE_BTC_URL = (
        "https://data-api.binance.vision/api/v3/ticker/price"
        "?symbol=BTCUSDT"
    )

    # Eski testlerle uyumluluk için korunuyor.
    BTC_SPOT_URL = COINGECKO_BTC_URL

    REQUEST_TIMEOUT = 8

    @staticmethod
    def empty_values() -> dict[str, str]:
        return {
            "xu100": "Yakında",
            "usdtry": "---",
            "eurtry": "---",
            "gold": "Yakında",
            "btc": "---",
        }

    @classmethod
    def error_snapshot(cls, message: str) -> MarketSnapshot:
        return MarketSnapshot(
            values=cls.empty_values(),
            errors=(message,),
        )

    @classmethod
    def get_snapshot(
        cls,
        session: Any | None = None,
    ) -> MarketSnapshot:
        values = cls.empty_values()
        errors: list[str] = []

        owns_session = session is None
        client = session or requests.Session()

        try:
            try:
                cls._load_exchange_rates(client, values)
            except Exception as exc:
                LOGGER.warning(
                    "Döviz verisi alınamadı: %s",
                    exc,
                )
                errors.append("Döviz verisi alınamadı")

            try:
                cls._load_btc_price(client, values)
            except Exception as exc:
                LOGGER.warning(
                    "BTC verisi alınamadı: %s",
                    exc,
                )
                errors.append("BTC verisi alınamadı")
        finally:
            if owns_session:
                client.close()

        return MarketSnapshot(
            values=values,
            errors=tuple(errors),
        )

    @classmethod
    def get_data(cls) -> dict[str, str]:
        """Yalnızca piyasa değerlerini döndürür."""

        return cls.get_snapshot().values

    @staticmethod
    def _require_mapping(
        value: object,
        field_name: str,
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise ValueError(
                f"{field_name} nesne biçiminde olmalı"
            )
        return value

    @staticmethod
    def _positive_finite_number(
        value: object,
        field_name: str,
    ) -> float:
        if isinstance(value, bool):
            raise ValueError(
                f"{field_name} sayısal değil"
            )

        normalized = value
        if isinstance(value, str):
            text = (
                value.strip()
                .replace("\u00a0", "")
                .replace(" ", "")
                .replace("₺", "")
                .replace("$", "")
                .replace("€", "")
            )

            if "," in text and "." not in text:
                integer_part, separator, decimal_part = text.rpartition(",")
                if separator and integer_part and 0 < len(decimal_part) <= 2:
                    text = f"{integer_part}.{decimal_part}"
                else:
                    text = text.replace(",", "")
            else:
                text = text.replace(",", "")

            normalized = text

        try:
            number = float(normalized)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"{field_name} sayısal değil"
            ) from exc

        if not math.isfinite(number) or number <= 0:
            raise ValueError(
                f"{field_name} pozitif ve sonlu olmalı"
            )

        return number

    @classmethod
    def _request_json(
        cls,
        client: Any,
        url: str,
    ) -> dict[str, Any]:
        response = client.get(
            url,
            timeout=cls.REQUEST_TIMEOUT,
            headers={
                "User-Agent": "PROJECT-ANKA-V2/2.0",
                "Accept": "application/json",
            },
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            "",
        ).lower()

        if "json" not in content_type:
            raise ValueError(
                "Veri kaynağı JSON yanıtı vermedi"
            )

        payload = response.json()

        if not isinstance(payload, dict):
            raise ValueError(
                "Veri kaynağı geçersiz yanıt verdi"
            )

        return payload

    @classmethod
    def _load_exchange_rates(
        cls,
        client: Any,
        values: dict[str, str],
    ) -> None:
        provider = ForexProvider()
        provider.session = client

        parsed = cls._require_mapping(
            provider.fetch(),
            "Döviz sağlayıcısı yanıtı",
        )
        usdtry = cls._positive_finite_number(
            parsed.get("usdtry"),
            "USD/TRY kuru",
        )
        eurtry = cls._positive_finite_number(
            parsed.get("eurtry"),
            "EUR/TRY kuru",
        )

        values["usdtry"] = f"₺{usdtry:,.2f}"
        values["eurtry"] = f"₺{eurtry:,.2f}"

    @classmethod
    def _load_btc_price(
        cls,
        client: Any,
        values: dict[str, str],
    ) -> None:
        provider = CryptoProvider()
        provider.session = client

        parsed = cls._require_mapping(
            provider.fetch(),
            "Kripto sağlayıcısı yanıtı",
        )
        btc_price = cls._positive_finite_number(
            parsed.get("btc"),
            "BTC/USD fiyatı",
        )

        values["btc"] = f"${btc_price:,.2f}"
