"""CPU-only mode must be opt-in and must reach local Ollama agents."""

import unittest

from core.agent_hub.adapters.ollama_adapter import OllamaAdapter
from scripts.anka_team import ROLE_MODELS, build_registry


class OllamaCpuTeamTests(unittest.TestCase):
    def test_adapter_can_request_cpu_only(self):
        adapter = OllamaAdapter("test", "reviewer", model="gemma3:1b", num_gpu=0)
        self.assertEqual(adapter.agent.num_gpu, 0)

    def test_adapter_default_is_unchanged(self):
        adapter = OllamaAdapter("test", "reviewer", model="gemma3:1b")
        self.assertIsNone(adapter.agent.num_gpu)

    def test_local_team_cpu_only_option_reaches_each_role(self):
        registry = build_registry("http://127.0.0.1:11434", cpu_only=True)
        self.assertEqual(registry.list_agents(), [f"local-{role}" for role in ROLE_MODELS])
        for role in ROLE_MODELS:
            with self.subTest(role=role):
                self.assertEqual(registry.get_agent(f"local-{role}").agent.num_gpu, 0)

    def test_local_team_default_remains_unspecified(self):
        registry = build_registry("http://127.0.0.1:11434")
        for role in ROLE_MODELS:
            with self.subTest(role=role):
                self.assertIsNone(registry.get_agent(f"local-{role}").agent.num_gpu)


if __name__ == "__main__":
    unittest.main()
