from __future__ import annotations

from datetime import datetime

from .models import TaskRecord, TaskStatus
from .task_store import TaskStore


class ApprovalPolicy:
    def __init__(self, task_store: TaskStore | None = None) -> None:
        self.task_store = task_store

    def is_approved(self, task: TaskRecord) -> bool:
        return not (task.requires_approval and not task.approved_by)

    def approve_task(
        self,
        task_id: int,
        approved_by: str,
        reason: str | None = None,
    ) -> TaskRecord:
        store = self._require_store()
        updated = store.update_task(
            task_id,
            status=TaskStatus.QUEUED,
            requires_approval=False,
            approved_by=approved_by,
            approved_at=datetime.utcnow(),
            approval_reason=reason,
            clear_lock=True,
        )
        store.record_approval_action(task_id, "approved", approved_by, reason)
        return updated

    def reject_task(
        self,
        task_id: int,
        rejected_by: str,
        reason: str | None = None,
    ) -> TaskRecord:
        store = self._require_store()
        error = f"Rejected by {rejected_by}: {reason or 'No reason provided'}"
        updated = store.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            error=error,
            approved_by=rejected_by,
            approved_at=datetime.utcnow(),
            approval_reason=reason,
            clear_lock=True,
        )
        store.record_approval_action(task_id, "rejected", rejected_by, reason)
        return updated

    def _require_store(self) -> TaskStore:
        if self.task_store is None:
            raise RuntimeError("ApprovalPolicy requires a TaskStore")
        return self.task_store
