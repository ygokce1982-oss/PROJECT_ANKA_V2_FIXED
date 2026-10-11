"""Editable local settings and explicit SQLite backup/restore controls."""

import sqlite3
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core import local_settings
from ui.components.local_workbench import state_path


class SettingsPage(QWidget):
    settings_changed = Signal(dict)
    database_restored = Signal()

    def __init__(self, database_path: Path | None = None):
        super().__init__()
        self.database_path = Path(database_path) if database_path is not None else state_path()
        self.settings_path = self.database_path.with_name("settings.json")
        layout = QVBoxLayout(self)
        description = QLabel(
            "Yerel ayarlar · Yalnız bu bilgisayarda saklanır. "
            "Sağlayıcı bağlantısı veya kimlik bilgisi içermez.\n"
            "SQLite yedeği analizleri, deneme hesabını ve alarmları içerir. "
            "Ayarlar ayrı JSON dosyasındadır. "
            "Geri yükleme mevcut yerel kayıtların yerini alır."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.symbol = QLineEdit()
        self.symbol.setMaxLength(32)
        self.currency = QComboBox()
        self.currency.addItems(["TRY", "USD", "EUR"])
        row = QHBoxLayout()
        row.addWidget(QLabel("Varsayılan sembol"))
        row.addWidget(self.symbol)
        row.addWidget(QLabel("Para birimi"))
        row.addWidget(self.currency)
        layout.addLayout(row)
        actions = QHBoxLayout()
        self.save_button = QPushButton("Ayarları kaydet")
        self.backup_button = QPushButton("Yerel veriyi yedekle")
        self.restore_button = QPushButton("Yedekten geri yükle")
        for button, slot in (
            (self.save_button, self.save_settings),
            (self.backup_button, self.backup_database),
            (self.restore_button, self.restore_database),
        ):
            button.clicked.connect(slot)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status = QLabel("Ayarlar yükleniyor")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        path_label = QLabel(f"Veri: {self.database_path}\nAyarlar: {self.settings_path}")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        layout.addStretch()
        try:
            values = local_settings.load_settings(self.settings_path)
            self.status.setText("Yerel ayarlar hazır")
        except ValueError as error:
            values = local_settings.DEFAULT_SETTINGS
            self.status.setText(f"{error}; güvenli varsayılanlar gösteriliyor")
        self.symbol.setText(values["default_symbol"])
        self.currency.setCurrentText(values["default_currency"])

    def save_settings(self):
        try:
            values = local_settings.save_settings(
                self.settings_path,
                {
                    "default_symbol": self.symbol.text(),
                    "default_currency": self.currency.currentText(),
                },
            )
            self.settings_changed.emit(values)
            self.status.setText("Ayarlar kalıcı olarak kaydedildi")
        except (OSError, ValueError, sqlite3.Error) as error:
            self.status.setText(str(error))

    def backup_database(self):
        destination, _ = QFileDialog.getSaveFileName(
            self, "Yerel SQLite yedeği", "", "SQLite (*.sqlite)"
        )
        if not destination:
            return
        try:
            local_settings.backup_database(self.database_path, Path(destination))
            self.status.setText("Yerel SQLite yedeği oluşturuldu; ayarlar ayrı dosyada")
        except (OSError, ValueError, sqlite3.Error) as error:
            self.status.setText(str(error))

    def restore_database(self):
        source, _ = QFileDialog.getOpenFileName(
            self, "Mevcut yerel kayıtların yerine yedek yükle", "", "SQLite (*.sqlite)"
        )
        if not source:
            return
        try:
            local_settings.restore_database(self.database_path, Path(source))
            self.database_restored.emit()
            self.status.setText(
                "Yerel kayıtlar yedekten geri yüklendi; bağlantılar etkinleştirilmedi"
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            self.status.setText(str(error))
