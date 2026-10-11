"""Professional plain-text navigation with no platform-specific icon fonts."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class Sidebar(QListWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("TerminalSidebar")
        self.setFixedWidth(226)
        self.setSpacing(8)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.addItem(QListWidgetItem("01   Piyasa Merkezi"))
        self.addItem(QListWidgetItem("02   Grafik ve Analiz"))
        self.addItem(QListWidgetItem("03   ANKA Yapay Zekâ"))
        self.addItem(QListWidgetItem("04   Haber ve Araştırma"))
        self.addItem(QListWidgetItem("05   Sanal Portföy"))
        self.addItem(QListWidgetItem("06   Ayarlar"))
        self.setCurrentRow(0)
