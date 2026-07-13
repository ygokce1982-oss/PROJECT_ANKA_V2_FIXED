from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

from ui.sidebar import Sidebar
from ui.statusbar import StatusBar
from ui.workspace import Workspace


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("PROJECT ANKA V2 | YG ALPHA TERMINAL")
        self.resize(1600, 900)

        self._build_ui()
        self.setStatusBar(StatusBar())

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        title = QLabel("PROJECT ANKA | YG ALPHA TERMINAL")
        title.setStyleSheet("font-size:24px;font-weight:bold;padding:12px;")
        main_layout.addWidget(title)

        body = QHBoxLayout()
        self.sidebar = Sidebar()
        self.workspace = Workspace()

        body.addWidget(self.sidebar)
        body.addWidget(self.workspace, 1)
        main_layout.addLayout(body, 1)

        self.sidebar.currentRowChanged.connect(self.workspace.setCurrentIndex)
