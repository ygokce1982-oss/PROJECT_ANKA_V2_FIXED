import unittest

from core.ai.mock_agent import MockAgent
from core.ai.orchestrator import MultiAIOrchestrator


class AIOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = MultiAIOrchestrator()

    def test_add_agent(self) -> None:
        agent = MockAgent(name="coder1", role="coder")
        self.orchestrator.add_agent(agent)

        self.assertEqual(self.orchestrator.list_agents(), ["coder1"])

    def test_add_same_agent_twice_raises(self) -> None:
        agent = MockAgent(name="reviewer1", role="reviewer")
        self.orchestrator.add_agent(agent)

        with self.assertRaises(ValueError):
            self.orchestrator.add_agent(agent)

    def test_remove_agent(self) -> None:
        agent = MockAgent(name="researcher1", role="researcher")
        self.orchestrator.add_agent(agent)
        self.orchestrator.remove_agent("researcher1")

        self.assertEqual(self.orchestrator.list_agents(), [])

    def test_run_task_all_agents(self) -> None:
        coder = MockAgent(name="coder1", role="coder")
        reviewer = MockAgent(name="reviewer1", role="reviewer")
        self.orchestrator.add_agent(coder)
        self.orchestrator.add_agent(reviewer)

        results = self.orchestrator.run_task("Write code")

        self.assertEqual(len(results), 2)
        self.assertTrue(all(result.success for result in results))
        self.assertIn("coder1", [result.agent_name for result in results])
        self.assertIn("reviewer1", [result.agent_name for result in results])

    def test_run_task_by_role(self) -> None:
        coder = MockAgent(name="coder1", role="coder")
        analyst = MockAgent(name="analyst1", role="analyst")
        self.orchestrator.add_agent(coder)
        self.orchestrator.add_agent(analyst)

        results = self.orchestrator.run_task("Analyze data", roles=["analyst"])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].role, "analyst")

    def test_task_continues_when_agent_errors(self) -> None:
        good_agent = MockAgent(name="coder1", role="coder")
        bad_agent = MockAgent(
            name="reviewer1",
            role="reviewer",
            success=False,
            error="intentional failure",
        )

        self.orchestrator.add_agent(good_agent)
        self.orchestrator.add_agent(bad_agent)

        results = self.orchestrator.run_task("Review code")

        self.assertEqual(len(results), 2)
        self.assertTrue(any(result.success for result in results))
        self.assertTrue(any(not result.success for result in results))

    def test_empty_agent_list_returns_empty(self) -> None:
        results = self.orchestrator.run_task("No agents")

        self.assertEqual(results, [])

    def test_context_passed_to_agent(self) -> None:
        agent = MockAgent(name="researcher1", role="researcher")
        self.orchestrator.add_agent(agent)

        context = {"topic": "energy"}
        results = self.orchestrator.run_task("Research", context=context)

        self.assertEqual(len(results), 1)
        self.assertIn("context={'topic': 'energy'}", results[0].output)

    def test_agent_result_fields(self) -> None:
        agent = MockAgent(name="analyst1", role="analyst")
        self.orchestrator.add_agent(agent)

        results = self.orchestrator.run_task("Summarize")
        result = results[0]

        self.assertEqual(result.agent_name, "analyst1")
        self.assertEqual(result.role, "analyst")
        self.assertTrue(result.success)
        self.assertIsNone(result.error)
        self.assertIsNotNone(result.output)


if __name__ == "__main__":
    unittest.main()
