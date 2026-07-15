from __future__ import annotations

import json
from typing import Any

import requests

from .base_agent import BaseAgent
from .models import AgentResult


class OllamaAgent(BaseAgent):
    """Ollama yerel yapay zekâ servisine bağlanan ajan."""

    def __init__(
        self,
        name: str,
        role: str,
        model: str,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        temperature: float = 0.2,
        num_predict: int = 256,
        session: requests.Session | None = None,
    ) -> None:
        self.name = name
        self.role = role
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.temperature = temperature
        self.num_predict = num_predict
        self.session = session

    def connect(self) -> None:
        """Varsa mevcut session kullanır, yoksa yeni bir oturum oluşturur."""
        if self.session is None:
            self.session = requests.Session()
            self.session.trust_env = False

    def run(self, task: str, context: dict[str, Any] | None = None) -> AgentResult:
        if not self.model or not self.model.strip():
            return AgentResult(
                agent_name=self.name,
                role=self.role,
                success=False,
                output=None,
                error="Model adı boş olamaz",
            )

        self.connect()
        assert self.session is not None

        messages: list[dict[str, str]] = [
            {"role": "system", "content": f"Role: {self.role}"},
            {"role": "user", "content": task},
        ]

        if context is not None:
            safe_context = dict(context)
            messages.append(
                {
                    "role": "system",
                    "content": f"Context: {json.dumps(safe_context, ensure_ascii=False)}",
                }
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.num_predict,
            },
        }

        try:
            response = self.session.post(
                f"{self.base_url}/api/chat",
                timeout=self.timeout,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if not isinstance(data, dict):
                return AgentResult(
                    agent_name=self.name,
                    role=self.role,
                    success=False,
                    output=None,
                    error="Ollama yanıtı geçerli JSON sözlüğü değil",
                )

            message = data.get("message")
            if not isinstance(message, dict):
                return AgentResult(
                    agent_name=self.name,
                    role=self.role,
                    success=False,
                    output=None,
                    error="Ollama yanıtında message alanı eksik",
                )

            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                return AgentResult(
                    agent_name=self.name,
                    role=self.role,
                    success=False,
                    output=None,
                    error="Ollama yanıtında içerik yok",
                )

            return AgentResult(
                agent_name=self.name,
                role=self.role,
                success=True,
                output=content,
                error=None,
            )
        except requests.RequestException as exc:
            return AgentResult(
                agent_name=self.name,
                role=self.role,
                success=False,
                output=None,
                error=str(exc),
            )
        except ValueError as exc:
            return AgentResult(
                agent_name=self.name,
                role=self.role,
                success=False,
                output=None,
                error=str(exc),
            )

    def health_check(self) -> bool:
        self.connect()
        assert self.session is not None

        try:
            response = self.session.get(
                f"{self.base_url}/api/tags",
                timeout=5,
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
