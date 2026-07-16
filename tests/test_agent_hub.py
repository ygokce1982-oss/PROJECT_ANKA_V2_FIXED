import os
import sqlite3
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone

from core.agent_hub.agent_registry import AgentRegistry
from core.agent_hub.adapters.mock_adapter import MockAdapter
from core.agent_hub.hub import AgentHub
from core.agent_hub.models import TaskStatus
from core.agent_hub.task_store import TaskStore

os.environ.setdefault("ANKA_LOG_DIR", os.path.join(tempfile.gettempdir(), "anka-logs"))


class AgentHubTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "agent_hub.db")
        self.store = TaskStore(db_path=self.db_path)
        self.registry = AgentRegistry()
        self.hub = AgentHub(task_store=self.store, registry=self.registry)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def _make_task_ready_now(self, task_id: int) -> None:
        self.store.update_task(
            task_id,
            next_run_at=datetime.utcnow() - timedelta(seconds=1),
        )

    def test_enqueue_and_persist_task(self) -> None:
        task = self.hub.enqueue_task(
            title="Test görev",
            description="Açıklama",
            role="researcher",
        )
        loaded = self.store.get_task(task.id)
        self.assertEqual(loaded.id, task.id)
        self.assertEqual(loaded.status, TaskStatus.QUEUED)

    def test_schema_version_and_indexes_created(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM schema_version")
            self.assertEqual(cursor.fetchone()[0], 1)
            cursor = conn.execute("PRAGMA index_list('tasks')")
            indexes = [row[1] for row in cursor.fetchall()]
            self.assertIn("ix_tasks_status", indexes)
            self.assertIn("ix_tasks_role", indexes)
            self.assertIn("ix_tasks_priority", indexes)
            self.assertIn("ix_tasks_created_at", indexes)
            self.assertIn("ix_tasks_next_run_at", indexes)
        finally:
            conn.close()

    def test_register_agent_unique_name(self) -> None:
        adapter = MockAdapter(name="mock1", role="researcher")
        self.hub.register_agent("mock1", adapter)
        with self.assertRaises(ValueError):
            self.hub.register_agent("mock1", adapter)

    def test_claim_next_task_is_atomic(self) -> None:
        task = self.hub.enqueue_task(title="Claim", description="Claim", role="researcher")
        first = self.store.claim_next_task("worker-1")
        second = self.store.claim_next_task("worker-2")
        self.assertIsNotNone(first)
        self.assertIsNone(second)
        self.assertEqual(first.locked_by, "worker-1")
        self.assertEqual(self.store.get_task(task.id).status, TaskStatus.RUNNING)

    def test_claim_next_task_is_atomic_with_concurrent_workers(self) -> None:
        task = self.hub.enqueue_task(
            title="Concurrent",
            description="Concurrent",
            role="researcher",
        )
        barrier = threading.Barrier(2)
        results: list[object] = []
        results_lock = threading.Lock()

        def claim(worker_id: str) -> None:
            store = TaskStore(db_path=self.db_path)
            barrier.wait()
            result = store.claim_next_task(worker_id)
            with results_lock:
                results.append(result)

        threads = [
            threading.Thread(target=claim, args=("worker-1",)),
            threading.Thread(target=claim, args=("worker-2",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        self.assertEqual(len(results), 2)
        claimed = [result for result in results if result is not None]
        self.assertEqual(len(claimed), 1)
        self.assertEqual(self.store.get_task(task.id).status, TaskStatus.RUNNING)

    def test_run_next_executes_task(self) -> None:
        self.registry.register("mock1", MockAdapter(name="mock1", role="researcher"))
        task = self.hub.enqueue_task(title="Run", description="Do work", role="researcher")
        result = self.hub.run_next()
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
        self.assertEqual(result.status, TaskStatus.COMPLETED)
        updated = self.store.get_task(task.id)
        self.assertEqual(updated.status, TaskStatus.COMPLETED)
        self.assertEqual(updated.attempts, 1)

    def test_failure_retries_until_max_attempts(self) -> None:
        class BadAdapter(MockAdapter):
            def run(self, task: str, **kwargs: object) -> object:
                raise RuntimeError("failed")

        self.registry.register("bad", BadAdapter(name="bad", role="researcher"))
        task = self.hub.enqueue_task(
            title="Retry",
            description="Repeat",
            role="researcher",
            max_attempts=2,
        )

        first = self.hub.run_next()
        self.assertFalse(first.success)
        self.assertEqual(first.status, TaskStatus.QUEUED)
        self.assertEqual(self.store.get_task(task.id).attempts, 1)

        self._make_task_ready_now(task.id)
        second = self.hub.run_next()
        self.assertFalse(second.success)
        self.assertEqual(second.status, TaskStatus.FAILED)

        updated = self.store.get_task(task.id)
        self.assertEqual(updated.status, TaskStatus.FAILED)
        self.assertEqual(updated.attempts, 2)

    def test_backoff_sets_next_run_at(self) -> None:
        class BadAdapter(MockAdapter):
            def run(self, task: str, **kwargs: object) -> object:
                raise RuntimeError("failed")

        self.registry.register("bad", BadAdapter(name="bad", role="researcher"))
        task = self.hub.enqueue_task(
            title="Backoff",
            description="Backoff",
            role="researcher",
            max_attempts=3,
        )

        result = self.hub.run_next()
        self.assertFalse(result.success)
        updated = self.store.get_task(task.id)
        self.assertEqual(updated.status, TaskStatus.QUEUED)
        self.assertIsNotNone(updated.next_run_at)
        self.assertGreater(updated.next_run_at, datetime.utcnow())

    def test_permanent_failure_does_not_retry(self) -> None:
        class ValidationAdapter(MockAdapter):
            def run(self, task: str, **kwargs: object) -> object:
                return type(
                    "Result",
                    (),
                    {"success": False, "output": None, "error": "Validation failed"},
                )

        self.registry.register(
            "bad",
            ValidationAdapter(name="bad", role="researcher"),
        )
        task = self.hub.enqueue_task(
            title="Validate",
            description="Validate",
            role="researcher",
            max_attempts=3,
        )

        result = self.hub.run_next()
        self.assertFalse(result.success)
        self.assertEqual(result.status, TaskStatus.FAILED)
        updated = self.store.get_task(task.id)
        self.assertEqual(updated.status, TaskStatus.FAILED)
        self.assertEqual(updated.attempts, 1)
        self.assertIsNone(updated.next_run_at)

    def test_task_requires_approval_returns_blocked_result(self) -> None:
        self.registry.register("mock1", MockAdapter(name="mock1", role="researcher"))
        task = self.hub.enqueue_task(
            title="Approval",
            description="Need approval",
            role="researcher",
            requires_approval=True,
        )

        result = self.hub.run_next()
        self.assertIsNotNone(result)
        self.assertFalse(result.success)
        self.assertEqual(result.status, TaskStatus.BLOCKED)
        self.assertEqual(self.store.get_task(task.id).status, TaskStatus.BLOCKED)

    def test_approve_and_reject_workflow_records_audit(self) -> None:
        task = self.hub.enqueue_task(
            title="Approval",
            description="Need approval",
            role="researcher",
            requires_approval=True,
        )

        approved = self.hub.approve_task(task.id, "auditor", "Looks good")
        self.assertEqual(approved.status, TaskStatus.QUEUED)
        audit = self.store.get_approval_audit(task.id)
        self.assertEqual(audit[-1][0], "approved")
        self.assertEqual(audit[-1][1], "auditor")

        task2 = self.hub.enqueue_task(
            title="Reject",
            description="Need approval",
            role="researcher",
            requires_approval=True,
        )
        rejected = self.hub.reject_task(task2.id, "auditor", "Not acceptable")
        self.assertEqual(rejected.status, TaskStatus.CANCELLED)
        audit2 = self.store.get_approval_audit(task2.id)
        self.assertEqual(audit2[-1][0], "rejected")
        self.assertEqual(audit2[-1][1], "auditor")

    def test_unhealthy_agent_blocks_task(self) -> None:
        class UnhealthyAdapter(MockAdapter):
            def health_check(self) -> bool:
                return False

        self.registry.register(
            "bad",
            UnhealthyAdapter(name="bad", role="researcher"),
        )
        task = self.hub.enqueue_task(
            title="Block",
            description="Block",
            role="researcher",
        )
        result = self.hub.run_next()
        self.assertFalse(result.success)
        self.assertEqual(result.status, TaskStatus.BLOCKED)
        self.assertEqual(self.store.get_task(task.id).status, TaskStatus.BLOCKED)

    def test_healthy_agent_is_used_when_another_is_unhealthy(self) -> None:
        class UnhealthyAdapter(MockAdapter):
            def health_check(self) -> bool:
                return False

        self.registry.register(
            "bad",
            UnhealthyAdapter(name="bad", role="researcher"),
        )
        self.registry.register(
            "good",
            MockAdapter(name="good", role="researcher", output="healthy result"),
        )
        task = self.hub.enqueue_task(
            title="Fallback",
            description="Fallback",
            role="researcher",
        )
        result = self.hub.run_next()
        self.assertTrue(result.success)
        self.assertEqual(result.result, "healthy result")
        self.assertEqual(self.store.get_task(task.id).status, TaskStatus.COMPLETED)

    def test_adapter_timeout_returns_promptly(self) -> None:
        class SlowAdapter(MockAdapter):
            def run(self, task: str, **kwargs: object) -> object:
                time.sleep(1.0)
                return type("Result", (), {"success": True, "output": "done"})

        self.registry.register(
            "slow",
            SlowAdapter(name="slow", role="researcher"),
        )
        hub = AgentHub(
            task_store=self.store,
            registry=self.registry,
            adapter_timeout_seconds=0.02,
        )
        task = self.hub.enqueue_task(
            title="Timeout",
            description="Sleep",
            role="researcher",
        )

        started = time.monotonic()
        result = hub.run_next()
        elapsed = time.monotonic() - started

        self.assertFalse(result.success)
        self.assertEqual(result.status, TaskStatus.QUEUED)
        self.assertLess(elapsed, 0.5)
        self.assertEqual(self.store.get_task(task.id).attempts, 1)

    def test_failed_task_does_not_block_other_tasks(self) -> None:
        class BadAdapter(MockAdapter):
            def run(self, task: str, **kwargs: object) -> object:
                raise RuntimeError("failed")

        self.registry.register("bad", BadAdapter(name="bad", role="researcher"))
        self.registry.register("good", MockAdapter(name="good", role="researcher"))
        self.hub.enqueue_task(
            title="Fail",
            description="Fail",
            role="researcher",
            priority=200,
            max_attempts=3,
        )
        self.hub.enqueue_task(
            title="Success",
            description="Success",
            role="researcher",
            priority=100,
        )

        first = self.hub.run_next()
        self.assertFalse(first.success)
        second = self.hub.run_next()
        self.assertIsNotNone(second)
        self.assertTrue(second.success)
        self.assertEqual(second.status, TaskStatus.COMPLETED)

    def test_hub_restart_preserves_tasks(self) -> None:
        task = self.hub.enqueue_task(
            title="Persist",
            description="Persist",
            role="researcher",
        )
        new_store = TaskStore(db_path=self.db_path)
        self.assertEqual(new_store.get_task(task.id).id, task.id)

    def test_no_agent_available_requeues_without_attempt(self) -> None:
        task = self.hub.enqueue_task(
            title="No agent",
            description="No agent",
            role="missing-role",
        )
        result = self.hub.run_next()
        self.assertEqual(result.status, TaskStatus.QUEUED)
        updated = self.store.get_task(task.id)
        self.assertEqual(updated.status, TaskStatus.QUEUED)
        self.assertEqual(updated.attempts, 0)

    def test_recover_expired_running_task(self) -> None:
        task = self.hub.enqueue_task(
            title="Recover",
            description="Recover",
            role="researcher",
            max_attempts=2,
        )
        claimed = self.store.claim_next_task("worker-1", lease_seconds=1)
        self.assertEqual(claimed.status, TaskStatus.RUNNING)

        later = datetime.now(timezone.utc) + timedelta(seconds=2)
        self.store.recover_expired_tasks(now=later)
        recovered = self.store.get_task(task.id)
        self.assertEqual(recovered.status, TaskStatus.QUEUED)
        self.assertEqual(recovered.attempts, 1)


if __name__ == "__main__":
    unittest.main()
