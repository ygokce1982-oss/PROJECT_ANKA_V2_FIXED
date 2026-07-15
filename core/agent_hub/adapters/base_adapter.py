from __future__ import annotations

from typing import Any


class BaseAdapter:
    def __init__(self, name: str, role: str) -> None:
        self.name = name
        self.role = role

    def run(self, task: str, **kwargs: Any) -> Any:
        raise NotImplementedError("BaseAdapter.run must be implemented by subclasses")

    def health_check(self) -> bool:
        return False
