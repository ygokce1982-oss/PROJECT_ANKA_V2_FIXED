from __future__ import annotations

from .base_adapter import BaseAdapter


class AntigravityAdapter(BaseAdapter):
    def __init__(self, name: str, role: str) -> None:
        super().__init__(name, role)

    def run(self, task: str, **kwargs: object) -> object:
        return type("Result", (), {"success": False, "output": None, "error": "Unavailable"})

    def health_check(self) -> bool:
        return False
