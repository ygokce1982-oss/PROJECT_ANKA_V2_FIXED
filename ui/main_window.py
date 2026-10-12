"""ANKA Finans workspace shell — reference-driven market terminal."""
from __future__ import annotations
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
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
        self.resize(1440, 900)
        self.setMinimumSize(1080, 680)
        self._auxiliary_windows = []
        self._advanced_terminal = None
        self._build_ui()
        self.setStatusBar(StatusBar())
        tools_menu = self.menuBar().addMenu("Araçlar")
        advanced_action = QAction("Gelişmiş grafikler (Demo / CSV)", self)
        advanced_action.setObjectName("openAdvancedTerminalAction")
        advanced_action.triggered.connect(self.open_advanced_terminal)
        tools_menu.addAction(advanced_action)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("TerminalRoot")
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setObjectName("TerminalTopBar")
        top.setFixedHeight(66)
        hl = QHBoxLayout(top)
        hl.setContentsMargins(17, 7, 16, 7)
        hl.setSpacing(15)
        mark = QLabel("A")
        mark.setObjectName("Mark")
        mark.setFixedSize(35, 35)
        mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hl.addWidget(mark)
        self.page_title = QLabel("ANKA")
        self.page_title.setObjectName("BrandLabel")
        hl.addWidget(self.page_title)
        hl.addWidget(QLabel("F İ N A N S"), 0)
        sep = QFrame()
        sep.setObjectName("TopDivider")
        sep.setFixedSize(1, 33)
        hl.addWidget(sep)
        hl.addWidget(QLabel("ÇALIŞMA ALANI"), 0)
        hl.addWidget(QLabel("Piyasa izleme  ▾"), 0)
        hl.addWidget(QLabel("● Düzen kayıtlı"), 0)
        hl.addStretch(1)
        grid_button = QPushButton("3 ekran")
        grid_button.setObjectName("SecondaryButton")
        grid_button.clicked.connect(self.open_workspace_window)
        hl.addWidget(grid_button)
        hl.addWidget(QLabel("DEMO"), 0)
        user = QLabel("AK")
        user.setObjectName("UserBadge")
        user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user.setFixedSize(32, 32)
        hl.addWidget(user)
        outer.addWidget(top)

        strip = QFrame()
        strip.setObjectName("PriceStrip")
        strip.setFixedHeight(36)
        prices = QHBoxLayout(strip)
        prices.setContentsMargins(85, 1, 18, 1)
        prices.setSpacing(17)
        for item in (
            "BIST 100      11.765,42     +1,24%",
            "BIST 30      13.428,16     +1,48%",
            "USD/TRY      43,28     +0,08%",
            "EUR/TRY      50,14     -0,12%",
            "ALTIN (GR)      5.842,60     +0,67%",
        ):
            label = QLabel(item)
            label.setObjectName("TickerItem")
            prices.addWidget(label)
        prices.addStretch()
        prices.addWidget(QLabel("ÖRNEK PİYASA ÖZETİ"))
        outer.addWidget(strip)

        center = QHBoxLayout()
        center.setContentsMargins(0, 0, 0, 0)
        center.setSpacing(0)
        self.sidebar = Sidebar()
        self.workspace = Workspace()
        center.addWidget(self.sidebar)
        center.addWidget(self.workspace, 1)
        outer.addLayout(center, 1)
        self.sidebar.currentRowChanged.connect(self.workspace.setCurrentIndex)
        self.workspace.currentChanged.connect(self.sidebar.setCurrentRow)

    def open_advanced_terminal(self):
        if self._advanced_terminal is None:
            # Load the existing workstation only when requested; never run its launcher.
            from ui.advanced_terminal import AdvancedTerminal

            terminal = AdvancedTerminal(self)
            self._advanced_terminal = terminal
            terminal.closed.connect(lambda: self._release_advanced_terminal(terminal))
            terminal.destroyed.connect(lambda: self._release_advanced_terminal(terminal))
        terminal = self._advanced_terminal
        if terminal.isMinimized():
            terminal.showNormal()
        else:
            terminal.show()
        terminal.raise_()
        terminal.activateWindow()
        return terminal

    def _release_advanced_terminal(self, terminal):
        # A deferred deletion from an older window must not clear a newly opened one.
        if self._advanced_terminal is terminal:
            self._advanced_terminal = None

    def open_workspace_window(self):
        visible = [
            w for w in QApplication.topLevelWidgets()
            if isinstance(w, MainWindow) and w.isVisible()
        ]
        if len(visible) >= 3:
            self.statusBar().showMessage("En fazla üç çalışma penceresi açılabilir", 5000)
            return None
        window = MainWindow()
        window.setWindowTitle("ANKA Finans | Ek Çalışma Penceresi")
        window.show()
        self._auxiliary_windows.append(window)
        return window

    def closeEvent(self, event):
        if self._advanced_terminal is not None:
            self._advanced_terminal.close()
        for window in self._auxiliary_windows:
            window.close()
        super().closeEvent(event)
