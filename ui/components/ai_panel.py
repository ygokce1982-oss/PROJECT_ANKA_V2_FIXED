from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
    QTextEdit,
)

from core.ai.local_team import LocalAITeam
from core.ai.workflow import WorkflowResult
from ui.ai_worker import AIWorker


class AIPage(QWidget):
    def __init__(self, local_team: LocalAITeam | None = None) -> None:
        super().__init__()

        self.local_team = local_team or LocalAITeam()
        self._worker: AIWorker | None = None

        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        title = QLabel("🤖 YAPAY ZEKA")
        title.setStyleSheet("font-size:28px;font-weight:bold;")
        layout.addWidget(title)

        model_name = getattr(self.local_team, "model", LocalAITeam().model)
        model_label = QLabel(f"Kullanılan model: {model_name}")
        model_label.setStyleSheet("font-size:14px;color:#BBBBBB;padding-bottom:8px;")
        layout.addWidget(model_label)

        instruction_label = QLabel("Yapılmasını istediğiniz görevi Türkçe olarak yazın ve Analiz Et düğmesine basın.")
        instruction_label.setStyleSheet("font-size:13px;color:#CCCCCC;")
        layout.addWidget(instruction_label)

        self.task_input = QTextEdit()
        self.task_input.setPlaceholderText("Görev metnini buraya yazın...")
        self.task_input.setFixedHeight(160)
        layout.addWidget(self.task_input)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.analyze_button = QPushButton("Analiz Et")
        self.analyze_button.clicked.connect(self._on_analyze_clicked)
        self.analyze_button.setCursor(Qt.CursorShape.PointingHandCursor)
        button_layout.addWidget(self.analyze_button)
        layout.addLayout(button_layout)

        self.status_label = QLabel("AI paneli hazır.")
        self.status_label.setStyleSheet("color:#66BB6A;padding:8px 0px;")
        layout.addWidget(self.status_label)

        output_label = QLabel("Sonuç:")
        output_label.setStyleSheet("font-size:14px;color:#BBBBBB;padding-top:8px;")
        layout.addWidget(output_label)

        self.result_output = QPlainTextEdit()
        self.result_output.setReadOnly(True)
        self.result_output.setPlaceholderText("Analiz sonuçları burada görünecek...")
        self.result_output.setMinimumHeight(220)
        layout.addWidget(self.result_output)

        layout.addStretch()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self._shutdown_worker)

    def _set_status(self, text: str, color: str | None = None) -> None:
        self.status_label.setText(text)
        if color is not None:
            self.status_label.setStyleSheet(f"color:{color};padding:8px 0px;")

    def _on_analyze_clicked(self) -> None:
        task = self.task_input.toPlainText().strip()
        if not task:
            self._set_status("⚠ Görev boş olamaz.", "#FF7043")
            return

        if self._worker is not None and self._worker.isRunning():
            return

        self.analyze_button.setEnabled(False)
        self._set_status("Analiz ediliyor...", "#FFEB3B")
        self.result_output.clear()

        self._worker = AIWorker(task=task, local_team=self.local_team)
        self._worker.setParent(self)
        self._worker.result_ready.connect(self._on_result_ready)
        self._worker.finished.connect(self._worker_finished)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_result_ready(self, result: WorkflowResult) -> None:
        if result.success and result.final_output:
            self.result_output.setPlainText(result.final_output.strip())
            self._set_status("✓ Analiz tamamlandı.", "#66BB6A")
        else:
            error_text = " • ".join(result.errors) if result.errors else "Beklenmeyen analiz hatası."
            self.result_output.setPlainText(error_text)
            self._set_status("⚠ Analiz hatası. Hata alanına bakınız.", "#FF7043")

        self.analyze_button.setEnabled(True)

    def _worker_finished(self) -> None:
        self.analyze_button.setEnabled(True)
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()

    def _shutdown_worker(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(5000)
