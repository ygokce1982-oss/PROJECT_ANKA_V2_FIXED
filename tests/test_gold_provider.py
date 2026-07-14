import unittest

from core.providers.gold_provider import GoldProvider


class GoldProviderTests(unittest.TestCase):
    def test_valid_gold_price(self) -> None:
        provider = GoldProvider()

        parsed = provider.parse({"gold_try": 4250.0})
        self.assertEqual(parsed, {"gold_try": 4250.0})
        self.assertTrue(provider.validate(parsed))
        self.assertEqual(provider.format(parsed), {"gold": "₺4,250.00"})

    def test_missing_data_raises_value_error(self) -> None:
        provider = GoldProvider()

        with self.assertRaises(ValueError):
            provider.parse({})

    def test_zero_or_negative_price_invalid(self) -> None:
        provider = GoldProvider()

        parsed_zero = {"gold_try": 0.0}
        parsed_negative = {"gold_try": -1.0}

        self.assertFalse(provider.validate(parsed_zero))
        self.assertFalse(provider.validate(parsed_negative))

    def test_fetch_raises_not_implemented_error(self) -> None:
        provider = GoldProvider()

        with self.assertRaises(NotImplementedError) as cm:
            provider.fetch()

        self.assertIn(
            "Onaylanmış altın veri kaynağı henüz yapılandırılmadı",
            str(cm.exception),
        )


if __name__ == "__main__":
    unittest.main()
