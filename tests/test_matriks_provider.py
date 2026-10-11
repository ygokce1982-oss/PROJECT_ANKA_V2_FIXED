"""Offline contract tests for the Matriks read-only API adapter."""

import unittest
from unittest.mock import Mock

from core.providers.matriks_provider import MatriksConfigurationError, MatriksProvider


class MatriksProviderTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.response = Mock()
        self.response.json.return_value = [
            {
                "time": 1628542800000,
                "open": 9.12,
                "high": 9.21,
                "low": 9.04,
                "close": 9.11,
                "totalQuantity": 168545356,
                "volume": 1538559735.08,
            }
        ]
        self.session.get.return_value = self.response
        self.client = MatriksProvider(
            token="offline-fake-token", issuer="TEST", session=self.session
        )

    def test_authenticated_bar_request_uses_documented_endpoint(self):
        bars = self.client.fetch_bars(
            symbol="GARAN", start="2021-08-10", end="2021-08-12", period="1day"
        )
        self.assertEqual(len(bars), 1)
        self.assertEqual(bars[0]["volume"], 168545356)
        self.assertEqual(bars[0]["turnover"], 1538559735.08)
        self.session.get.assert_called_once_with(
            MatriksProvider.BAR_URL,
            params={
                "symbol": "GARAN",
                "start": "2021-08-10",
                "end": "2021-08-12",
                "period": "1day",
            },
            headers={"Authorization": "jwt offline-fake-token", "Accept": "application/json"},
            timeout=10.0,
        )

    def test_missing_token_fails_before_network(self):
        client = MatriksProvider(token="", session=self.session)
        with self.assertRaises(MatriksConfigurationError):
            client.fetch_bars(symbol="GARAN", start="2021-08-10", end="2021-08-12")
        self.session.get.assert_not_called()

    def test_invalid_query_never_hits_network(self):
        for symbol in ("GARAN&x=1", "gar an", ""):
            with self.assertRaises(ValueError):
                self.client.fetch_bars(symbol=symbol, start="2021-08-10", end="2021-08-12")
        with self.assertRaises(ValueError):
            self.client.fetch_bars(symbol="GARAN", start="2021-08-12", end="2021-08-10")
        with self.assertRaises(ValueError):
            self.client.fetch_bars(
                symbol="GARAN", start="2021-08-10", end="2021-08-12", period="2min"
            )
        self.session.get.assert_not_called()

    def test_discovery_does_not_send_token(self):
        self.response.json.return_value = {"rest": {}, "mqtt": {}}
        self.assertIn("rest", self.client.discover())
        self.session.get.assert_called_once_with(
            MatriksProvider.DISCOVERY_URL,
            params={"issuer": "TEST"},
            timeout=10.0,
        )

    def test_discovery_requires_issuer(self):
        client = MatriksProvider(token="fake", issuer="", session=self.session)
        with self.assertRaises(MatriksConfigurationError):
            client.discover()
        self.session.get.assert_not_called()

    def test_rejects_inconsistent_or_nonfinite_bars(self):
        valid = self.client.parse(self.response.json(), symbol="GARAN")
        self.assertTrue(self.client.validate(valid))
        valid[0]["high"] = 1.0
        self.assertFalse(self.client.validate(valid))
        valid[0]["high"] = float("nan")
        self.assertFalse(self.client.validate(valid))

    def test_rejects_duplicate_or_out_of_order_timestamps(self):
        bar = self.client.parse(self.response.json(), symbol="GARAN")[0]
        self.assertFalse(self.client.validate([bar, dict(bar)]))
        older = dict(bar, timestamp_ms=bar["timestamp_ms"] - 1)
        self.assertFalse(self.client.validate([bar, older]))

    def test_default_fetch_requires_parameters(self):
        with self.assertRaises(MatriksConfigurationError):
            self.client.fetch()
        self.session.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
