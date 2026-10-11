"""Compact workstation rail, keyboard accessible with tooltips."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidget, QListWidgetItem


class Sidebar(QListWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("TerminalSidebar")
        self.setFixedWidth(72)
        self.setSpacing(5)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for text, tooltip in (
            ("01", "Piyasa izleme"),
            ("02", "Grafik ve analiz"),
            ("03", "ANKA Yapay Zekâ"),
            ("04", "Haber ve araştırma"),
            ("05", "Sanal portföy"),
            ("06", "Ayarlar"),
        ):
            item = QListWidgetItem(text)
            item.setToolTip(tooltip)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.addItem(item)
        self.setCurrentRow(0)
