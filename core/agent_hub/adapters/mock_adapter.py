from __future__ import annotations

from .base_adapter import BaseAdapter


class MockAdapter(BaseAdapter):
    def __init__(self, name: str, role: str, success: bool = True, output: str | None = None) -> None:
        super().__init__(name, role)
        self.success = success
        self.output = output or "mock output"

    def run(self, task: str, **kwargs: object) -> object:
        if not self.success:
            raise RuntimeError("Mock adapter failed")
        return type("Result", (), {"success": True, "output": self.output})

    def health_check(self) -> bool:
        return True
