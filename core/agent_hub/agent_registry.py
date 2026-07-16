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

    def get_agent_infos_by_role(self, role: str) -> list[AgentInfo]:
        return [
            info
            for info in self._agents.values()
            if getattr(info.agent, "role", None) == role
        ]

    def has_agents_for_role(self, role: str) -> bool:
        return bool(self.get_agent_infos_by_role(role))

    def get_agents_by_role(self, role: str) -> list[Any]:
        infos = self.get_agent_infos_by_role(role)
        for info in infos:
            self._refresh_info(info)
        return [info.agent for info in infos if info.healthy]

    def list_agents(self) -> list[str]:
        return list(self._agents)

    def refresh_health(self) -> None:
        for info in self._agents.values():
            self._refresh_info(info)

    @staticmethod
    def _check_health(agent: Any) -> bool:
        health_check = getattr(agent, "health_check", None)
        if health_check is None:
            return True
        try:
            return bool(health_check())
        except Exception:
            return False

    def _refresh_info(self, info: AgentInfo) -> None:
        info.healthy = self._check_health(info.agent)
        info.last_checked = datetime.now(timezone.utc)
