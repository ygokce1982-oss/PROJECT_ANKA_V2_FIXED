from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .models import AgentResult


class BaseAgent(ABC):
    """Yapay zekâ ajanlarının temel soyut sınıfı."""

    name: str
    role: str

    @abstractmethod
    def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        """Ajana bir görev gönderir ve sonuç döndürür."""
        raise NotImplementedError
