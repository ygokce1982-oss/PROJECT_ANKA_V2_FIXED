"""Owned, locally styled access to the existing demo / CSV workstation."""
from PySide6.QtCore import Qt, Signal

from scripts.anka_professional_toolchain_demo import QSS, Terminal


class AdvancedTerminal(Terminal):
    closed = Signal()

    def __init__(self, parent):
        super().__init__()
        # Terminal's standalone constructor restores geometry before it has an owner.
        geometry = self.saveGeometry()
        self.setParent(parent, Qt.WindowType.Window)
        self.restoreGeometry(geometry)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet(QSS)

    def closeEvent(self, event):
        super().closeEvent(event)
        if event.isAccepted():
            self.closed.emit()
