"""Offline checks for the ANKA local delivery team."""

import tempfile
import unittest
from pathlib import Path

from core.agent_hub import AgentHub
from core.agent_hub.agent_registry import AgentRegistry
from core.agent_hub.task_store import TaskStore
from scripts.anka_team import ROLE_MODELS, build_registry, project_snapshot, seed_tasks, write_report


class DeliveryTeamTests(unittest.TestCase):
    def test_four_roles_have_local_models(self) -> None:
        registry = build_registry("http://localhost:11434")
        self.assertEqual(len(registry.list_agents()), 4)
        for role, model in ROLE_MODELS.items():
            agent = registry.get_agent(f"local-{role}")
            self.assertEqual(agent.role, role)
            self.assertEqual(agent.agent.model, model)

    def test_seed_is_idempotent_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = TaskStore(db_path=str(Path(directory) / "tasks.db"))
            hub = AgentHub(task_store=store, registry=AgentRegistry())
            created = seed_tasks(hub, "Test dokumani")
            self.assertEqual(len(created), 4)
            self.assertEqual(seed_tasks(hub, "Test dokumani"), [])
            self.assertEqual(len(store.list_tasks()), 4)
            for task in store.list_tasks():
                self.assertFalse(task.requires_approval)
                self.assertEqual(task.max_attempts, 1)
                self.assertIn("komut calistirma YAPMA", task.description)

    def test_snapshot_reads_only_allowlisted_docs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "PROJECT_STATUS.md").write_text("prototip", encoding="utf-8")
            (root / "docs" / "ARCHITECTURE.md").write_text("mimari", encoding="utf-8")
            (root / ".env").write_text("SECRET_TOKEN=never_share", encoding="utf-8")
            result = project_snapshot(root)
            self.assertIn("prototip", result)
            self.assertIn("mimari", result)
            self.assertNotIn("never_share", result)

    def test_report_contains_task_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = TaskStore(db_path=str(root / "tasks.db"))
            hub = AgentHub(task_store=store, registry=AgentRegistry())
            seed_tasks(hub, "Test")
            report = root / "report.md"
            write_report(store, report)
            content = report.read_text(encoding="utf-8")
            self.assertIn("Yerel Ajan Ekibi", content)
            self.assertEqual(content.count("## ANKA-TEAM-20261009"), 4)
            self.assertIn("queued", content)

    def test_run_returns_failure_when_an_agent_fails(self) -> None:
        from unittest.mock import patch

        from core.agent_hub.models import TaskExecutionResult, TaskStatus
        from scripts.anka_team import main

        with tempfile.TemporaryDirectory() as directory:
            failure = TaskExecutionResult(
                task_id=1, success=False, status=TaskStatus.FAILED, error="Model unavailable"
            )
            with (
                patch("scripts.anka_team.available_models", return_value=set(ROLE_MODELS.values())),
                patch("scripts.anka_team.AgentHub.run_next", return_value=failure),
                patch("scripts.anka_team.write_report"),
            ):
                result = main(["run", "--db", str(Path(directory) / "tasks.db"), "--max-tasks", "1"])
            self.assertEqual(result, 1)

    def test_retry_only_resets_failed_team_tasks(self) -> None:
        from core.agent_hub.models import TaskStatus
        from scripts.anka_team import main

        with tempfile.TemporaryDirectory() as directory:
            db = str(Path(directory) / "tasks.db")
            store = TaskStore(db_path=db)
            hub = AgentHub(task_store=store, registry=AgentRegistry())
            ids = seed_tasks(hub, "Test")
            store.update_task(ids[0], status=TaskStatus.FAILED, attempts=1)
            other = store.add_task("Baska is", "Baska", "researcher")
            store.update_task(other.id, status=TaskStatus.FAILED, attempts=1)
            self.assertEqual(main(["retry", "--db", db]), 0)
            self.assertEqual(store.get_task(ids[0]).status, TaskStatus.QUEUED)
            self.assertEqual(store.get_task(ids[0]).attempts, 0)
            self.assertEqual(store.get_task(other.id).status, TaskStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
