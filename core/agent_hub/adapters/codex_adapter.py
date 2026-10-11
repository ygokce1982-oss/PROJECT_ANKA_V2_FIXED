"""Bounded Codex CLI adapter; rejects unverified execution as acceptance.

Windows timeout handling kills the CMD wrapper *and* descendant model/Node
processes. Each role still requires deterministic tests and independent review.
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


def _stop_process_tree(process: subprocess.Popen[str]) -> None:
    """Bounded best-effort cleanup after timeout. Never kill unrelated PIDs."""
    if os.name == "nt" and getattr(process, "pid", None):
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                shell=False, check=False, capture_output=True,
                timeout=8,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass
    try:
        process.communicate(timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        pass


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
        """Installed executable is not proof of successful login."""
        return shutil.which(self.executable) is not None and (
            self.workspace is None or self.workspace.is_dir()
        )

    @staticmethod
    def _minimal_environment() -> dict[str, str]:
        """No automatic forwarding of API keys / provider secrets."""
        allowed = (
            "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC",
            "USERPROFILE", "HOMEDRIVE", "HOMEPATH", "APPDATA",
            "LOCALAPPDATA", "TEMP", "TMP", "HOME", "LANG",
        )
        value = {key: os.environ[key] for key in allowed if key in os.environ}
        value["GIT_TERMINAL_PROMPT"] = "0"
        return value

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
        resolved = shutil.which(self.executable)
        if not resolved:
            return CodexRunResult(False, error="Adapter unavailable: CLI not found")
        command = [
            resolved, "exec", "--sandbox",
            "workspace-write" if self.allow_writes else "read-only",
            "--cd", str(self.workspace), "-",
        ]
        flags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            if os.name == "nt" else 0
        )
        try:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
                errors="replace", shell=False, cwd=str(self.workspace),
                env=self._minimal_environment(), creationflags=flags,
            )
        except OSError:
            return CodexRunResult(False, error="Adapter unavailable: failed to start CLI")
        try:
            output, _stderr = process.communicate(input=task, timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired:
            _stop_process_tree(process)
            return CodexRunResult(False, error="Agent execution timed out; process tree terminated")
        except OSError:
            _stop_process_tree(process)
            return CodexRunResult(False, error="Agent execution failed during subprocess I/O")
        if process.returncode:
            return CodexRunResult(False, error=f"Codex CLI failed: exit {process.returncode}")
        content = (output or "").strip()
        if not content:
            return CodexRunResult(False, error="Codex CLI returned no result")
        return CodexRunResult(True, output=content[-16000:])
