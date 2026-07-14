from __future__ import annotations

from typing import Any

from .base_agent import BaseAgent
from .models import AgentResult


class MockAgent(BaseAgent):
    """Gerçek API olmayan test amaçlı yapay zekâ ajanı."""

    def __init__(
        self,
        name: str,
        role: str,
        success: bool = True,
        output: str | None = None,
        error: str | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.success = success
        self.output = output or "Mock output"
        self.error = error
        self.last_context: dict[str, Any] | None = None

    def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        self.last_context = context or {}

        if not self.success:
            return AgentResult(
                agent_name=self.name,
                role=self.role,
                success=False,
                output=None,
                error=self.error or "Mock agent failed",
            )

        formatted_output = f"[{self.role}] {self.name} completed: {task}"
        if context:
            formatted_output += f" | context={context}"

        return AgentResult(
            agent_name=self.name,
            role=self.role,
            success=True,
            output=formatted_output,
            error=None,
        )
