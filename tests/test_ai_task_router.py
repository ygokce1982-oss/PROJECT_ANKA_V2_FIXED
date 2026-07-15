import unittest

from core.ai.task_router import AITaskRouter, TaskRoute


class AITaskRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = AITaskRouter()

    def test_empty_task_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.router.route("")

    def test_coder_routing(self) -> None:
        route = self.router.route("Kod yazma görevi")
        self.assertEqual(route.role, "coder")
        self.assertGreaterEqual(route.confidence, 0.0)
        self.assertLessEqual(route.confidence, 1.0)
        self.assertTrue(route.reason.startswith("Görev metni 'coder'"))

    def test_reviewer_routing(self) -> None:
        route = self.router.route("Güvenlik kontrolü yap")
        self.assertEqual(route.role, "reviewer")
        self.assertIn("reviewer", route.role)

    def test_researcher_routing(self) -> None:
        route = self.router.route("Kaynak araştırması yap")
        self.assertEqual(route.role, "researcher")
        self.assertIn("research", route.reason)

    def test_analyst_routing(self) -> None:
        route = self.router.route("Risk değerlendirmesi hazırla")
        self.assertEqual(route.role, "analyst")
        self.assertIn("analyst", route.role)

    def test_default_role_when_no_match(self) -> None:
        route = self.router.route("Bir görev tanımı")
        self.assertEqual(route.role, "analyst")
        self.assertEqual(route.confidence, 0.6)

    def test_valid_preferred_role_used(self) -> None:
        route = self.router.route("Herhangi bir görev", preferred_role="reviewer")
        self.assertEqual(route.role, "reviewer")
        self.assertEqual(route.confidence, 0.9)

    def test_invalid_preferred_role_ignored(self) -> None:
        route = self.router.route("Herhangi bir görev", preferred_role="invalid")
        self.assertEqual(route.role, "analyst")
        self.assertEqual(route.confidence, 0.6)

    def test_confidence_bounds(self) -> None:
        route = self.router.route("Finansal analiz yap")
        self.assertGreaterEqual(route.confidence, 0.0)
        self.assertLessEqual(route.confidence, 1.0)

    def test_turkish_case_insensitive_routing(self) -> None:
        route = self.router.route("İNCELEME raporu hazırla")
        self.assertEqual(route.role, "reviewer")

    def test_preferred_role_case_insensitive(self) -> None:
        route = self.router.route("Herhangi bir görev", preferred_role="Coder")
        self.assertEqual(route.role, "coder")


if __name__ == "__main__":
    unittest.main()
