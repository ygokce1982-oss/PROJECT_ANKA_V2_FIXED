from PySide6.QtWidgets import QListWidget


class Sidebar(QListWidget):
    def __init__(self) -> None:
        super().__init__()

        self.setMaximumWidth(230)
        self.addItems(
            [
                "📈 Piyasalar",
                "📊 Grafik",
                "🤖 Yapay Zeka",
                "📰 Haberler",
                "💼 Portföy",
                "⚙️ Ayarlar",
            ]
        )
        self.setCurrentRow(0)
