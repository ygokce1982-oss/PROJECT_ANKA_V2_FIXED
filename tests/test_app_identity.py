"""Regression gate for ANKA Finans application identity, no GUI or network."""
import ast
from pathlib import Path
import unittest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class AppIdentityTests(unittest.TestCase):
    def test_actual_qapplication_name_is_anka_finans(self):
        tree = ast.parse(APP_PATH.read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "app"
            and node.func.attr == "setApplicationName"
        ]
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(calls[0].args), 1)
        self.assertIsInstance(calls[0].args[0], ast.Constant)
        self.assertEqual(calls[0].args[0].value, "ANKA Finans")

    def test_old_identity_not_present(self):
        self.assertNotIn("PROJECT ANKA V2", APP_PATH.read_text(encoding="utf-8"))
