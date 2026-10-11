import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from core.local_settings import load_settings
from core.offline_workbench import LocalStore
from ui.components.settings_page import SettingsPage


class SettingsUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_save_reopen_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'research.sqlite'
            page = SettingsPage(database)
            emitted = []
            page.settings_changed.connect(emitted.append)
            page.symbol.setText('US_SAMPLE')
            page.currency.setCurrentText('USD')
            page.save_button.click()
            self.assertEqual(len(emitted), 1)
            other = SettingsPage(database)
            self.assertEqual(other.symbol.text(), 'US_SAMPLE')
            self.assertEqual(other.currency.currentText(), 'USD')
            page.symbol.setText('')
            page.save_button.click()
            self.assertEqual(load_settings(page.settings_path)['default_symbol'], 'US_SAMPLE')
            self.assertIn('sembol', page.status.text())
            page.close()
            other.close()

    def test_dialog_backup_restore_and_invalid_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'research.sqlite'
            store = LocalStore(database)
            page = SettingsPage(database)
            backup = Path(directory) / 'backup.sqlite'
            try:
                store.trade('A', 'BUY', 1, 100)
                with patch('ui.components.settings_page.QFileDialog.getSaveFileName', return_value=(str(backup), '')):
                    page.backup_button.click()
                store.trade('A', 'SELL', 1, 110)
                emitted = []
                page.database_restored.connect(lambda: emitted.append(True))
                with patch('ui.components.settings_page.QFileDialog.getOpenFileName', return_value=(str(backup), '')):
                    page.restore_button.click()
                self.assertEqual(emitted, [True])
                self.assertEqual(store.portfolio({'A': 100})['cash'], 99900)
                invalid = Path(directory) / 'bad.sqlite'
                invalid.write_text('bad')
                with patch('ui.components.settings_page.QFileDialog.getOpenFileName', return_value=(str(invalid), '')):
                    page.restore_button.click()
                self.assertEqual(emitted, [True])
                self.assertEqual(store.portfolio({'A': 100})['cash'], 99900)
                self.assertIn('geçerli', page.status.text())
            finally:
                page.close()
                store.close()

    def test_cancel_and_corrupt_settings_safe_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'research.sqlite'
            (Path(directory) / 'settings.json').write_text('broken')
            page = SettingsPage(database)
            try:
                self.assertEqual(page.symbol.text(), 'DEMO1')
                self.assertIn('varsayılan', page.status.text())
                with patch('ui.components.settings_page.QFileDialog.getSaveFileName', return_value=('', '')):
                    page.backup_button.click()
                self.assertFalse(database.exists())
            finally:
                page.close()
