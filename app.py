import sys

from PySide6.QtWidgets import QApplication

from core.logging_config import configure_logging
from ui.main_window import MainWindow
from ui.styles import STYLE


def main() -> None:
    configure_logging()

    app = QApplication(sys.argv)
    app.setApplicationName("PROJECT ANKA V2")
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
