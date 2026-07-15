from __future__ import annotations

from typing import Any
from .models import TaskRecord


class ApprovalPolicy:
    def __init__(self, task_store: Any | None = None) -> None:
        self.task_store = task_store

    def is_approved(self, task: TaskRecord) -> bool:
        if task.requires_approval and not task.approved_by:
            return False
        return True
