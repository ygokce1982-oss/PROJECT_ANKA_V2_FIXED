from __future__ import annotations

import logging
import concurrent.futures
from datetime import datetime, timedelta
from typing import Any

from .agent_registry import AgentRegistry
from .approval_policy import ApprovalPolicy
from .models import TaskExecutionResult, TaskRecord, TaskStatus
from .scheduler import Scheduler
from .task_store import TaskStore

LOGGER = logging.getLogger(__name__)


class AgentHub:
    def __init__(
        self,
        task_store: TaskStore | None = None,
        registry: AgentRegistry | None = None,
        scheduler: Scheduler | None = None,
        approval_policy: ApprovalPolicy | None = None,
    ) -> None:
        self.task_store = task_store or TaskStore()
        self.registry = registry or AgentRegistry()
        self.scheduler = scheduler or Scheduler(self.task_store)
        self.approval_policy = approval_policy or ApprovalPolicy()

    def enqueue_task(
        self,
        title: str,
        description: str,
        role: str,
        priority: int = 100,
        max_attempts: int = 3,
        requires_approval: bool = False,
    ) -> TaskRecord:
        return self.task_store.add_task(
            title=title,
            description=description,
            role=role,
            priority=priority,
            max_attempts=max_attempts,
            requires_approval=requires_approval,
        )

    def register_agent(self, name: str, agent: Any) -> None:
        self.registry.register(name, agent)

    def approve_task(self, task_id: int, approved_by: str, reason: str | None = None) -> TaskRecord:
        now = datetime.utcnow()
        return self.task_store.update_task(
            task_id,
            status=TaskStatus.QUEUED,
            requires_approval=False,
            approved_by=approved_by,
            approved_at=now,
            approval_reason=reason,
            clear_lock=True,
        )

    def reject_task(self, task_id: int, rejected_by: str, reason: str | None = None) -> TaskRecord:
        now = datetime.utcnow()
        error_msg = f"Rejected by {rejected_by}: {reason or 'No reason provided'}"
        return self.task_store.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            error=error_msg,
            approved_by=rejected_by,
            approved_at=now,
            approval_reason=reason,
            clear_lock=True,
        )

    def run_next(self) -> TaskExecutionResult | None:
        task = self.scheduler.select_next_task()
        if task is None:
            return None

        if not self.approval_policy.is_approved(task):
            updated = self.task_store.update_task(task.id, status=TaskStatus.BLOCKED, clear_lock=True)
            return TaskExecutionResult(task_id=updated.id, success=False, status=TaskStatus.BLOCKED, error="Approval required")

        agent = self._select_agent_for_task(task)
        if agent is None:
            # Revert to QUEUED and release lock
            self.task_store.update_task(task.id, status=TaskStatus.QUEUED, clear_lock=True)
            return TaskExecutionResult(task_id=task.id, success=False, status=TaskStatus.QUEUED, error="No agent available")

        # Health check
        if hasattr(agent, "health_check"):
            try:
                is_healthy = agent.health_check()
            except Exception as exc:
                is_healthy = False
                LOGGER.warning("Agent health check raised exception: %s", exc)
            if not is_healthy:
                failed = self.task_store.update_task(
                    task.id,
                    status=TaskStatus.FAILED,
                    attempts=task.attempts + 1,
                    error="Selected agent is unhealthy",
                    clear_lock=True,
                )
                return TaskExecutionResult(task_id=failed.id, success=False, error="Selected agent is unhealthy", status=TaskStatus.FAILED)

        # We call mark_running to maintain compatibility (it updates updated_at)
        running_task = self.scheduler.mark_running(task)
        
        timeout = getattr(agent, "timeout", 30)
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(agent.run, running_task.description)
            try:
                result = future.result(timeout=timeout)
                if getattr(result, "success", False) and getattr(result, "output", None) is not None:
                    final_result = str(result.output)
                    completed = self.task_store.update_task(
                        running_task.id,
                        status=TaskStatus.COMPLETED,
                        result=final_result,
                        error=None,
                        clear_lock=True,
                    )
                    return TaskExecutionResult(task_id=completed.id, success=True, result=final_result, status=TaskStatus.COMPLETED)

                error_message = getattr(result, "error", "Agent execution failed")
                if self._is_adapter_unavailable(result):
                    return self._handle_agent_failure(running_task, error_message, retry=False)
                return self._handle_agent_failure(running_task, error_message)
            except concurrent.futures.TimeoutError:
                return self._handle_agent_failure(running_task, f"Agent execution timed out after {timeout} seconds")
            except Exception as exc:
                return self._handle_agent_failure(running_task, str(exc))

    def _select_agent_for_task(self, task: TaskRecord) -> Any | None:
        candidates = self.registry.get_agents_by_role(task.role)
        return candidates[0] if candidates else None

    def _is_adapter_unavailable(self, result: Any) -> bool:
        error = getattr(result, "error", None)
        if not isinstance(error, str):
            return False
        return "unavail" in error.lower()

    def _handle_agent_failure(self, task: TaskRecord, error: str, retry: bool = True) -> TaskExecutionResult:
        new_attempts = task.attempts + 1
        if retry and new_attempts < task.max_attempts:
            # calculate backoff
            backoff_delay = 2 ** new_attempts
            next_retry = datetime.utcnow() + timedelta(seconds=backoff_delay)
            updated = self.task_store.update_task(
                task.id,
                status=TaskStatus.QUEUED,
                attempts=new_attempts,
                next_retry_at=next_retry,
                error=error,
                clear_lock=True,
            )
            return TaskExecutionResult(task_id=updated.id, success=False, error=error, status=TaskStatus.QUEUED)

        failed = self.task_store.update_task(
            task.id,
            status=TaskStatus.FAILED,
            attempts=new_attempts,
            error=error,
            clear_lock=True,
        )
        return TaskExecutionResult(task_id=failed.id, success=False, error=error, status=TaskStatus.FAILED)
