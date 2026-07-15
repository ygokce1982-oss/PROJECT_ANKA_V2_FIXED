from __future__ import annotations

from typing import Optional

from .models import TaskRecord, TaskStatus
from .task_store import TaskStore


class Scheduler:
    def __init__(self, task_store: TaskStore) -> None:
        self.task_store = task_store

    def select_next_task(self) -> TaskRecord | None:
        self.task_store.recover_expired_leases(lease_duration_seconds=300)
        return self.task_store.lock_next_task()

    def mark_running(self, task: TaskRecord) -> TaskRecord:
        return self.task_store.update_task(task.id, status=TaskStatus.RUNNING)

    def should_retry(self, task: TaskRecord) -> bool:
        return task.attempts + 1 < task.max_attempts
