from __future__ import annotations

import unittest
from unittest.mock import patch

from core.ai.local_team import LocalAITeam
from core.ai.mock_agent import MockAgent


class LowMemoryLocalTeamTests(unittest.TestCase):
    def test_cpu_only_defaults_and_role_models(self):
        with patch.dict("os.environ", {"ANKA_OLLAMA_MODEL": ""}, clear=False):
            team = LocalAITeam()
        for name in team.roles:
            agent = team.orchestrator._agents[name]
            self.assertEqual(agent.num_gpu, 0)
            self.assertEqual(agent.num_ctx, 512)
            expected = "qwen2.5-coder:1.5b" if name == "coder" else "gemma3:1b"
            self.assertEqual(agent.model, expected)

    def test_explicit_override_remains_supported(self):
        team = LocalAITeam(model="qwen3:4b", num_gpu=None, num_ctx=2048)
        for name in team.roles:
            agent = team.orchestrator._agents[name]
            self.assertEqual(agent.model, "qwen3:4b")
            self.assertIsNone(agent.num_gpu)
            self.assertEqual(agent.num_ctx, 2048)

    def test_environment_model_overrides_all_roles(self):
        with patch.dict("os.environ", {"ANKA_OLLAMA_MODEL": "gemma3:4b"}):
            team = LocalAITeam()
        self.assertEqual(
            {team.orchestrator._agents[role].model for role in team.roles},
            {"gemma3:4b"},
        )

    def test_injected_agents_preserved(self):
        agents = {
            role: MockAgent(name=role, role=role)
            for role in ("researcher", "coder", "reviewer", "analyst")
        }
        team = LocalAITeam(agents=agents)
        self.assertEqual(set(team.orchestrator.list_agents()), set(agents))
        self.assertTrue(team.run("Read-only test").success)


if __name__ == "__main__":
    unittest.main()
