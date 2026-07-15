from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.ai.local_team import LocalAITeam
from core.ai.workflow import WorkflowResult


class AIWorker(QThread):
    result_ready = Signal(object)

    def __init__(self, task: str, local_team: LocalAITeam | None = None) -> None:
        super().__init__()
        self.task = task
        self.local_team = local_team or LocalAITeam()

    def run(self) -> None:
        try:
            result = self.local_team.run(self.task)
        except Exception as exc:
            result = WorkflowResult(
                success=False,
                step_results=(),
                final_output=None,
                errors=(f"Ollama işleminde beklenmeyen hata: {exc}",),
            )
        self.result_ready.emit(result)
