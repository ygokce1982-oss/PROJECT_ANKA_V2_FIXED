import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from core.local_settings import DEFAULT_SETTINGS, load_settings, save_settings, backup_database, restore_database
from core.offline_workbench import LocalStore, sample_bars


class LocalSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.database = self.root / 'research.sqlite'
        self.store = LocalStore(self.database)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_settings_default_persist_and_invalid_preserves_file(self):
        path = self.root / 'settings.json'
        self.assertEqual(load_settings(path), DEFAULT_SETTINGS)
        save_settings(path, {'default_symbol': ' GOLD ', 'default_currency': 'USD'})
        self.assertEqual(load_settings(path), {'default_symbol': 'GOLD', 'default_currency': 'USD'})
        before = path.read_bytes()
        for bad in ({'default_symbol': '', 'default_currency': 'TRY'}, {'default_symbol': 'A', 'default_currency': 'JPY'}, {'default_symbol': 'A', 'default_currency': 'TRY', 'api_key': 'x'}):
            with self.assertRaises(ValueError):
                save_settings(path, bad)
            self.assertEqual(path.read_bytes(), before)
        self.assertEqual(len(list(self.root.glob('settings.json.*'))), 0)

    def test_malformed_settings_rejected(self):
        path = self.root / 'settings.json'
        path.write_text('broken')
        with self.assertRaises(ValueError):
            load_settings(path)

    def test_wal_backup_restore_open_and_reopen(self):
        self.store.execute(sample_bars())
        self.store.trade('DEMO1', 'BUY', 2, 100)
        self.store.add_alert('DEMO1', 120, 100)
        backup = self.root / 'saved.sqlite'
        backup_database(self.database, backup)
        self.store.trade('DEMO1', 'SELL', 1, 110)
        restore_database(self.database, backup)
        self.assertEqual(self.store.portfolio({'DEMO1': 100})['cash'], 99800)
        other = LocalStore(self.database)
        try:
            self.assertEqual(other.portfolio({'DEMO1': 100})['cash'], 99800)
            self.assertIsNotNone(other.latest())
            self.assertEqual(other.connection.execute('SELECT COUNT(*) FROM alerts').fetchone()[0], 1)
        finally:
            other.close()

    def test_invalid_restore_preserves_existing_state_and_bytes(self):
        self.store.trade('A', 'BUY', 1, 50)
        text = self.root / 'text.sqlite'
        text.write_text('not sqlite')
        incomplete = self.root / 'wrong.sqlite'
        with closing(sqlite3.connect(incomplete)) as connection:
            connection.execute('CREATE TABLE foo(x)')
            connection.commit()
        before = self.database.read_bytes()
        for source in (text, incomplete, self.root / 'missing.sqlite'):
            with self.assertRaises(ValueError):
                restore_database(self.database, source)
            self.assertEqual(self.database.read_bytes(), before)
            self.assertEqual(self.store.portfolio({'A': 50})['cash'], 99950)

    def test_invalid_backup_preserves_destination(self):
        dest = self.root / 'saved.sqlite'
        dest.write_bytes(b'existing')
        with self.assertRaises(ValueError):
            backup_database(self.root / 'missing.sqlite', dest)
        self.assertEqual(dest.read_bytes(), b'existing')
        with self.assertRaises(ValueError):
            backup_database(self.database, self.database)
        with self.assertRaises(ValueError):
            restore_database(self.database, self.database)

    def test_bad_account_backup_rejected_without_target_creation(self):
        source = self.root / 'invalid.sqlite'
        backup_database(self.database, source)
        with closing(sqlite3.connect(source)) as connection:
            connection.execute('DELETE FROM account')
            connection.commit()
        new_target = self.root / 'new.sqlite'
        with self.assertRaises(ValueError):
            restore_database(new_target, source)
        self.assertFalse(new_target.exists())
