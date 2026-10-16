"""Local NEWS/KAP/CALENDAR import and searchable provenance display."""

import sqlite3
from datetime import UTC, datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.research_records import KINDS, ResearchStore, publication_age_label
from ui.components.local_workbench import state_path


class ResearchPage(QWidget):
    def __init__(self, kind=None, store_path=None, *, clock=None):
        super().__init__()
        if kind is not None and kind not in KINDS:
            raise ValueError("Geçersiz araştırma türü")
        self.store_path = store_path or state_path()
        self._clock = clock or (lambda: datetime.now(UTC))
        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "Yerel araştırma · LOCAL_IMPORT · Canlı akış değil · "
                "Kaynak doğruluğu içe aktaran kişiye aittir"
            )
        )
        actions = QHBoxLayout()
        self.import_button = QPushButton("JSON içe aktar (en fazla 2 MB)")
        self.import_button.clicked.connect(self.import_json)
        self.refresh_button = QPushButton("Yerel kayıtları yenile")
        self.refresh_button.clicked.connect(self.refresh)
        self.kind_filter = QComboBox()
        self.kind_filter.addItems(["Tümü", *KINDS])
        if kind:
            self.kind_filter.setCurrentText(kind)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Başlık / özet ara")
        self.symbol = QLineEdit()
        self.symbol.setPlaceholderText("Sembol (isteğe bağlı)")
        for widget in (self.import_button, self.refresh_button, self.kind_filter, self.symbol, self.search):
            actions.addWidget(widget)
        layout.addLayout(actions)
        self.status = QLabel()
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["Tür", "Sembol", "Tarih (UTC)", "Başlık", "Özet", "Kaynak URL", "Köken", "Yayın yaşı"]
        )
        self.table.horizontalHeaderItem(7).setToolTip(
            "İçe aktarılan published_at tarihine göre son hesaplama. 24 saat yalnız gösterim eşiğidir. "
            "Kaynağın güncelliğini veya takvim etkinliği zamanını doğrulamaz."
        )
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)
        self.kind_filter.currentTextChanged.connect(self.refresh)
        self.symbol.textChanged.connect(self.refresh)
        self.search.textChanged.connect(self.refresh)
        self.refresh()

    def refresh(self):
        try:
            now = self._clock()
            publication_age_label("", now=now)  # Validate the reference even for an empty result.
            kind = self.kind_filter.currentText()
            rows = ResearchStore(self.store_path).query(
                kind=None if kind == "Tümü" else kind,
                symbol=self.symbol.text(),
                text=self.search.text(),
            )
            self.table.setRowCount(len(rows))
            for index, record in enumerate(rows):
                for column, key in enumerate(
                    ("kind", "symbol", "published_at", "title", "summary", "source_url", "origin")
                ):
                    item = QTableWidgetItem(record[key])
                    item.setToolTip(record[key])
                    self.table.setItem(index, column, item)
                age_item = QTableWidgetItem(publication_age_label(record["published_at"], now=now))
                age_item.setToolTip(self.table.horizontalHeaderItem(7).toolTip())
                self.table.setItem(index, 7, age_item)
            self.status.setText(
                f"{len(rows)} yerel kayıt gösteriliyor (en fazla 200) · LOCAL_IMPORT · Canlı değil\n"
                f"Yaş hesabı (UTC): {now.astimezone(UTC).isoformat(timespec='seconds')} · "
                "Kaynak güncelliği doğrulanmadı; yenileme yerel kayıtları okur."
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            self.table.setRowCount(0)
            self.status.setText(f"Kayıtlar okunamadı: {error} · LOCAL_IMPORT · Canlı değil")
        self._view_status = self.status.text()

    def import_json(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Yerel kaynak kayıtlarını içe aktar", "", "JSON (*.json)"
        )
        if not path:
            return
        try:
            result = ResearchStore(self.store_path).import_json(path)
            self.refresh()
            self.status.setText(
                f"{result['inserted']} yeni kayıt; {result['duplicates']} yinelenen kayıt\n"
                + self._view_status
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            self.status.setText(f"İçe aktarma başarısız: {error}\n{self._view_status}")
