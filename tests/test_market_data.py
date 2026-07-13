import unittest

import requests

from core.market_data import MarketData


class StubResponse:
    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self.payload


class StubSession:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, object]]] = []

    def get(self, url: str, **kwargs: object) -> StubResponse:
        self.calls.append((url, kwargs))
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        if not isinstance(response, StubResponse):
            raise TypeError("Geçersiz test yanıtı")
        return response


class MarketDataTests(unittest.TestCase):
    def test_successful_snapshot_formats_values(self) -> None:
        session = StubSession(
            {
                MarketData.EXCHANGE_RATES_URL: StubResponse(
                    {"result": "success", "rates": {"TRY": 40.0, "EUR": 0.8}}
                ),
                MarketData.BTC_SPOT_URL: StubResponse({"data": {"amount": "62500.50"}}),
            }
        )

        snapshot = MarketData.get_snapshot(session=session)

        self.assertEqual(snapshot.values["usdtry"], "₺40.00")
        self.assertEqual(snapshot.values["eurtry"], "₺50.00")
        self.assertEqual(snapshot.values["btc"], "$62,500.50")
        self.assertEqual(snapshot.errors, ())
        self.assertEqual(len(session.calls), 2)

    def test_source_failures_keep_safe_placeholders(self) -> None:
        session = StubSession(
            {
                MarketData.EXCHANGE_RATES_URL: requests.ConnectionError("offline"),
                MarketData.BTC_SPOT_URL: requests.Timeout("timeout"),
            }
        )

        snapshot = MarketData.get_snapshot(session=session)

        self.assertEqual(snapshot.values["usdtry"], "---")
        self.assertEqual(snapshot.values["eurtry"], "---")
        self.assertEqual(snapshot.values["btc"], "---")
        self.assertEqual(len(snapshot.errors), 2)

    def test_invalid_exchange_payload_is_reported(self) -> None:
        session = StubSession(
            {
                MarketData.EXCHANGE_RATES_URL: StubResponse({"result": "error"}),
                MarketData.BTC_SPOT_URL: StubResponse({"data": {"amount": "62000"}}),
            }
        )

        snapshot = MarketData.get_snapshot(session=session)

        self.assertEqual(snapshot.values["usdtry"], "---")
        self.assertEqual(snapshot.values["btc"], "$62,000.00")
        self.assertEqual(snapshot.errors, ("Döviz verisi alınamadı",))


if __name__ == "__main__":
    unittest.main()
