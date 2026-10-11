import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication

from ui.components.research_page import ResearchPage


class ResearchUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_import_source_filter_and_visible_error(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("socket.socket.connect", side_effect=AssertionError("NETWORK_FORBIDDEN")),
        ):
            source = Path(directory) / "news.json"
            source.write_text(
                json.dumps(
                    [
                        dict(
                            title="Şirket Özet İŞLEM",
                            kind="NEWS",
                            symbol="THYAO",
                            published_at="2026-10-10T12:00:00+03:00",
                            source_url="https://example.org/news",
                            summary="Özet",
                        )
                    ]
                ),
                encoding="utf-8",
            )
            page = ResearchPage("NEWS", Path(directory) / "research.sqlite")
            try:
                with patch(
                    "ui.components.research_page.QFileDialog.getOpenFileName",
                    return_value=(str(source), "JSON"),
                ):
                    page.import_button.click()
                self.assertEqual(page.table.rowCount(), 1)
                self.assertEqual(page.table.item(0, 5).text(), "https://example.org/news")
                self.assertEqual(page.table.item(0, 6).text(), "LOCAL_IMPORT")
                self.assertIn("+00:00", page.table.item(0, 2).text())
                self.assertIn("Canlı değil", page.status.text())
                page.search.setText("şirket özet")
                self.assertEqual(page.table.rowCount(), 1)
                page.search.setText("işlem")
                self.assertEqual(page.table.rowCount(), 1)
                page.search.setText("özet")
                self.assertEqual(page.table.rowCount(), 1)
                page.search.setText("missing")
                self.assertEqual(page.table.rowCount(), 0)
                page.search.clear()
                page.kind_filter.setCurrentText("KAP")
                self.assertEqual(page.table.rowCount(), 0)
                source.write_text("invalid", encoding="utf-8")
                with patch(
                    "ui.components.research_page.QFileDialog.getOpenFileName",
                    return_value=(str(source), "JSON"),
                ):
                    page.import_button.click()
                self.assertIn("başarısız", page.status.text())
            finally:
                page.close()
