import json
import math
import sqlite3
import tempfile
import unittest
from pathlib import Path
from core.offline_workbench import LocalStore, sample_bars


class MultiassetStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'store.sqlite'
        self.store = LocalStore(self.path)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_symbol_history_metadata_and_distinct_prices(self):
        first = self.store.execute(sample_bars(), 'A', currency='TRY')
        other = self.store.execute(sample_bars(), 'B', origin='LOCAL_CSV', currency='USD')
        self.assertEqual(self.store.latest('A')['digest'], first['digest'])
        self.assertEqual(self.store.latest()['digest'], other['digest'])
        runs = self.store.latest_by_symbol()
        self.assertEqual(set(runs), {'A', 'B'})
        self.assertEqual(runs['B']['source'], 'LOCAL_CSV')
        self.assertEqual(runs['B']['as_of'], sample_bars()[-1].time)
        self.store.trade('A', 'BUY', 2, 10)
        self.store.trade('B', 'BUY', 3, 20, fx_rates={'USD': 30})
        report = self.store.portfolio({'A': 11, 'B': 21}, fx_rates={'USD': 31})
        values = {row['symbol']: row['value'] for row in report['positions']}
        self.assertEqual(values, {'A': 22, 'B': 1953})
        self.assertEqual(report['known_equity'], 100155)

    def test_currency_conflict_never_changes_records(self):
        self.store.execute(sample_bars(), 'US', currency='USD')
        with self.assertRaises(ValueError):
            self.store.execute(sample_bars(), 'US', currency='TRY')
        with self.assertRaises(ValueError):
            self.store.trade('US', 'BUY', 1, 1, currency='EUR', fx_rates={'EUR': 30})
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM runs').fetchone()[0], 1)
        self.assertEqual(self.store.connection.execute('SELECT cash FROM account').fetchone()[0], 100000)

    def test_missing_fx_trade_rejected_and_valuation_incomplete(self):
        self.store.execute(sample_bars(), 'US', currency='USD')
        with self.assertRaises(ValueError):
            self.store.trade('US', 'BUY', 1, 10)
        self.store.trade('US', 'BUY', 1, 10, fx_rates={'USD': 30})
        result = self.store.portfolio({'US': 12})
        self.assertEqual(result['missing_fx'], ['US'])
        self.assertFalse(result['valuation_complete'])
        self.assertEqual(result['known_equity'], 99700)
        self.assertTrue(self.store.portfolio({'US': 12}, fx_rates={'USD': 31})['valuation_complete'])

    def test_bad_fx_and_overflow_trade_atomic(self):
        for rate in (0, -1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                self.store.trade('US', 'BUY', 1, 10, currency='USD', fx_rates={'USD': rate})
        with self.assertRaises(ValueError):
            self.store.trade('US', 'BUY', 1e308, 10, currency='USD', fx_rates={'USD': 30})
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM assets').fetchone()[0], 0)
        self.assertEqual(self.store.connection.execute('SELECT COUNT(*) FROM trades').fetchone()[0], 0)

    def test_reopen_preserves_currency_and_trade_conversion(self):
        self.store.trade('US', 'BUY', 2, 10, currency='USD', fx_rates={'USD': 30})
        other = LocalStore(self.path)
        try:
            with self.assertRaises(ValueError):
                other.trade('US', 'SELL', 1, 12)
            other.trade('US', 'SELL', 1, 12, fx_rates={'USD': 31})
            self.assertEqual(other.portfolio({'US': 12}, fx_rates={'USD': 31})['known_equity'], 100144)
            self.assertEqual(other.connection.execute('SELECT currency,fx_rate FROM trades ORDER BY id').fetchall(), [('USD', 30), ('USD', 31)])
        finally:
            other.close()

    def test_legacy_schema_migration_preserves_try(self):
        self.store.close()
        self.path.unlink()
        con = sqlite3.connect(self.path)
        con.executescript('CREATE TABLE account(id INTEGER PRIMARY KEY,cash REAL); INSERT INTO account VALUES(1,99000); CREATE TABLE holdings(symbol TEXT PRIMARY KEY,quantity REAL); INSERT INTO holdings VALUES("OLD",10); CREATE TABLE trades(id INTEGER PRIMARY KEY,at TEXT,symbol TEXT,side TEXT,quantity REAL,price REAL); INSERT INTO trades VALUES(1,"old","OLD","BUY",10,100);')
        con.commit()
        con.close()
        self.store = LocalStore(self.path)
        self.assertEqual(self.store.portfolio({'OLD': 110})['known_equity'], 100100)
        self.assertEqual(self.store.connection.execute('SELECT currency,fx_rate FROM trades').fetchone(), ('TRY', 1))
        with self.assertRaises(ValueError):
            self.store.execute(sample_bars(), 'OLD', currency='USD')
        self.store.trade('NEW', 'BUY', 1, 100)
        self.assertEqual(self.store.connection.execute('SELECT currency FROM assets WHERE symbol="NEW"').fetchone()[0], 'TRY')

    def test_total_overflow_is_rejected(self):
        self.store.trade('A', 'BUY', 1, 1)
        self.store.trade('B', 'BUY', 1, 1)
        with self.assertRaises(ValueError):
            self.store.portfolio({'A': 1e308, 'B': 1e308})
        with self.assertRaises(ValueError):
            self.store.portfolio({'A': 1e308, 'B': 1}, stress=1)

    def test_currency_validation_and_default_compatibility(self):
        for currency in ('', 'US', '123', 'ABCD'):
            with self.assertRaises(ValueError):
                self.store.execute(sample_bars(), currency=currency)
        self.assertEqual(self.store.execute(sample_bars(), currency='usd')['currency'], 'USD')
        self.store.trade('LEGACY', 'BUY', 1, 100)
        self.assertTrue(self.store.portfolio({'LEGACY': 100})['valuation_complete'])
