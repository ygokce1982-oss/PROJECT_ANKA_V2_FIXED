"""ANKA Finans professional desktop shell (offline-safe)."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QVBoxLayout, QWidget,
)

from ui.sidebar import Sidebar
from ui.statusbar import StatusBar
from ui.workspace import Workspace


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("AnkaMain")
        self.setWindowTitle("ANKA Finans | Profesyonel Piyasa Terminali")
        self.resize(1640, 960)
        self.setMinimumSize(1090, 700)
        self._auxiliary_windows = []
        self._build_ui()
        self.setStatusBar(StatusBar())

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("TerminalRoot")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setObjectName("TerminalTopBar")
        top.setFixedHeight(88)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(30, 12, 24, 12)
        brand = QVBoxLayout()
        brand.setSpacing(3)
        self.page_title = QLabel("ANKA  /  FİNANS")
        self.page_title.setObjectName("BrandLabel")
        brand.addWidget(self.page_title)
        subtitle = QLabel("PİYASA İSTİHBARATI  ·  ARAŞTIRMA VE KARAR DESTEK")
        subtitle.setObjectName("BrandSubTitle")
        brand.addWidget(subtitle)
        top_layout.addLayout(brand)
        top_layout.addStretch(1)
        label = QLabel("ÇEVRİMDIŞI / KONTROLLÜ")
        label.setObjectName("OfflineBadge")
        top_layout.addWidget(label)
        multi = QPushButton("Yeni Çalışma Penceresi")
        multi.setObjectName("SecondaryButton")
        multi.clicked.connect(self.open_workspace_window)
        top_layout.addWidget(multi)
        outer.addWidget(top)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        self.sidebar = Sidebar()
        self.workspace = Workspace()
        body.addWidget(self.sidebar)
        body.addWidget(self.workspace, 1)
        outer.addLayout(body, 1)
        self.sidebar.currentRowChanged.connect(self.workspace.setCurrentIndex)
        self.workspace.currentChanged.connect(self.sidebar.setCurrentRow)

    def open_workspace_window(self):
        visible = [
            window for window in QApplication.topLevelWidgets()
            if isinstance(window, MainWindow) and window.isVisible()
        ]
        if len(visible) >= 3:
            self.statusBar().showMessage(
                "En fazla üç bağımsız çalışma penceresi kullanılabilir", 5000
            )
            return None
        window = MainWindow()
        window.setWindowTitle("ANKA Finans | Ek Çalışma Penceresi")
        window.show()
        self._auxiliary_windows.append(window)
        return window

    def closeEvent(self, event):
        for window in self._auxiliary_windows:
            window.close()
        super().closeEvent(event)
