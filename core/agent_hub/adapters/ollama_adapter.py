from __future__ import annotations

from core.ai.ollama_agent import OllamaAgent
from .base_adapter import BaseAdapter


class OllamaAdapter(BaseAdapter):
    def __init__(self, name: str, role: str, model: str | None = None, base_url: str | None = None) -> None:
        super().__init__(name, role)
        self.agent = OllamaAgent(name=name, role=role, model=model or "qwen3:4b", base_url=base_url or "http://localhost:11434")

    def run(self, task: str, **kwargs: object) -> object:
        return self.agent.run(task)

    def health_check(self) -> bool:
        return self.agent.health_check()
