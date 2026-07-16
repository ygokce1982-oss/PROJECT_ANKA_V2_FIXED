from __future__ import annotations

from .models import TaskRecord
from .task_store import TaskStore


class Scheduler:
    def __init__(self, task_store: TaskStore) -> None:
        self.task_store = task_store

    def select_next_task(
        self,
        worker_id: str = "agent-hub",
        lease_seconds: int = 300,
    ) -> TaskRecord | None:
        self.task_store.recover_expired_tasks()
        return self.task_store.claim_next_task(worker_id, lease_seconds)

    def mark_running(self, task: TaskRecord) -> TaskRecord:
        # Atomic claim already places the task in RUNNING state.
        return self.task_store.get_task(task.id)

    def should_retry(self, task: TaskRecord) -> bool:
        return task.attempts < task.max_attempts
