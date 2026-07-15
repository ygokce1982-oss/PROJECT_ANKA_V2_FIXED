from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class AgentInfo:
    name: str
    agent: Any
    healthy: bool | None = None
    last_checked: datetime | None = None


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: OrderedDict[str, AgentInfo] = OrderedDict()

    def register(self, name: str, agent: Any) -> None:
        if name in self._agents:
            raise ValueError(f"Agent already registered: {name}")
        self._agents[name] = AgentInfo(name=name, agent=agent)

    def get_agent(self, name: str) -> Any:
        if name not in self._agents:
            raise KeyError(f"Agent not found: {name}")
        return self._agents[name].agent

    def get_agents_by_role(self, role: str) -> list[Any]:
        candidates = [info for info in self._agents.values() if getattr(info.agent, "role", None) == role and info.healthy]
        return [info.agent for info in candidates]

    def list_agents(self) -> list[str]:
        return list(self._agents)

    def refresh_health(self) -> None:
        now = datetime.now(timezone.utc)
        for info in self._agents.values():
            healthy = True
            try:
                healthy = info.agent.health_check()
            except Exception:
                healthy = False
            info.healthy = healthy
            info.last_checked = now
