import unittest
from unittest.mock import patch

import requests

from core.market_data import MarketData
from core.providers.crypto_provider import CryptoProvider
from core.providers.forex_provider import ForexProvider


class StubResponse:
    def __init__(
        self,
        payload: object,
        headers: dict | None = None,
    ) -> None:
        self.payload = payload
        self.headers = headers or {
            "Content-Type": "application/json"
        }

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class StubSession:
    def __init__(
        self,
        responses: dict[str, object],
    ) -> None:
        self.responses = responses
        self.calls: list[
            tuple[str, dict[str, object]]
        ] = []

    def get(
        self,
        url: str,
        **kwargs: object,
    ) -> StubResponse:
        self.calls.append((url, kwargs))
        response = self.responses[url]

        if isinstance(response, Exception):
            raise response

        if not isinstance(response, StubResponse):
            raise TypeError(
                "Geçersiz test yanıtı"
            )

        return response


class MarketDataTests(unittest.TestCase):
    def test_successful_snapshot_formats_values(
        self,
    ) -> None:
        session = StubSession(
            {
                MarketData.EXCHANGE_RATES_URL: StubResponse(
                    {
                        "result": "success",
                        "rates": {
                            "TRY": 40.0,
                            "EUR": 0.8,
                        },
                    }
                ),
                MarketData.BTC_SPOT_URL: StubResponse(
                    {
                        "bitcoin": {
                            "usd": 62500.50
                        }
                    }
                ),
            }
        )

        snapshot = MarketData.get_snapshot(
            session=session
        )

        self.assertEqual(
            snapshot.values["usdtry"],
            "₺40.00",
        )
        self.assertEqual(
            snapshot.values["eurtry"],
            "₺50.00",
        )
        self.assertEqual(
            snapshot.values["btc"],
            "$62,500.50",
        )
        self.assertEqual(snapshot.errors, ())
        self.assertEqual(len(session.calls), 2)

    def test_source_failures_keep_safe_placeholders(
        self,
    ) -> None:
        session = StubSession(
            {
                MarketData.EXCHANGE_RATES_URL: (
                    requests.ConnectionError(
                        "offline"
                    )
                ),
                MarketData.BTC_SPOT_URL: (
                    requests.Timeout(
                        "timeout"
                    )
                ),
            }
        )

        snapshot = MarketData.get_snapshot(
            session=session
        )

        self.assertEqual(
            snapshot.values["usdtry"],
            "---",
        )
        self.assertEqual(
            snapshot.values["eurtry"],
            "---",
        )
        self.assertEqual(
            snapshot.values["btc"],
            "---",
        )
        self.assertEqual(len(snapshot.errors), 2)

    def test_invalid_exchange_payload_is_reported(
        self,
    ) -> None:
        session = StubSession(
            {
                MarketData.EXCHANGE_RATES_URL: StubResponse(
                    {"result": "error"}
                ),
                MarketData.BTC_SPOT_URL: StubResponse(
                    {
                        "bitcoin": {
                            "usd": 62000
                        }
                    }
                ),
            }
        )

        snapshot = MarketData.get_snapshot(
            session=session
        )

        self.assertEqual(
            snapshot.values["usdtry"],
            "---",
        )
        self.assertEqual(
            snapshot.values["btc"],
            "$62,000.00",
        )
        self.assertEqual(
            snapshot.errors,
            ("Döviz verisi alınamadı",),
        )

    def test_non_finite_exchange_value_is_rejected(
        self,
    ) -> None:
        with (
            patch.object(
                ForexProvider,
                "fetch",
                return_value={
                    "usdtry": float("nan"),
                    "eurtry": 50.0,
                },
            ),
            patch.object(
                CryptoProvider,
                "fetch",
                return_value={
                    "btc": "$62,500.50"
                },
            ),
        ):
            snapshot = MarketData.get_snapshot(
                session=object()
            )

        self.assertEqual(
            snapshot.values["usdtry"],
            "---",
        )
        self.assertEqual(
            snapshot.values["eurtry"],
            "---",
        )
        self.assertEqual(
            snapshot.values["btc"],
            "$62,500.50",
        )
        self.assertEqual(
            snapshot.errors,
            ("Döviz verisi alınamadı",),
        )

    def test_zero_btc_value_is_rejected(
        self,
    ) -> None:
        with (
            patch.object(
                ForexProvider,
                "fetch",
                return_value={
                    "usdtry": 40.0,
                    "eurtry": 50.0,
                },
            ),
            patch.object(
                CryptoProvider,
                "fetch",
                return_value={"btc": 0},
            ),
        ):
            snapshot = MarketData.get_snapshot(
                session=object()
            )

        self.assertEqual(
            snapshot.values["usdtry"],
            "₺40.00",
        )
        self.assertEqual(
            snapshot.values["eurtry"],
            "₺50.00",
        )
        self.assertEqual(
            snapshot.values["btc"],
            "---",
        )
        self.assertEqual(
            snapshot.errors,
            ("BTC verisi alınamadı",),
        )

    def test_provider_response_must_be_mapping(
        self,
    ) -> None:
        with (
            patch.object(
                ForexProvider,
                "fetch",
                return_value=[],
            ),
            patch.object(
                CryptoProvider,
                "fetch",
                return_value={"btc": 62000},
            ),
        ):
            snapshot = MarketData.get_snapshot(
                session=object()
            )

        self.assertEqual(
            snapshot.values["usdtry"],
            "---",
        )
        self.assertEqual(
            snapshot.values["btc"],
            "$62,000.00",
        )
        self.assertEqual(
            snapshot.errors,
            ("Döviz verisi alınamadı",),
        )

    def test_formatted_numeric_strings_are_supported(
        self,
    ) -> None:
        self.assertEqual(
            MarketData._positive_finite_number(
                "$62,500.50",
                "BTC",
            ),
            62500.50,
        )
        self.assertEqual(
            MarketData._positive_finite_number(
                "40,50",
                "Kur",
            ),
            40.50,
        )


class ForexProviderTests(unittest.TestCase):
    def test_forex_provider_parses_rates_without_network(
        self,
    ) -> None:
        session = StubSession(
            {
                ForexProvider.EXCHANGE_RATES_URL: StubResponse(
                    {
                        "result": "success",
                        "rates": {
                            "TRY": 35.0,
                            "EUR": 0.7,
                        },
                    }
                )
            }
        )

        provider = ForexProvider()
        provider.session = session

        parsed = provider.fetch()

        self.assertAlmostEqual(
            parsed["usdtry"],
            35.0,
        )
        self.assertAlmostEqual(
            parsed["eurtry"],
            35.0 / 0.7,
        )


if __name__ == "__main__":
    unittest.main()
