"""Explicit live Codex read-only smoke test, never a production acceptance."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.agent_hub.adapters.codex_adapter import CodexAdapter

root = Path(__file__).resolve().parents[1]
adapter = CodexAdapter("codex-review", "reviewer", workspace=root, timeout_seconds=75)
print("CLI_PRESENT=" + str(adapter.health_check()), flush=True)
result = adapter.run(
    "In one brief Turkish sentence, describe the purpose of ANKA Finans, a stock-market monitoring application. Do not edit files."
)
print("LIVE_SUCCESS=" + str(result.success), flush=True)
print("LIVE_ERROR=" + str(result.error), flush=True)
print("LIVE_OUTPUT_CHARS=" + str(len(result.output or "")), flush=True)
if result.output:
    print("LIVE_LAST_LINE=" + result.output.strip().splitlines()[-1][:600], flush=True)
raise SystemExit(0 if result.success else 2)
