import requests
import unittest

from core.ai.ollama_agent import OllamaAgent
from core.ai.orchestrator import MultiAIOrchestrator


class StubResponse:
    def __init__(self, payload: object, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if not 200 <= self.status_code < 300:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> object:
        return self.payload


class StubSession:
    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.last_request: dict[str, object] | None = None
        self.last_url: str | None = None

    def post(self, url: str, **kwargs: object) -> StubResponse:
        self.last_request = kwargs
        self.last_url = url
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response

    def get(self, url: str, **kwargs: object) -> StubResponse:
        response = self.responses[url]
        if isinstance(response, Exception):
            raise response
        return response


class OllamaAgentTests(unittest.TestCase):
    def test_successful_chat_response(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse(
                    {"message": {"content": "Hello from Ollama"}}
                )
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="researcher",
            model="llama-2",
            session=session,
        )

        result = agent.run("Generate summary")

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Hello from Ollama")
        self.assertIsNone(result.error)

    def test_task_and_context_passed(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse(
                    {"message": {"content": "Done"}}
                )
            }
        )

        context = {"topic": "finance"}
        agent = OllamaAgent(
            name="ollama1",
            role="analyst",
            model="llama-2",
            session=session,
        )

        result = agent.run("Analyze data", context=context)

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Done")
        self.assertEqual(context, {"topic": "finance"})

    def test_payload_includes_think_false(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse(
                    {"message": {"content": "Ready"}}
                )
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="assistant",
            model="llama-2",
            session=session,
        )

        result = agent.run("Prepare answer")

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Ready")
        self.assertIsNotNone(session.last_request)
        self.assertEqual(session.last_request["json"]["think"], False)

    def test_thinking_flag_ignored(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse(
                    {"message": {"content": "Final answer", "thinking": True}}
                )
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="assistant",
            model="llama-2",
            session=session,
        )

        result = agent.run("Ask question")

        self.assertTrue(result.success)
        self.assertEqual(result.output, "Final answer")

    def test_empty_model_name_returns_error(self) -> None:
        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="",
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("Model adı boş olamaz", result.error)

    def test_connection_error(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": requests.ConnectionError("refused")
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("refused", result.error)

    def test_timeout_error(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": requests.Timeout("timeout")
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("timeout", result.error)

    def test_http_error(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse(
                    {"message": {"content": "Hello"}}, status_code=500
                )
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("HTTP 500", result.error)

    def test_non_dict_response(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse("invalid")
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("geçerli JSON sözlüğü değil", result.error)

    def test_missing_message_field(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse({})
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("message alanı eksik", result.error)

    def test_missing_content_field(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse({"message": {}})
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("içerik yok", result.error)

    def test_empty_content(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse({"message": {"content": ""}})
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="coder",
            model="llama-2",
            session=session,
        )

        result = agent.run("Task")

        self.assertFalse(result.success)
        self.assertIn("içerik yok", result.error)

    def test_health_check_success(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/tags": StubResponse({"tags": []})
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="researcher",
            model="llama-2",
            session=session,
        )

        self.assertTrue(agent.health_check())

    def test_health_check_failure(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/tags": requests.ConnectionError("refused")
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="researcher",
            model="llama-2",
            session=session,
        )

        self.assertFalse(agent.health_check())

    def test_ollama_agent_with_orchestrator(self) -> None:
        session = StubSession(
            {
                "http://localhost:11434/api/chat": StubResponse(
                    {"message": {"content": "Orchestrated"}}
                )
            }
        )

        agent = OllamaAgent(
            name="ollama1",
            role="researcher",
            model="llama-2",
            session=session,
        )

        orchestrator = MultiAIOrchestrator()
        orchestrator.add_agent(agent)

        results = orchestrator.run_task("Run task")

        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].output, "Orchestrated")


if __name__ == "__main__":
    unittest.main()
