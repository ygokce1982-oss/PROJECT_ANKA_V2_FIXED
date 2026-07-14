import unittest

import requests

from core.providers.crypto_provider import CryptoProvider


class StubResponse:
    def __init__(self, payload: object, headers: dict | None = None) -> None:
        self.payload = payload
        self.headers = headers or {"Content-Type": "application/json"}

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class StubSession:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses

    def get(self, url: str, **kwargs: object) -> StubResponse:
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, StubResponse):
            raise TypeError("Geçersiz test yanıtı")
        return response


class CryptoProviderTests(unittest.TestCase):
    def test_coingecko_success(self) -> None:
        session = StubSession(
            {
                CryptoProvider.COINGECKO_BTC_URL: StubResponse(
                    {"bitcoin": {"usd": 62000.0}}
                )
            }
        )

        provider = CryptoProvider()
        provider.session = session

        result = provider.fetch()

        self.assertEqual(result, {"btc": "$62,000.00"})

    def test_coingecko_fails_binance_success(self) -> None:
        session = StubSession(
            {
                CryptoProvider.COINGECKO_BTC_URL: requests.Timeout("timeout"),
                CryptoProvider.BINANCE_BTC_URL: StubResponse({"price": "62000.00"}),
            }
        )

        provider = CryptoProvider()
        provider.session = session

        result = provider.fetch()

        self.assertEqual(result, {"btc": "$62,000.00"})

    def test_both_sources_fail(self) -> None:
        session = StubSession(
            {
                CryptoProvider.COINGECKO_BTC_URL: requests.Timeout("timeout"),
                CryptoProvider.BINANCE_BTC_URL: requests.ConnectionError("offline"),
            }
        )

        provider = CryptoProvider()
        provider.session = session

        with self.assertRaises(RuntimeError) as cm:
            provider.fetch()

        self.assertIn("CoinGecko:", str(cm.exception))
        self.assertIn("Binance:", str(cm.exception))

    def test_invalid_or_negative_price(self) -> None:
        session = StubSession(
            {
                CryptoProvider.COINGECKO_BTC_URL: StubResponse(
                    {"bitcoin": {"usd": -100.0}}
                ),
                CryptoProvider.BINANCE_BTC_URL: StubResponse({"price": "-100.00"}),
            }
        )

        provider = CryptoProvider()
        provider.session = session

        with self.assertRaises(RuntimeError) as cm:
            provider.fetch()

        self.assertIn("CoinGecko:", str(cm.exception))
        self.assertIn("Binance:", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
