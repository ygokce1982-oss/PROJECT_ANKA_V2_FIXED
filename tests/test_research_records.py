import json
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from core.research_records import MAX_IMPORT_BYTES, ResearchStore


def record(**changes):
    return dict(
        title="Kaynak duyurusu",
        kind="KAP",
        published_at="2026-10-10T12:00:00+03:00",
        source_url="https://example.org/announcement",
        symbol="THYAO",
        summary="Yerel özet",
        **changes,
    )


class ResearchRecordTests(unittest.TestCase):
    def test_turkish_unicode_search_after_reopen(self):
        item = record()
        item.update(title="Şirket Özet İŞLEM", summary="IŞIK ve GÜNCEL")
        self.store.import_records([item])
        reopened = ResearchStore(self.path)
        for query in ("şirket özet", "işlem", "ışık", "güncel", "S\u0327irket O\u0308zet"):
            with self.subTest(query=query):
                self.assertEqual(len(reopened.query(text=query)), 1)
        self.assertEqual(reopened.query(text="işık"), [])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "research.sqlite"
        self.store = ResearchStore(self.path)

    def test_invalid_source_time_and_batch_atomicity(self):
        for field, value in (
            ("source_url", "file:///secret"),
            ("source_url", "javascript:alert(1)"),
            ("source_url", "https://user:pass@example.org"),
            ("published_at", "2026-10-10"),
            ("published_at", "bad"),
            ("kind", "LIVE"),
        ):
            bad = record()
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.store.import_records([record(), bad])
            self.assertEqual(self.store.query(), [])

    def test_duplicate_identity_timezone_and_reopened_search(self):
        first = record()
        second = dict(first, published_at="2026-10-10T09:00:00Z")
        result = self.store.import_records([first, second])
        self.assertEqual((result["inserted"], result["duplicates"]), (1, 1))
        self.assertEqual(self.store.import_records([first])["inserted"], 0)
        reopened = ResearchStore(self.path)
        rows = reopened.query(kind="KAP", symbol="thyao", text="duyuru")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["origin"], "LOCAL_IMPORT")
        self.assertFalse(rows[0]["live"])
        self.assertEqual(reopened.query(kind="NEWS"), [])
        self.assertEqual(reopened.query(text="%"), [])

    def test_database_failure_rolls_back_complete_batch(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.execute("""CREATE TRIGGER reject_bad BEFORE INSERT ON research_records
                WHEN NEW.title='reject' BEGIN SELECT RAISE(ABORT,'rejected'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.import_records(
                [record(), dict(record(), title="reject", source_url="https://example.org/2")]
            )
        self.assertEqual(self.store.query(), [])

    def test_bounded_json_import_and_limit(self):
        source = Path(self.directory.name) / "import.json"
        source.write_text(json.dumps([record()]), encoding="utf-8")
        self.assertEqual(self.store.import_json(source)["inserted"], 1)
        source.write_bytes(b" " * (MAX_IMPORT_BYTES + 1))
        with self.assertRaises(ValueError):
            self.store.import_json(source)
        with self.assertRaises(ValueError):
            self.store.query(limit=1001)
