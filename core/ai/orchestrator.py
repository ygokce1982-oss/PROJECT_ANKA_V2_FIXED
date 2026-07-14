from __future__ import annotations

from typing import Iterable

from .base_agent import BaseAgent
from .models import AgentResult


class MultiAIOrchestrator:
    """Çoklu ajanın aynı görevleri koordine ettiği orkestratör."""

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def add_agent(self, agent: BaseAgent) -> None:
        """Aynı addan daha fazla ajanın eklenmesini engeller."""
        if agent.name in self._agents:
            raise ValueError(f"Ajan zaten kayıtlı: {agent.name}")

        self._agents[agent.name] = agent

    def remove_agent(self, name: str) -> None:
        """Kayıtlı ajanı listeden çıkarır."""
        if name not in self._agents:
            raise KeyError(f"Ajan bulunamadı: {name}")

        del self._agents[name]

    def list_agents(self) -> list[str]:
        """Kayıtlı ajan isimlerini döndürür."""
        return list(self._agents)

    def get_agents_by_role(self, role: str) -> list[BaseAgent]:
        """Belirli role sahip ajanları döndürür."""
        return [agent for agent in self._agents.values() if agent.role == role]

    def run_task(
        self,
        task: str,
        context: dict[str, object] | None = None,
        roles: Iterable[str] | None = None,
    ) -> list[AgentResult]:
        """Görevi tüm veya belirli ajanlara gönderir."""
        targets = self._agents.values()
        if roles is not None:
            targets = [agent for agent in targets if agent.role in roles]

        results: list[AgentResult] = []
        for agent in targets:
            try:
                result = agent.run(task, context=context)
            except Exception as exc:
                results.append(
                    AgentResult(
                        agent_name=agent.name,
                        role=agent.role,
                        success=False,
                        output=None,
                        error=str(exc),
                    )
                )
            else:
                results.append(result)

        return results
