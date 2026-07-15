from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Any


class TaskStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    REVIEW = "review"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class TaskRecord:
    id: int
    title: str
    description: str
    role: str
    priority: int
    status: TaskStatus
    attempts: int
    max_attempts: int
    created_at: datetime
    updated_at: datetime
    result: str | None = None
    error: str | None = None
    requires_approval: bool = False
    locked_by: str | None = None
    locked_at: datetime | None = None
    lease_expires_at: datetime | None = None
    next_run_at: datetime | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None
    approval_reason: str | None = None


@dataclass(frozen=True)
class TaskExecutionResult:
    task_id: int
    success: bool
    result: str | None = None
    error: str | None = None
    status: TaskStatus = TaskStatus.COMPLETED
