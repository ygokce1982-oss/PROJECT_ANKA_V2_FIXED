import logging
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.styles import STYLE


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PROJECT ANKA V2")
    app.setStyleSheet(STYLE)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
