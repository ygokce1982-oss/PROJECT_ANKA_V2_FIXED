import os
import unittest

from core.ai.local_team import LocalAITeam
from core.ai.mock_agent import MockAgent


class LocalTeamTests(unittest.TestCase):
    def test_four_roles_created(self) -> None:
        agents = {
            "researcher": MockAgent(name="researcher1", role="researcher"),
            "coder": MockAgent(name="coder1", role="coder"),
            "reviewer": MockAgent(name="reviewer1", role="reviewer"),
            "analyst": MockAgent(name="analyst1", role="analyst"),
        }

        team = LocalAITeam(agents=agents)
        self.assertEqual(set(team.orchestrator.list_agents()), set(agents.keys()))

    def test_env_model_and_base_url(self) -> None:
        os.environ["ANKA_OLLAMA_MODEL"] = "test-model"
        os.environ["ANKA_OLLAMA_URL"] = "http://example.local"

        agents = {r: MockAgent(name=r, role=r) for r in ["researcher", "coder", "reviewer", "analyst"]}
        team = LocalAITeam(agents=agents)

        self.assertEqual(team.model, "test-model")
        self.assertEqual(team.base_url, "http://example.local")

        os.environ.pop("ANKA_OLLAMA_MODEL", None)
        os.environ.pop("ANKA_OLLAMA_URL", None)

    def test_successful_workflow(self) -> None:
        agents = {
            "researcher": MockAgent(name="researcher1", role="researcher"),
            "coder": MockAgent(name="coder1", role="coder"),
            "reviewer": MockAgent(name="reviewer1", role="reviewer"),
            "analyst": MockAgent(name="analyst1", role="analyst"),
        }
        team = LocalAITeam(agents=agents)

        result = team.run("Implement feature")
        self.assertTrue(result.success)
        # final output should be produced by last agent
        self.assertIsNotNone(result.final_output)
        self.assertIn("Görevi sadece Türkçe, kısa ve somut yanıtla", team.workflow.steps[0].task_template)
        self.assertIn("Kullanıcıdan ek bilgi isteme", team.workflow.steps[0].task_template)
        self.assertIn("Ek soru sorma", team.workflow.steps[2].task_template)
        self.assertIn("Takip sorusu veya seçenek teklifiyle bitir", team.workflow.steps[3].task_template)

    def test_ollama_unreachable_returns_safe_error(self) -> None:
        class BadAgent(MockAgent):
            def health_check(self):
                return False

        agents = {r: BadAgent(name=r, role=r) for r in ["researcher", "coder", "reviewer", "analyst"]}
        team = LocalAITeam(agents=agents)

        res = team.run("Task")
        self.assertFalse(res.success)
        self.assertIn("Ollama servisine ulaşılamıyor", res.errors[0])

    def test_context_not_mutated(self) -> None:
        agents = {r: MockAgent(name=r, role=r) for r in ["researcher", "coder", "reviewer", "analyst"]}
        team = LocalAITeam(agents=agents)

        context = {"topic": "health"}
        _ = team.run("Task", context=context)
        self.assertEqual(context, {"topic": "health"})

    def test_result_ordering_and_empty_task(self) -> None:
        agents = {r: MockAgent(name=r, role=r) for r in ["researcher", "coder", "reviewer", "analyst"]}
        team = LocalAITeam(agents=agents)

        # empty task
        res = team.run("")
        self.assertFalse(res.success)

        # ordering
        res = team.run("Do work")
        names = [sr.agent_name for sr in res.step_results]
        self.assertEqual(names, ["researcher", "coder", "reviewer", "analyst"])


if __name__ == "__main__":
    unittest.main()
