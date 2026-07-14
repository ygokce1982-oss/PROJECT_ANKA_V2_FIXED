"""Kripto para verisi sağlayıcısı için iskelet modül."""

from typing import Any, Dict

import requests

from .base_provider import BaseProvider


class CryptoProvider(BaseProvider):
    """Kripto para fiyatlarını ve piyasa bilgisini getiren sağlayıcı sınıfı."""

    COINGECKO_BTC_URL = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin&vs_currencies=usd"
    )
    BINANCE_BTC_URL = (
        "https://data-api.binance.vision/api/v3/ticker/price"
        "?symbol=BTCUSDT"
    )
    REQUEST_TIMEOUT = 8

    def __init__(self) -> None:
        self.session: requests.Session | None = None

    def connect(self) -> None:
        """İsteğe bağlı kalıcı `requests.Session` sağlar."""
        if self.session is None:
            self.session = requests.Session()

    def fetch(self) -> Dict[str, str]:
        """Kripto fiyatı almak için CoinGecko, sonra Binance'e düşen akış."""
        self.connect()
        assert self.session is not None

        errors: list[str] = []

        try:
            payload = self._request_json(self.session, self.COINGECKO_BTC_URL)
            parsed = self.parse(payload, source="CoinGecko")
            if self.validate(parsed):
                return parsed
            raise ValueError("Geçersiz CoinGecko fiyatı")
        except Exception as exc:
            errors.append(f"CoinGecko: {exc}")

        try:
            payload = self._request_json(self.session, self.BINANCE_BTC_URL)
            parsed = self.parse(payload, source="Binance")
            if self.validate(parsed):
                return parsed
            raise ValueError("Geçersiz Binance fiyatı")
        except Exception as exc:
            errors.append(f"Binance: {exc}")

        raise RuntimeError(" | ".join(errors))

    def _request_json(self, client: Any, url: str) -> dict[str, Any]:
        response = client.get(
            url,
            timeout=self.REQUEST_TIMEOUT,
            headers={
                "User-Agent": "PROJECT-ANKA-V2/2.0",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").lower()
        if "json" not in content_type:
            raise ValueError("Veri kaynağı JSON yanıtı vermedi")

        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Veri kaynağı geçersiz yanıt verdi")

        return payload

    def parse(self, raw_data: Any, source: str) -> Dict[str, str]:
        """Ham kaynaktan `btc` anahtarını döndürecek biçime dönüştürür."""
        if not isinstance(raw_data, dict):
            raise TypeError("Beklenmeyen payload tipi")

        if source == "CoinGecko":
            bitcoin = raw_data.get("bitcoin", {})
            price = float(bitcoin["usd"])
        else:
            price = float(raw_data["price"])

        formatted = f"${price:,.2f}"
        return {"btc": formatted}

    def validate(self, parsed_data: Any) -> bool:
        """Pozitif BTC fiyatını doğrular."""
        try:
            btc_value = parsed_data["btc"]
            if not isinstance(btc_value, str) or not btc_value.startswith("$"):
                return False
            numeric = float(btc_value.replace("$", "").replace(",", ""))
            return numeric > 0
        except Exception:
            return False
