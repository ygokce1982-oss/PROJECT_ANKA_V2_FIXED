"""Resource choices must reach Ollama without altering existing defaults."""
import unittest

from core.ai.ollama_agent import OllamaAgent
from tests.test_ollama_agent import StubResponse, StubSession


class OllamaResourceTests(unittest.TestCase):
    def test_explicit_cpu_and_context_are_forwarded(self):
        session = StubSession({"http://localhost:11434/api/chat": StubResponse(
            {"message": {"content": "OK"}})})
        agent = OllamaAgent("helper", "reviewer", "gemma3:1b", session=session,
                            num_ctx=512, num_gpu=0)
        self.assertTrue(agent.run("Reply OK").success)
        self.assertEqual(session.last_request["json"]["options"]["num_gpu"], 0)
        self.assertEqual(session.last_request["json"]["options"]["num_ctx"], 512)

    def test_invalid_resource_settings_fail_before_session_call(self):
        for options in ({"num_gpu": -1}, {"num_gpu": True}, {"num_ctx": 0}, {"num_ctx": 1.5}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                OllamaAgent("helper", "reviewer", "gemma3:1b", **options)
