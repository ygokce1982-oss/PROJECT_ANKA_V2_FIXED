import json
import os
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from core.research_records import ResearchStore
from core import research_records
from ui.components.research_page import ResearchPage

NOW = datetime(2026, 10, 16, 12, tzinfo=UTC)


def record(kind='NEWS', stamp=None):
    return dict(title='Yerel örnek', kind=kind, symbol='THYAO',
                published_at=stamp or NOW.isoformat(),
                source_url='https://example.org/' + kind, summary='Yalnız test kaydı')


class PublicationAgeTests(unittest.TestCase):
    def test_exact_24_hour_and_future_boundaries(self):
        cases = [(timedelta(), 'Son 24 saat'),
                 (timedelta(hours=24, microseconds=-1), 'Son 24 saat'),
                 (timedelta(hours=24), '24 saatten eski'),
                 (timedelta(days=30), '24 saatten eski'),
                 (timedelta(microseconds=-1), 'Gelecek tarih')]
        for age, expected in cases:
            with self.subTest(age=age):
                self.assertEqual(research_records.publication_age_label((NOW-age).isoformat(), now=NOW), expected)

    def test_offset_is_same_instant(self):
        self.assertEqual(research_records.publication_age_label('2026-10-16T15:00:00+03:00', now=NOW), 'Son 24 saat')

    def test_malformed_or_naive_legacy_stamp_is_not_fresh(self):
        for value in ('bad', '', None, '2026-10-16', '2026-10-16T12:00:00', '0001-01-01T00:00:00+23:00'):
            with self.subTest(value=value):
                self.assertEqual(research_records.publication_age_label(value, now=NOW), 'Tarih geçersiz')

    def test_naive_reference_clock_is_rejected(self):
        with self.assertRaises(ValueError):
            research_records.publication_age_label(NOW.isoformat(), now=NOW.replace(tzinfo=None))


class ResearchAgeUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'research.sqlite'
        self.store = ResearchStore(self.path)
        self.now = NOW

    def page(self):
        page = ResearchPage(store_path=self.path, clock=lambda: self.now)
        self.addCleanup(page.close)
        return page

    def test_mixed_kinds_keep_source_and_local_origin_with_age(self):
        self.store.import_records([record('NEWS', (NOW-timedelta(days=3)).isoformat()), record('KAP'),
                                  record('CALENDAR', (NOW+timedelta(days=2)).isoformat())])
        page=self.page()
        rows={page.table.item(i,0).text():i for i in range(page.table.rowCount())}
        for kind, age in [('NEWS','24 saatten eski'),('KAP','Son 24 saat'),('CALENDAR','Gelecek tarih')]:
            row=rows[kind]
            self.assertEqual(page.table.item(row,7).text(),age)
            self.assertEqual(page.table.item(row,5).text(),'https://example.org/'+kind)
            self.assertEqual(page.table.item(row,6).text(),'LOCAL_IMPORT')
        self.assertIn('2026-10-16T12:00:00+00:00',page.status.text())
        self.assertIn('Canlı değil',page.status.text())

    def test_manual_refresh_updates_age_with_new_clock(self):
        self.store.import_records([record()])
        page=self.page()
        self.assertEqual(page.table.item(0,7).text(),'Son 24 saat')
        self.now += timedelta(days=1)
        page.refresh_button.click()
        self.assertEqual(page.table.item(0,7).text(),'24 saatten eski')
        self.assertIn('2026-10-17T12:00:00+00:00',page.status.text())

    def test_failed_filter_read_clears_old_rows(self):
        self.store.import_records([record()])
        page=self.page()
        self.assertEqual(page.table.rowCount(),1)
        with patch.object(ResearchStore,'query',side_effect=sqlite3.OperationalError('read failed')):
            page.kind_filter.setCurrentText('KAP')
        self.assertEqual(page.table.rowCount(),0)
        self.assertIn('Kayıtlar okunamadı',page.status.text())
        page.kind_filter.setCurrentText('NEWS')
        self.assertEqual(page.table.rowCount(),1)

    def test_successful_import_preserves_calculation_time(self):
        page=self.page()
        source=Path(self.temp.name)/'import.json'
        source.write_text(json.dumps([record()]),encoding='utf-8')
        with patch('ui.components.research_page.QFileDialog.getOpenFileName',return_value=(str(source),'JSON')):
            page.import_button.click()
        self.assertIn('1 yeni kayıt',page.status.text())
        self.assertIn('2026-10-16T12:00:00+00:00',page.status.text())
        self.assertEqual(page.table.item(0,7).text(),'Son 24 saat')

    def test_import_does_not_hide_subsequent_read_failure(self):
        page=self.page()
        source=Path(self.temp.name)/'import.json'
        source.write_text(json.dumps([record()]),encoding='utf-8')
        with patch('ui.components.research_page.QFileDialog.getOpenFileName',return_value=(str(source),'JSON')), \
             patch.object(ResearchStore,'query',side_effect=sqlite3.OperationalError('read failed')):
            page.import_button.click()
        self.assertIn('1 yeni kayıt',page.status.text())
        self.assertIn('Kayıtlar okunamadı',page.status.text())
        self.assertEqual(page.table.rowCount(),0)
        self.assertEqual(len(self.store.query()),1)

    def test_reopen_and_refresh_leave_persisted_record_unchanged(self):
        self.store.import_records([record()])
        before=self.store.query()
        page=self.page()
        page.refresh_button.click()
        page.close()
        reopened=self.page()
        self.assertEqual(reopened.table.item(0,7).text(),'Son 24 saat')
        self.assertEqual(ResearchStore(self.path).query(),before)

    def test_failed_import_retains_age_reference_without_accumulating_errors(self):
        self.store.import_records([record()])
        page=self.page()
        before=self.store.query()
        source=Path(self.temp.name)/'broken.json'
        source.write_text('invalid JSON',encoding='utf-8')
        self.now += timedelta(days=1)
        for _ in range(2):
            with patch('ui.components.research_page.QFileDialog.getOpenFileName',return_value=(str(source),'JSON')):
                page.import_button.click()
            self.assertEqual(page.table.rowCount(),1)
            self.assertEqual(page.table.item(0,7).text(),'Son 24 saat')
            self.assertIn('2026-10-16T12:00:00+00:00',page.status.text())
            self.assertIn('Kaynak güncelliği doğrulanmadı',page.status.text())
            self.assertEqual(page.status.text().count('İçe aktarma başarısız'),1)
            self.assertEqual(self.store.query(),before)
        page.refresh_button.click()
        self.assertEqual(page.table.item(0,7).text(),'24 saatten eski')
        self.assertIn('2026-10-17T12:00:00+00:00',page.status.text())
