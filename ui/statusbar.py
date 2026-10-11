"""Explicit status: do not imply unverified live market connections."""
from PySide6.QtWidgets import QStatusBar


class StatusBar(QStatusBar):
    def __init__(self) -> None:
        super().__init__()
        self.showMessage(
            "ANKA Finans  •  Çevrimdışı / denetimli araştırma  •  "
            "Gerçek emir iletimi KAPALI  •  Canlı veri doğrulanmadı"
        )
