from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from ui.components.dashboard import Dashboard


class SimplePage(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:24px;font-weight:bold;padding:10px;")

        info = QLabel("Bu modül sonraki sürümlerde geliştirilecektir.")
        info.setStyleSheet("font-size:14px;color:#B0B0B0;padding:10px;")

        layout.addWidget(title_label)
        layout.addWidget(info)
        layout.addStretch()


class Workspace(QStackedWidget):
    def __init__(self) -> None:
        super().__init__()

        self.addWidget(Dashboard())
        self.addWidget(SimplePage("📊 Grafik"))
        self.addWidget(SimplePage("🤖 Yapay Zeka"))
        self.addWidget(SimplePage("📰 Haberler"))
        self.addWidget(SimplePage("💼 Portföy"))
        self.addWidget(SimplePage("⚙️ Ayarlar"))
