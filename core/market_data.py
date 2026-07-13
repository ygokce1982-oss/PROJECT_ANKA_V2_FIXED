"""PROJECT ANKA piyasa veri işlemleri."""

import logging
from dataclasses import dataclass
from typing import Any

import requests


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
        payload = cls._request_json(
            client,
            cls.EXCHANGE_RATES_URL,
        )

        if payload.get("result") != "success":
            raise ValueError(
                "Döviz servisi başarısız sonuç döndürdü"
            )

        rates = payload["rates"]

        usdtry = float(rates["TRY"])
        usdeur = float(rates["EUR"])

        if usdeur <= 0:
            raise ValueError("Geçersiz EUR kuru")

        values["usdtry"] = f"₺{usdtry:,.2f}"
        values["eurtry"] = f"₺{usdtry / usdeur:,.2f}"

    @classmethod
    def _load_btc_price(
        cls,
        client: Any,
        values: dict[str, str],
    ) -> None:
        source_errors: list[str] = []

        try:
            payload = cls._request_json(
                client,
                cls.COINGECKO_BTC_URL,
            )

            bitcoin = payload.get("bitcoin", {})
            amount = float(bitcoin["usd"])

            values["btc"] = f"${amount:,.2f}"
            return

        except Exception as exc:
            source_errors.append(
                f"CoinGecko: {exc}"
            )
            LOGGER.info(
                "CoinGecko kullanılamadı: %s",
                exc,
            )

        try:
            payload = cls._request_json(
                client,
                cls.BINANCE_BTC_URL,
            )

            amount = float(payload["price"])

            values["btc"] = f"${amount:,.2f}"
            return

        except Exception as exc:
            source_errors.append(
                f"Binance: {exc}"
            )
            LOGGER.info(
                "Binance kullanılamadı: %s",
                exc,
            )

        raise RuntimeError(
            " | ".join(source_errors)
        )