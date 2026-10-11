"""Contract tests for the public ANKA operation journal."""
import tempfile
from pathlib import Path
import unittest

from scripts.record_operation import append_event, verify


class JournalContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "events.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def append(self, **kwargs):
        params = dict(
            actor="researcher", action="read-only architecture inspection",
            status="PASS", evidence="unit test: evidence-1",
            next_step="continue test", rollback="no changes",
            source="offline-test", journal=self.path,
        )
        params.update(kwargs)
        return append_event(**params)

    def test_append_and_verify(self):
        self.append()
        self.assertEqual(verify(self.path), 1)

    def test_append_two_preserves_history(self):
        self.append()
        self.append(actor="reviewer", status="BLOCKED")
        self.assertEqual(verify(self.path), 2)

    def test_secret_rejected_without_write(self):
        with self.assertRaises(ValueError):
            self.append(evidence="password=not-allowed")
        self.assertFalse(self.path.exists())

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            self.append(status="COMPLETED")
        self.assertFalse(self.path.exists())

    def test_newline_rejected(self):
        with self.assertRaises(ValueError):
            self.append(action="first line\nunsafe")
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
