from __future__ import annotations

import logging
from core.agent_hub import AgentHub
from core.agent_hub.agent_registry import AgentRegistry
from core.agent_hub.adapters.mock_adapter import MockAdapter
from core.agent_hub.task_store import TaskStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    task_store = TaskStore()
    registry = AgentRegistry()
    hub = AgentHub(task_store=task_store, registry=registry)

    registry.register("mock_researcher", MockAdapter(name="mock_researcher", role="researcher"))
    registry.register("mock_analyst", MockAdapter(name="mock_analyst", role="analyst"))

    task = hub.enqueue_task(
        title="Örnek görev",
        description="Bu bir Agent Hub testi görevidir.",
        role="researcher",
        priority=100,
        max_attempts=1,
    )
    logger.info("Enqueued task %s", task.id)

    result = hub.run_next()
    if result is not None:
        logger.info("Task %s finished: success=%s, status=%s", result.task_id, result.success, result.status)
    else:
        logger.info("No task available")


if __name__ == "__main__":
    main()
