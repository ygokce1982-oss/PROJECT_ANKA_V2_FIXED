import unittest

from core.ai.mock_agent import MockAgent
from core.ai.workflow import MultiAIWorkflow, WorkflowResult, WorkflowStep
from core.ai.orchestrator import MultiAIOrchestrator


class AIWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = MultiAIOrchestrator()
        self.workflow = MultiAIWorkflow(self.orchestrator)

    def test_add_and_remove_step(self) -> None:
        step = WorkflowStep(
            name="draft",
            role="coder",
            task_template="{task}",
            required=True,
        )
        self.workflow.add_step(step)
        self.assertEqual(self.workflow.list_steps(), ["draft"])

        self.workflow.remove_step("draft")
        self.assertEqual(self.workflow.list_steps(), [])

    def test_coder_reviewer_sequence(self) -> None:
        coder = MockAgent(name="coder1", role="coder")
        reviewer = MockAgent(name="reviewer1", role="reviewer")
        self.orchestrator.add_agent(coder)
        self.orchestrator.add_agent(reviewer)

        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}")
        )
        self.workflow.add_step(
            WorkflowStep(name="review", role="reviewer", task_template="Review: {previous_output}")
        )

        result = self.workflow.run("Write code")

        self.assertTrue(result.success)
        self.assertIn(
            "[reviewer] reviewer1 completed: Review: [coder] coder1 completed: Write code",
            result.final_output,
        )

    def test_previous_output_passed(self) -> None:
        coder = MockAgent(name="coder1", role="coder")
        reviewer = MockAgent(name="reviewer1", role="reviewer")
        self.orchestrator.add_agent(coder)
        self.orchestrator.add_agent(reviewer)

        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}"),
        )
        self.workflow.add_step(
            WorkflowStep(name="review", role="reviewer", task_template="Next: {previous_output}"),
        )

        result = self.workflow.run("Write code")

        self.assertTrue(result.success)
        self.assertIn("Next: [coder] coder1 completed: Write code", result.final_output)

    def test_context_not_mutated(self) -> None:
        coder = MockAgent(name="coder1", role="coder")
        self.orchestrator.add_agent(coder)
        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}")
        )

        context = {"topic": "finance"}
        self.workflow.run("Write code", context=context)

        self.assertEqual(context, {"topic": "finance"})

    def test_required_step_failure_stops(self) -> None:
        coder = MockAgent(name="coder1", role="coder", success=False, error="fail")
        reviewer = MockAgent(name="reviewer1", role="reviewer")
        self.orchestrator.add_agent(coder)
        self.orchestrator.add_agent(reviewer)

        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}", required=True)
        )
        self.workflow.add_step(
            WorkflowStep(name="review", role="reviewer", task_template="Review: {previous_output}", required=True)
        )

        result = self.workflow.run("Write code")

        self.assertFalse(result.success)
        self.assertEqual(len(result.step_results), 1)

    def test_optional_step_failure_continues(self) -> None:
        coder = MockAgent(name="coder1", role="coder")
        reviewer = MockAgent(name="reviewer1", role="reviewer", success=False, error="review fail")
        analyst = MockAgent(name="analyst1", role="analyst")
        self.orchestrator.add_agent(coder)
        self.orchestrator.add_agent(reviewer)
        self.orchestrator.add_agent(analyst)

        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}", required=True)
        )
        self.workflow.add_step(
            WorkflowStep(name="review", role="reviewer", task_template="Review: {previous_output}", required=False)
        )
        self.workflow.add_step(
            WorkflowStep(name="analysis", role="analyst", task_template="Analyze: {previous_output}", required=True)
        )

        result = self.workflow.run("Write code")

        self.assertFalse(result.success)
        self.assertEqual(len(result.step_results), 3)
        self.assertTrue(result.step_results[-1].success)

    def test_no_agent_for_role(self) -> None:
        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}")
        )

        result = self.workflow.run("Write code")

        self.assertFalse(result.success)
        self.assertIn("Role uygun ajan bulunamadı", result.errors[0])

    def test_empty_workflow(self) -> None:
        result = self.workflow.run("Write code")

        self.assertTrue(result.success)
        self.assertIsNone(result.final_output)
        self.assertEqual(result.step_results, ())

    def test_same_role_multiple_agents_uses_first(self) -> None:
        first = MockAgent(name="coder1", role="coder")
        second = MockAgent(name="coder2", role="coder")
        self.orchestrator.add_agent(first)
        self.orchestrator.add_agent(second)

        self.workflow.add_step(
            WorkflowStep(name="draft", role="coder", task_template="{task}")
        )

        result = self.workflow.run("Write code")

        self.assertEqual(result.step_results[0].agent_name, "coder1")


if __name__ == "__main__":
    unittest.main()
