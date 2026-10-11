"""Acceptance for strict local CSV entry, no network or live-data claim."""
from pathlib import Path
import tempfile
import unittest
from core.multi_asset_csv import load_price_csv


class MultiAssetCsvTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.path=Path(self.folder.name)/"prices.csv"

    def tearDown(self):
        self.folder.cleanup()

    def write(self,body):
        self.path.write_text("symbol,date,close,currency\n"+body,encoding="utf-8")

    def test_import_and_provenance(self):
        self.write("SP500,2025-01-02,100,USD\nSP500,2025-01-03,101,USD\n"
                   "GOLD,2025-01-02,200,USD\nGOLD,2025-01-03,202,USD\n")
        assets=load_price_csv(self.path)
        self.assertEqual({h.symbol for h in assets},{"SP500","GOLD"})
        self.assertTrue(all(h.demo is False for h in assets))
        self.assertTrue(all("DOĞRULANMADI" in h.source for h in assets))
        self.assertTrue(all(h.asof_utc for h in assets))

    def test_currency_mismatch_fails(self):
        self.write("SP500,2025-01-02,100,USD\nSP500,2025-01-03,101,USD\n"
                   "BIST,2025-01-02,100,TRY\nBIST,2025-01-03,101,TRY\n")
        with self.assertRaisesRegex(ValueError,"MIXED_CURRENCY"):
            load_price_csv(self.path)

    def test_empty_bad_or_only_one_series_rejected(self):
        for body in ("", "SP500,2025-01-02,100,USD\n",
                     "SP500,2025-01-02,nan,USD\nGOLD,2025-01-02,100,USD\n",
                     "SP500,2025-01-02,100,USD\nGOLD,2025-01-04,100,USD\n"):
            with self.subTest(body=body):
                self.write(body)
                with self.assertRaises(ValueError):
                    load_price_csv(self.path)

    def test_duplicate_date_and_changed_currency_rejected(self):
        for body in ("SP500,2025-01-02,100,USD\nSP500,2025-01-02,102,USD\nGOLD,2025-01-02,100,USD\n",
                     "SP500,2025-01-02,100,USD\nSP500,2025-01-03,101,TRY\nGOLD,2025-01-02,100,USD\n"):
            with self.subTest(body=body):
                self.write(body)
                with self.assertRaises(ValueError):
                    load_price_csv(self.path)

    def test_invalid_csv_header_rejected(self):
        self.path.write_text("symbol,date,price,currency\nA,2025-01-01,100,USD\n",encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"REQUIRED_COLUMNS"):
            load_price_csv(self.path)


if __name__ == "__main__":
    unittest.main()
