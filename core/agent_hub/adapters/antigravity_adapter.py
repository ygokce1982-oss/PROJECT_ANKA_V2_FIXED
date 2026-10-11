"""Antigravity CLI integration for ANKA planning and independent review.

Calls Gemini/Claude via authenticated `agy` CLI. Default plan mode cannot
change project files, run orders or bypass permissions; code edit orchestration
needs a separate tested approval and rollback gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

from .base_adapter import BaseAdapter
from .codex_adapter import _stop_process_tree


@dataclass(frozen=True)
class AntigravityResult:
    success: bool
    output: str | None = None
    error: str | None = None


DEFAULT_MODELS = {
    "planner": "gemini-3.8-flash-low",
    "researcher": "gemini-3.8-flash-low",
    "analyst": "gemini-3.8-flash-low",
    "developer": "gemini-3.8-flash-medium",
    "reviewer": "claude-sonnet-4-6",
}


class AntigravityAdapter(BaseAdapter):
    def __init__(
        self, name: str, role: str, *,
        workspace: str | Path | None = None,
        model: str | None = None,
        timeout_seconds: float = 75,
        executable: str = "agy",
    ) -> None:
        super().__init__(name, role)
        if not 5 <= timeout_seconds <= 300:
            raise ValueError("timeout_seconds outside 5..300")
        self.workspace = Path(workspace).resolve() if workspace is not None else None
        self.model = model or DEFAULT_MODELS.get(role, "gemini-3.8-flash-low")
        if not self.model or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.:" for c in self.model):
            raise ValueError("invalid model")
        self.timeout_seconds = float(timeout_seconds)
        self.executable = executable

    def health_check(self) -> bool:
        return shutil.which(self.executable) is not None and (
            self.workspace is not None and self.workspace.is_dir()
        )

    @staticmethod
    def _minimal_environment() -> dict[str, str]:
        allowed = (
            "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
            "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA",
            "LOCALAPPDATA", "TEMP", "TMP", "HOME", "LANG",
        )
        env = {name: os.environ[name] for name in allowed if name in os.environ}
        env["GIT_TERMINAL_PROMPT"] = "0"
        return env

    def run(self, task: str, **kwargs: object) -> AntigravityResult:
        if kwargs or not isinstance(task, str) or not task.strip() or len(task) > 12000:
            return AntigravityResult(False, error="Validation failed: invalid task")
        if not self.health_check():
            return AntigravityResult(False, error="Adapter unavailable: CLI or workspace missing")
        if not (self.workspace / ".git").exists():
            return AntigravityResult(False, error="Validation failed: isolated worktree required")
        binary = shutil.which(self.executable)
        if not binary:
            return AntigravityResult(False, error="Adapter unavailable: CLI missing")
        command = [
            binary, "--mode=plan", f"--model={self.model}",
            f"--print-timeout={int(self.timeout_seconds)}s", "--print", task,
        ]
        flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if os.name == "nt" else 0
        )
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=str(self.workspace), shell=False,
                text=True, encoding="utf-8", errors="replace",
                env=self._minimal_environment(), creationflags=flags,
            )
        except OSError:
            return AntigravityResult(False, error="Adapter unavailable: CLI launch failed")
        try:
            output, _stderr = process.communicate(timeout=self.timeout_seconds + 10)
        except subprocess.TimeoutExpired:
            _stop_process_tree(process)
            return AntigravityResult(False, error="Antigravity execution timed out")
        except OSError:
            _stop_process_tree(process)
            return AntigravityResult(False, error="Antigravity subprocess I/O failed")
        if process.returncode:
            return AntigravityResult(False, error=f"Antigravity CLI failed: exit {process.returncode}")
        content = (output or "").strip()
        if not content:
            return AntigravityResult(False, error="Antigravity CLI returned empty output")
        return AntigravityResult(True, output=content[-16000:])
