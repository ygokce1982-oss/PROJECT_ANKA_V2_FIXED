from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from ui.components.ai_panel import AIPage
from ui.components.dashboard import Dashboard
from ui.components.local_workbench import LocalWorkbenchPage, PaperPortfolioPage
from ui.components.research_page import ResearchPage
from ui.components.settings_page import SettingsPage


class SimplePage(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size:24px;font-weight:bold;padding:10px;")

        info = QLabel("Bu modül sonraki sürümlerde geliştirilecektir.")
        info.setStyleSheet("font-size:14px;color:#B0B0B0;padding:10px;")

        layout.addWidget(title_label)
        layout.addWidget(info)
        layout.addStretch()


class Workspace(QStackedWidget):
    def __init__(self) -> None:
        super().__init__()

        self.dashboard = Dashboard()
        self.addWidget(self.dashboard)
        self.dashboard.navigate_to.connect(self.setCurrentIndex)
        self.addWidget(LocalWorkbenchPage())
        self.addWidget(AIPage())
        self.addWidget(ResearchPage())
        self.addWidget(PaperPortfolioPage())
        settings = SettingsPage()
        self.addWidget(settings)
        settings.settings_changed.connect(self.apply_settings)
        settings.database_restored.connect(self.refresh_restored_state)

    def apply_settings(self, values):
        analysis = self.widget(1)
        analysis.symbol.setText(values["default_symbol"])
        analysis.currency.setCurrentText(values["default_currency"])

    def refresh_restored_state(self):
        self.widget(1).clear_analysis()
        self.widget(3).refresh()
        self.widget(4).refresh()
