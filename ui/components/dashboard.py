import logging

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
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
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        title = QLabel("📊 PİYASA PANELİ")
        title.setStyleSheet("font-size:28px;font-weight:bold;")

        self.refresh_button = QPushButton("↻ Yenile")
        self.refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_button.clicked.connect(self.refresh)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        grid = QGridLayout()
        self.cards: dict[str, InfoCard] = {}

        items = [
            ("📈 XU100", "xu100"),
            ("💵 USD/TRY", "usdtry"),
            ("💶 EUR/TRY", "eurtry"),
            ("🥇 ALTIN", "gold"),
            ("₿ BTC/USD", "btc"),
        ]

        for index, (text, key) in enumerate(items):
            card = InfoCard(text, color="#33AAFF")
            self.cards[key] = card
            grid.addWidget(card, index // 3, index % 3)

        layout.addLayout(grid)

        self.status_label = QLabel("Veriler hazırlanıyor…")
        self.status_label.setStyleSheet("color:#B0B0B0;padding:8px 2px;")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self._worker: MarketDataWorker | None = None
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._shutdown_worker)

        self.refresh()

    def refresh(self) -> None:
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
            self.status_label.setText("✓ Veriler güncellendi")
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
