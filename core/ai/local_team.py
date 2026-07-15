from __future__ import annotations

import os
from typing import Any, Dict

from .ollama_agent import OllamaAgent
from .orchestrator import MultiAIOrchestrator
from .workflow import MultiAIWorkflow
from .workflow import WorkflowStep, WorkflowResult


class LocalAITeam:
    """Yerel Ollama ajanlarından oluşan bir takım ve iş akışı yönetimi."""

    DEFAULT_MODEL = "qwen3:4b"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        agents: Dict[str, object] | None = None,
    ) -> None:
        self.model = model or os.getenv("ANKA_OLLAMA_MODEL", self.DEFAULT_MODEL)
        self.base_url = base_url or os.getenv("ANKA_OLLAMA_URL", self.DEFAULT_BASE_URL)

        self.orchestrator = MultiAIOrchestrator()

        # roles in order
        self.roles = ["researcher", "coder", "reviewer", "analyst"]

        # accept injected agents for tests
        if agents is None:
            # create OllamaAgent instances per role
            for role in self.roles:
                agent = OllamaAgent(name=role, role=role, model=self.model, base_url=self.base_url)
                self.orchestrator.add_agent(agent)
        else:
            for role in self.roles:
                if role in agents:
                    agent = agents[role]
                    # register injected agent under the role name so workflow step uses role as agent_name
                    try:
                        agent.name = role
                    except Exception:
                        pass
                    self.orchestrator.add_agent(agent)
                else:
                    # if not provided, create a default OllamaAgent
                    agent = OllamaAgent(name=role, role=role, model=self.model, base_url=self.base_url)
                    self.orchestrator.add_agent(agent)

        # default workflow
        self.workflow = MultiAIWorkflow(self.orchestrator)
        self.workflow.add_step(
            WorkflowStep(
                name="research",
                role="researcher",
                task_template=(
                    "Görevi sadece Türkçe, kısa ve somut yanıtla. "
                    "Kullanıcıdan ek bilgi isteme. Takip sorusu sorma. "
                    "Görevi mevcut bilgilerle tamamla. Gereksiz giriş veya kapanış yazma. "
                    "Düşünme sürecini gösterme. En fazla 5 madde yaz. "
                    "previous_output:\n{previous_output}\nTask: {task}"
                ),
                required=True,
            )
        )
        self.workflow.add_step(
            WorkflowStep(
                name="code",
                role="coder",
                task_template=(
                    "Görevi sadece Türkçe, kısa ve somut şekilde uygula. "
                    "Kod gerekmiyorsa kod yazma. Önceki çıktıyı geliştir. "
                    "En fazla 8 kısa madde veya kısa kod bloğu kullan. "
                    "previous_output:\n{previous_output}\nTask: {task}"
                ),
                required=True,
            )
        )
        self.workflow.add_step(
            WorkflowStep(
                name="review",
                role="reviewer",
                task_template=(
                    "Görevi sadece Türkçe, kısa ve somut şekilde gözden geçir. "
                    "Hataları, riskleri ve eksikleri belirt. Ek soru sorma. "
                    "Düzeltilmiş öneriyi doğrudan yaz. En fazla 5 madde kullan. "
                    "previous_output:\n{previous_output}\nTask: {task}"
                ),
                required=True,
            )
        )
        self.workflow.add_step(
            WorkflowStep(
                name="analysis",
                role="analyst",
                task_template=(
                    "Görevi sadece Türkçe, kısa ve somut şekilde sonuca bağla. "
                    "Önceki sonuçları birleştir. Kullanıcıya gösterilecek nihai Türkçe cevabı üret. "
                    "Takip sorusu veya seçenek teklifiyle bitir. En fazla 150 kelime kullan. "
                    "previous_output:\n{previous_output}\nTask: {task}"
                ),
                required=True,
            )
        )

    def health_check(self) -> bool:
        # check each agent if it supports health_check, assume True otherwise
        for name in self.orchestrator.list_agents():
            agent = self.orchestrator._agents[name]
            if hasattr(agent, "health_check"):
                try:
                    if not agent.health_check():
                        return False
                except Exception:
                    return False
        return True

    def run(self, task: str, context: Dict[str, Any] | None = None) -> WorkflowResult:
        if not task or not task.strip():
            return WorkflowResult(success=False, step_results=(), final_output=None, errors=("Görev metni boş olamaz",))

        # do health check first
        if not self.health_check():
            return WorkflowResult(success=False, step_results=(), final_output=None, errors=("Ollama servisine ulaşılamıyor veya bazı ajanlar sağlıksız",))

        # ensure context not mutated
        context_copy = dict(context) if context is not None else None

        result = self.workflow.run(task, context=context_copy)
        return result
