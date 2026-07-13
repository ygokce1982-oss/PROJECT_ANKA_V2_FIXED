from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class InfoCard(QFrame):
    def __init__(self, title: str, value: str = "---", color: str = "#2196F3") -> None:
        super().__init__()

        self.setMinimumHeight(120)
        layout = QVBoxLayout(self)

        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size:13px;color:#BBBBBB;font-weight:bold;border:none;")

        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(
            f"font-size:24px;font-weight:bold;color:{color};border:none;"
        )

        layout.addStretch()
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()

    def set_value(self, value: object) -> None:
        self.value_label.setText(str(value))
