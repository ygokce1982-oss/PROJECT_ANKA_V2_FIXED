"""Offline dependency and unittest preflight; never builds an installer."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

REQUIRED_MODULES = ("PySide6.QtWidgets", "requests")
DEPENDENCY_TIMEOUT = 60
TEST_TIMEOUT = 300

# Runs before importing application dependencies or discovering tests.
_BOOTSTRAP = r"""
import os
import sys
os.environ["QT_QPA_PLATFORM"] = "offscreen"
sys.dont_write_bytecode = True

def deny_external_activity(event, args):
    if event in {
        "socket.connect", "socket.bind", "socket.getaddrinfo",
        "socket.gethostbyname", "socket.gethostbyaddr", "socket.sendto",
        "socket.sendmsg", "subprocess.Popen", "os.system", "os.posix_spawn",
        "os.spawn", "os.exec", "os.startfile",
    }:
        raise RuntimeError("Offline preflight denied external activity: " + event)

sys.addaudithook(deny_external_activity)
sys.path.insert(0, os.getcwd())
"""
_DEPENDENCY_CODE = (
    _BOOTSTRAP
    + "\nimport importlib\n"
    + "\n".join(f"importlib.import_module({name!r})" for name in REQUIRED_MODULES)
)
_TEST_CODE = (
    _BOOTSTRAP
    + r"""
import unittest
suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
count = suite.countTestCases()
if count == 0:
    print("FAIL: no tests discovered", file=sys.stderr)
    sys.exit(2)
print("Discovered", count, "tests", flush=True)
result = unittest.TextTestRunner(verbosity=2).run(suite)
# Skips and expected failures require review; do not label them ready.
sys.exit(0 if result.wasSuccessful() and not result.skipped
         and not result.expectedFailures else 1)
"""
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


@contextmanager
def staged_repository(repository: Path) -> Iterator[Path]:
    """Run against a disposable copy so ordinary relative writes stay isolated."""
    with tempfile.TemporaryDirectory(prefix="anka-release-preflight-") as directory:
        staged = Path(directory) / "candidate"
        shutil.copytree(
            repository,
            staged,
            symlinks=True,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                "venv",
                "__pycache__",
                "*.pyc",
                ".pytest_cache",
                "build",
                "dist",
                ".env",
                ".env.*",
            ),
        )
        # Do not retain links that could lead writes outside the disposable tree.
        for path in staged.rglob("*"):
            if path.is_symlink() or path.is_junction():
                raise ValueError(f"Linked paths are unsupported: {path.relative_to(staged)}")
        yield staged


def run_check(name: str, code: str, directory: Path, timeout: int) -> CheckResult:
    environment = os.environ.copy()
    environment["QT_QPA_PLATFORM"] = "offscreen"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["TMP"] = str(directory.parent)
    environment["TEMP"] = str(directory.parent)
    environment["TMPDIR"] = str(directory.parent)
    try:
        completed = subprocess.run(
            [sys.executable, "-I", "-B", "-c", code],
            cwd=directory,
            env=environment,
            shell=False,
            timeout=timeout,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(name, False, f"Timed out after {timeout} seconds")
    except OSError as error:
        return CheckResult(name, False, f"Could not start check: {error}")
    output = "\n".join(
        part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
    )
    return CheckResult(
        name,
        completed.returncode == 0,
        f"Exit code: {completed.returncode}\n{output}".strip(),
    )


def run_preflight(repository: Path) -> list[CheckResult]:
    if not (repository / "tests").is_dir():
        return [CheckResult("repository", False, "Missing tests directory")]
    try:
        with staged_repository(repository) as staged:
            # Attempt both checks, including the suite when imports fail.
            return [
                run_check("dependencies", _DEPENDENCY_CODE, staged, DEPENDENCY_TIMEOUT),
                run_check("unit tests", _TEST_CODE, staged, TEST_TIMEOUT),
            ]
    except (OSError, ValueError, shutil.Error) as error:
        return [CheckResult("staging", False, str(error))]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only",
        action="store_true",
        default=True,
        help="Run checks only (default and only supported mode)",
    )
    parser.parse_args(argv)
    repository = Path(__file__).resolve().parents[1]
    results = run_preflight(repository)
    for result in results:
        print(f"{'PASS' if result.passed else 'FAIL'}: {result.name}")
        print(result.detail)
    passed = bool(results) and all(result.passed for result in results)
    if passed:
        print("OFFLINE CHECKS PASSED. Release readiness requires independent review.")
    else:
        print("NOT READY: offline preflight failed.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
