"""Explicit, bounded Codex CLI integration for isolated ANKA tasks.

Installing a CLI is not proof of account access or task success.
No finance orders, provider credentials, approvals, or Git publishing here.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

from .base_adapter import BaseAdapter


@dataclass(frozen=True)
class CodexRunResult:
    success: bool
    output: str | None = None
    error: str | None = None


class CodexAdapter(BaseAdapter):
    def __init__(
        self, name: str, role: str, *,
        workspace: str | Path | None = None,
        timeout_seconds: float = 120,
        allow_writes: bool = False,
        executable: str = "codex",
    ) -> None:
        super().__init__(name, role)
        if not 5 <= timeout_seconds <= 900:
            raise ValueError("timeout_seconds must be between 5 and 900")
        self.workspace = Path(workspace).resolve() if workspace is not None else None
        self.timeout_seconds = float(timeout_seconds)
        self.allow_writes = bool(allow_writes)
        self.executable = executable

    def health_check(self) -> bool:
        # A functioning CLI/login is checked by a separate live test gate.
        return shutil.which(self.executable) is not None and (
            self.workspace is None or self.workspace.is_dir()
        )

    @staticmethod
    def _minimal_environment() -> dict[str, str]:
        """Avoid forwarding provider keys from the parent process."""
        allow = (
            "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
            "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA",
            "LOCALAPPDATA", "TEMP", "TMP", "HOME", "LANG",
        )
        result = {key: os.environ[key] for key in allow if key in os.environ}
        result["GIT_TERMINAL_PROMPT"] = "0"
        return result

    def run(self, task: str, **kwargs: object) -> CodexRunResult:
        if not isinstance(task, str) or not task.strip() or len(task) > 12000:
            return CodexRunResult(False, error="Validation failed: invalid prompt")
        if kwargs:
            return CodexRunResult(False, error="Validation failed: unsupported options")
        if not self.health_check():
            return CodexRunResult(False, error="Adapter unavailable: CLI or workspace missing")
        if self.workspace is None:
            return CodexRunResult(False, error="Not configured: isolated workspace required")
        if not (self.workspace / ".git").exists():
            return CodexRunResult(False, error="Validation failed: workspace must be a Git worktree")

        sandbox = "workspace-write" if self.allow_writes else "read-only"
        resolved = shutil.which(self.executable)
        if resolved is None:
            return CodexRunResult(False, error="Adapter unavailable: CLI not found")
        command = [
            resolved, "exec", "--sandbox", sandbox,
            "--cd", str(self.workspace), "-",
        ]
        try:
            completed = subprocess.run(
                command, input=task, text=True, capture_output=True,
                encoding="utf-8", errors="replace", check=False,
                timeout=self.timeout_seconds, cwd=str(self.workspace),
                env=self._minimal_environment(),
            )
        except subprocess.TimeoutExpired:
            return CodexRunResult(False, error="Agent execution timed out")
        except OSError:
            return CodexRunResult(False, error="Adapter unavailable: failed to start CLI")

        if completed.returncode:
            return CodexRunResult(False, error=f"Codex CLI failed: exit {completed.returncode}")
        content = (completed.stdout or "").strip()
        if not content:
            return CodexRunResult(False, error="Codex CLI returned no result")
        return CodexRunResult(True, output=content[-16000:])
