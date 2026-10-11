"""Opt-in read-only Gemini/Claude analysis for ANKA Finans desktop.

Choosing a cloud model explicitly sends the user-entered task to that
provider. It never modifies repository source files or sends trading orders.
"""
from __future__ import annotations

from pathlib import Path

from core.agent_hub.adapters.antigravity_adapter import AntigravityAdapter
from core.ai.workflow import WorkflowResult


class RemoteReadOnlyTeam:
    """AIWorker-compatible, single-role, explicit-provider execution."""

    ROLE_MODELS = {
        "planner": "gemini-3.8-flash-low",
        "reviewer": "claude-sonnet-4-6",
    }

    def __init__(self, role: str, workspace: Path):
        if role not in self.ROLE_MODELS:
            raise ValueError("Unsupported role for controlled cloud analysis")
        self.role = role
        self.workspace = Path(workspace).resolve()
        self.model = self.ROLE_MODELS[role]

    def run(self, task: str) -> WorkflowResult:
        if not isinstance(task, str) or not task.strip() or len(task) > 4000:
            return WorkflowResult(
                success=False, step_results=(), final_output=None,
                errors=("Görev boş veya 4000 karakter sınırını aşıyor.",),
            )
        agent = AntigravityAdapter(
            "anka-read-only-" + self.role,
            self.role,
            workspace=self.workspace,
            timeout_seconds=65,
        )
        prefix = (
            "ANKA Finans finansal analiz asistanı. Sadece Türkçe cevapla. "
            "Sadece planlama veya inceleme yap; kod ve dosya değiştirme, "
            "gerçek emir veya hesap işlemi gerçekleştirme. "
            "Veri kaynağı ve sonuçları doğrulanmadıysa açıkça belirt.\nGörev: "
        )
        result = agent.run(prefix + task.strip())
        if result.success and result.output:
            return WorkflowResult(
                success=True,
                step_results=(),
                final_output=result.output,
            )
        return WorkflowResult(
            success=False,
            step_results=(),
            final_output=None,
            errors=(result.error or "Model çağrısı başarısız",),
        )
