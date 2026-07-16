from __future__ import annotations

import logging
import queue
import threading
from datetime import datetime, timedelta
from typing import Any

from .agent_registry import AgentRegistry
from .approval_policy import ApprovalPolicy
from .models import TaskExecutionResult, TaskRecord, TaskStatus
from .scheduler import Scheduler
from .task_store import TaskStore

LOGGER = logging.getLogger(__name__)


class AgentExecutionTimeout(RuntimeError):
    pass


class AgentHub:
    def __init__(
        self,
        task_store: TaskStore | None = None,
        registry: AgentRegistry | None = None,
        scheduler: Scheduler | None = None,
        approval_policy: ApprovalPolicy | None = None,
        adapter_timeout_seconds: float = 30.0,
        worker_id: str = "agent-hub",
        lease_seconds: int = 300,
    ) -> None:
        if adapter_timeout_seconds <= 0:
            raise ValueError("adapter_timeout_seconds must be positive")
        if lease_seconds <= 0:
            raise ValueError("lease_seconds must be positive")

        self.task_store = task_store or TaskStore()
        self.registry = registry or AgentRegistry()
        self.scheduler = scheduler or Scheduler(self.task_store)
        self.approval_policy = approval_policy or ApprovalPolicy(self.task_store)
        if getattr(self.approval_policy, "task_store", None) is None:
            self.approval_policy.task_store = self.task_store

        self.adapter_timeout_seconds = float(adapter_timeout_seconds)
        self.worker_id = worker_id
        self.lease_seconds = lease_seconds
        self._quarantined_agents: set[int] = set()

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

    def approve_task(
        self,
        task_id: int,
        approved_by: str,
        reason: str | None = None,
    ) -> TaskRecord:
        return self.approval_policy.approve_task(task_id, approved_by, reason)

    def reject_task(
        self,
        task_id: int,
        rejected_by: str,
        reason: str | None = None,
    ) -> TaskRecord:
        return self.approval_policy.reject_task(task_id, rejected_by, reason)

    def run_next(self) -> TaskExecutionResult | None:
        task = self.scheduler.select_next_task(
            worker_id=self.worker_id,
            lease_seconds=self.lease_seconds,
        )
        if task is None:
            return None

        if not self.approval_policy.is_approved(task):
            updated = self.task_store.update_task(
                task.id,
                status=TaskStatus.BLOCKED,
                clear_lock=True,
            )
            return TaskExecutionResult(
                task_id=updated.id,
                success=False,
                status=TaskStatus.BLOCKED,
                error="Approval required",
            )

        matching_agents = self.registry.get_agent_infos_by_role(task.role)
        healthy_agents = self.registry.get_agents_by_role(task.role)

        if not healthy_agents:
            if matching_agents:
                updated = self.task_store.update_task(
                    task.id,
                    status=TaskStatus.BLOCKED,
                    error="All matching agents are unhealthy",
                    clear_lock=True,
                )
                return TaskExecutionResult(
                    task_id=updated.id,
                    success=False,
                    status=TaskStatus.BLOCKED,
                    error="All matching agents are unhealthy",
                )

            updated = self.task_store.update_task(
                task.id,
                status=TaskStatus.QUEUED,
                error="No agent available",
                clear_lock=True,
            )
            return TaskExecutionResult(
                task_id=updated.id,
                success=False,
                status=TaskStatus.QUEUED,
                error="No agent available",
            )

        available_agents = [
            candidate
            for candidate in healthy_agents
            if id(candidate) not in self._quarantined_agents
        ]
        agent = available_agents[0] if available_agents else healthy_agents[0]

        try:
            result = self._run_agent_with_timeout(
                agent,
                task.description,
                self.adapter_timeout_seconds,
            )
        except AgentExecutionTimeout as exc:
            self._quarantined_agents.add(id(agent))
            return self._handle_agent_failure(task, str(exc), retry=True)
        except Exception as exc:
            self._quarantined_agents.add(id(agent))
            return self._handle_agent_failure(task, str(exc), retry=True)

        attempts = task.attempts + 1
        if getattr(result, "success", False) and getattr(result, "output", None) is not None:
            self._quarantined_agents.discard(id(agent))
            final_result = str(result.output)
            completed = self.task_store.update_task(
                task.id,
                status=TaskStatus.COMPLETED,
                attempts=attempts,
                result=final_result,
                error="",
                clear_lock=True,
            )
            return TaskExecutionResult(
                task_id=completed.id,
                success=True,
                result=final_result,
                status=TaskStatus.COMPLETED,
            )

        error_message = str(getattr(result, "error", None) or "Agent execution failed")
        self._quarantined_agents.add(id(agent))
        retry = not self._is_permanent_error(error_message)
        return self._handle_agent_failure(task, error_message, retry=retry)

    @staticmethod
    def _run_agent_with_timeout(agent: Any, description: str, timeout: float) -> Any:
        outcomes: queue.Queue[tuple[str, Any]] = queue.Queue(maxsize=1)

        def invoke() -> None:
            try:
                outcomes.put(("result", agent.run(description)))
            except Exception as exc:
                outcomes.put(("error", exc))

        worker = threading.Thread(
            target=invoke,
            name=f"anka-agent-{getattr(agent, 'name', 'worker')}",
            daemon=True,
        )
        worker.start()

        try:
            kind, payload = outcomes.get(timeout=timeout)
        except queue.Empty as exc:
            raise AgentExecutionTimeout(
                f"Agent execution timed out after {timeout:g} seconds"
            ) from exc

        if kind == "error":
            raise payload
        return payload

    @staticmethod
    def _is_permanent_error(error: str) -> bool:
        normalized = error.lower()
        permanent_markers = (
            "validation",
            "invalid",
            "unsupported",
            "not implemented",
            "unauthorized",
            "forbidden",
            "permission denied",
            "not configured",
            "adapter unavailable",
        )
        return any(marker in normalized for marker in permanent_markers)

    def _handle_agent_failure(
        self,
        task: TaskRecord,
        error: str,
        retry: bool = True,
    ) -> TaskExecutionResult:
        new_attempts = task.attempts + 1

        if retry and new_attempts < task.max_attempts:
            backoff_delay = 2 ** new_attempts
            next_run = datetime.utcnow() + timedelta(seconds=backoff_delay)
            updated = self.task_store.update_task(
                task.id,
                status=TaskStatus.QUEUED,
                attempts=new_attempts,
                next_run_at=next_run,
                error=error,
                clear_lock=True,
            )
            return TaskExecutionResult(
                task_id=updated.id,
                success=False,
                error=error,
                status=TaskStatus.QUEUED,
            )

        failed = self.task_store.update_task(
            task.id,
            status=TaskStatus.FAILED,
            attempts=new_attempts,
            error=error,
            clear_lock=True,
        )
        return TaskExecutionResult(
            task_id=failed.id,
            success=False,
            error=error,
            status=TaskStatus.FAILED,
        )
