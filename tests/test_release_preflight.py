"""Deterministic tests; no child processes or real UI are launched."""

import importlib.util
import io
import subprocess
import sys
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_preflight.py"
_SPEC = importlib.util.spec_from_file_location("anka_release_preflight", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
preflight = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = preflight
_SPEC.loader.exec_module(preflight)


class ReleasePreflightTests(unittest.TestCase):
    def test_command_is_safe_and_offscreen(self):
        completed = subprocess.CompletedProcess([], 0, "ok", "")
        with patch.object(preflight.subprocess, "run", return_value=completed) as run:
            result = preflight.run_check("tests", "pass", Path("candidate"), 17)
        self.assertTrue(result.passed)
        args, kwargs = run.call_args
        self.assertEqual(args[0], [sys.executable, "-I", "-B", "-c", "pass"])
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 17)
        self.assertEqual(kwargs["env"]["QT_QPA_PLATFORM"], "offscreen")
        self.assertEqual(kwargs["env"]["PYTHONDONTWRITEBYTECODE"], "1")

    def test_nonzero_exit_fails(self):
        with patch.object(
            preflight.subprocess,
            "run",
            return_value=subprocess.CompletedProcess([], 1, "", "test failed"),
        ):
            result = preflight.run_check("tests", "pass", Path("candidate"), 1)
        self.assertFalse(result.passed)
        self.assertIn("test failed", result.detail)

    def test_timeout_and_launch_failure_fail(self):
        for error in (subprocess.TimeoutExpired("python", 1), OSError("unavailable")):
            with self.subTest(error=type(error).__name__):
                with patch.object(preflight.subprocess, "run", side_effect=error):
                    result = preflight.run_check("tests", "pass", Path("candidate"), 1)
                self.assertFalse(result.passed)

    def test_suite_runs_even_when_dependencies_fail(self):
        results = [
            preflight.CheckResult("dependencies", False, "missing"),
            preflight.CheckResult("unit tests", False, "failed"),
        ]
        with (
            patch.object(Path, "is_dir", return_value=True),
            patch.object(preflight, "staged_repository", return_value=nullcontext(Path("copy"))),
            patch.object(preflight, "run_check", side_effect=results) as check,
        ):
            self.assertEqual(preflight.run_preflight(Path("repository")), results)
        self.assertEqual(check.call_count, 2)
        self.assertEqual(check.call_args_list[1].args[1], preflight._TEST_CODE)

    def test_missing_suite_fails_without_subprocess(self):
        with (
            patch.object(Path, "is_dir", return_value=False),
            patch.object(preflight.subprocess, "run") as run,
        ):
            results = preflight.run_preflight(Path("missing"))
        self.assertFalse(results[0].passed)
        run.assert_not_called()

    def test_staging_failure_fails(self):
        with (
            patch.object(Path, "is_dir", return_value=True),
            patch.object(preflight, "staged_repository", side_effect=OSError("copy failed")),
        ):
            results = preflight.run_preflight(Path("repository"))
        self.assertFalse(results[0].passed)

    def test_default_and_explicit_mode_and_failure_exit(self):
        for argv in ([], ["--check-only"]):
            for passed in (True, False):
                with self.subTest(argv=argv, passed=passed):
                    results = [preflight.CheckResult("unit tests", passed, "detail")]
                    with (
                        patch.object(preflight, "run_preflight", return_value=results),
                        patch("sys.stdout", new_callable=io.StringIO) as output,
                    ):
                        status = preflight.main(argv)
                    self.assertEqual(status, 0 if passed else 1)
                    self.assertIn(
                        "OFFLINE CHECKS PASSED" if passed else "NOT READY", output.getvalue()
                    )

    def test_installer_mode_is_rejected(self):
        with (
            patch("sys.stderr", new_callable=io.StringIO),
            patch.object(preflight, "run_preflight") as run,
        ):
            with self.assertRaises(SystemExit) as raised:
                preflight.main(["--build"])
        self.assertEqual(raised.exception.code, 2)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
