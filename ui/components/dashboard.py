"""ANKA Finans professional dashboard with verified navigation and data labels.

Never display fabricated market quotes. Data-refresh is separate from local
analysis, paper portfolio, research, and agent workflow navigation.
"""
from __future__ import annotations

import logging
import os

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from core.market_data import MarketData, MarketSnapshot
from ui.components.info_card import InfoCard

LOGGER = logging.getLogger(__name__)


class MarketDataWorker(QThread):
    completed = Signal(object)

    def run(self) -> None:
        try:
            snapshot = MarketData.get_snapshot()
        except Exception:
            LOGGER.exception("Beklenmeyen piyasa verisi hatası")
            snapshot = MarketData.error_snapshot("Beklenmeyen veri hatası")
        self.completed.emit(snapshot)


class Dashboard(QWidget):
    navigate_to = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("ProfessionalDashboard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 16, 14, 14)
        layout.setSpacing(17)

        heading = QHBoxLayout()
        title_area = QVBoxLayout()
        title_area.setSpacing(4)
        title = QLabel("Piyasa Komuta Merkezi")
        title.setStyleSheet("font-size:25px;font-weight:800;color:#EBF5FF;")
        subtitle = QLabel("Piyasa gözlemi  /  çevrimdışı analiz  /  sanal portföy")
        subtitle.setStyleSheet("font-size:11px;color:#8FA9BD;")
        title_area.addWidget(title)
        title_area.addWidget(subtitle)
        heading.addLayout(title_area, 1)
        self.refresh_button = QPushButton("Verileri Yenile")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.clicked.connect(self.refresh)
        heading.addWidget(self.refresh_button)
        layout.addLayout(heading)

        banner = QFrame()
        banner.setObjectName("MarketDataNotice")
        banner.setStyleSheet(
            "QFrame#MarketDataNotice{background:#2A2830;"
            "border:1px solid #665337;border-radius:9px;}"
        )
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(17, 12, 17, 12)
        banner_label = QLabel(
            "KONTROLLÜ MOD   •   Gerçek emir iletimi kapalı"
            "   •   Doğrulanmamış canlı fiyat gösterilmez"
        )
        banner_label.setStyleSheet(
            "color:#E6BC79;font-size:11px;font-weight:700;border:none;"
        )
        banner_layout.addWidget(banner_label)
        layout.addWidget(banner)

        overview = QHBoxLayout()
        overview.setSpacing(14)

        price_container = QFrame()
        price_container.setObjectName("MarketSummary")
        price_layout = QVBoxLayout(price_container)
        price_layout.setContentsMargins(20, 20, 20, 18)
        price_layout.setSpacing(14)
        price_heading = QLabel("PİYASA GÖSTERGELERİ")
        price_heading.setStyleSheet(
            "font-size:12px;font-weight:800;color:#9EB9CF;border:none;"
        )
        price_layout.addWidget(price_heading)
        grid = QGridLayout()
        grid.setSpacing(12)
        self.cards: dict[str, InfoCard] = {}
        items = [
            ("BIST 100", "xu100"),
            ("USD / TRY", "usdtry"),
            ("EUR / TRY", "eurtry"),
            ("ALTIN", "gold"),
            ("BTC / USD", "btc"),
        ]
        for index, (label, key) in enumerate(items):
            card = InfoCard(label, color="#60D1E3")
            card.value_label.setText("—")
            self.cards[key] = card
            grid.addWidget(card, index // 3, index % 3)
        price_layout.addLayout(grid)
        self.status_label = QLabel("Veriler hazırlanıyor…")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(
            "color:#A1B7C9;padding:9px 2px;font-size:11px;border:none;"
        )
        price_layout.addWidget(self.status_label)
        overview.addWidget(price_container, 3)

        actions_frame = QFrame()
        actions_frame.setObjectName("QuickActions")
        actions = QVBoxLayout(actions_frame)
        actions.setContentsMargins(19, 20, 19, 18)
        actions.setSpacing(11)
        label = QLabel("ÇALIŞMA ALANLARI")
        label.setStyleSheet(
            "font-size:12px;font-weight:800;color:#9EB9CF;border:none;"
        )
        actions.addWidget(label)
        routes = (
            ("Grafik ve Teknik Analiz", 1, "Örnek veri / CSV / göstergeler"),
            ("ANKA Ajan Merkezi", 2, "Görevler ve denetim durumu"),
            ("Haber ve Araştırma", 3, "Yerel araştırma kayıtları"),
            ("Sanal Portföy", 4, "Gerçek emir göndermez"),
        )
        self.quick_buttons = {}
        for text, index, note in routes:
            button = QPushButton(text + "   →")
            button.setObjectName(f"QuickRoute{index}")
            button.setStyleSheet(
                "text-align:left;padding:12px 14px;"
                "color:#E3F2FA;background:#23384C;"
                "border:1px solid #38516A;"
            )
            button.clicked.connect(
                lambda checked=False, target=index: self.navigate_to.emit(target)
            )
            actions.addWidget(button)
            self.quick_buttons[index] = button
            hint = QLabel(note)
            hint.setStyleSheet(
                "color:#839CB1;font-size:10px;padding-left:5px;border:none;"
            )
            actions.addWidget(hint)
        actions.addStretch(1)
        overview.addWidget(actions_frame, 2)
        layout.addLayout(overview, 1)

        footer = QFrame()
        footer.setObjectName("DashboardFooter")
        row = QHBoxLayout(footer)
        row.setContentsMargins(18, 10, 18, 10)
        for caption in (
            "ANALİZ: Yerel veri kullanılabilir",
            "PORTFÖY: Yalnız sanal işlemler",
            "CANLI BIST: Yetki doğrulanmadı",
        ):
            info = QLabel(caption)
            info.setStyleSheet(
                "font-size:10px;color:#AFC7D7;border:none;padding:4px;"
            )
            row.addWidget(info, 1)
        layout.addWidget(footer)

        self._worker: MarketDataWorker | None = None
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._shutdown_worker)
        self.refresh()

    def refresh(self) -> None:
        if os.getenv("ANKA_OFFLINE") == "1":
            self.status_label.setText(
                "Çevrimdışı mod: canlı fiyat yok. "
                "Grafik bölümünde örnek veri veya CSV analizi kullanabilirsiniz."
            )
            return
        if self._worker is not None and self._worker.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Piyasa verileri güncelleniyor…")
        self._worker = MarketDataWorker(self)
        self._worker.completed.connect(self._apply_snapshot)
        self._worker.finished.connect(self._worker_finished)
        self._worker.start()

    def _apply_snapshot(self, snapshot: MarketSnapshot) -> None:
        for key, card in self.cards.items():
            card.set_value(snapshot.values.get(key, "---"))
        if snapshot.errors:
            self.status_label.setText("⚠ " + " • ".join(snapshot.errors))
            self.status_label.setStyleSheet("color:#FFB74D;padding:8px 2px;")
        else:
            self.status_label.setText("Veriler güncellendi")
            self.status_label.setStyleSheet("color:#66BB6A;padding:8px 2px;")

    def _worker_finished(self) -> None:
        self.refresh_button.setEnabled(True)
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()

    def _shutdown_worker(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            wait_ms = (MarketData.REQUEST_TIMEOUT * 2 + 1) * 1000
            self._worker.wait(wait_ms)
