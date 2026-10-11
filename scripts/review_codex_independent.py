"""Separate, read-only reviewer pass for CodexAdapter changes."""
from pathlib import Path
import json
from datetime import datetime, timezone
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.agent_hub.adapters.codex_adapter import CodexAdapter

root = Path(__file__).resolve().parents[1]
reviewer = CodexAdapter("independent-reviewer", "reviewer", workspace=root, timeout_seconds=90)
request = ("Perform an independent read-only Python code review of "
           "core/agent_hub/adapters/codex_adapter.py and tests/test_codex_adapter.py. "
           "Evaluate Windows .cmd invocation, subprocess arguments, process timeouts, "
           "unintended filesystem writes and whether success is overstated. "
           "Give concrete findings and severity. Do not modify files. "
           "Do not claim production acceptance.")
result = reviewer.run(request)
report = {
    "time": datetime.now(timezone.utc).isoformat(),
    "reviewer": "codex-independent-read-only-run",
    "success": result.success,
    "review": (result.output or "")[-6000:],
    "error": result.error,
    "human_review": False,
    "production_pass": False,
}
out = root / "reports/codex_independent_review.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("INDEPENDENT_AGENT_SUCCESS=" + str(result.success), flush=True)
print("REVIEW_CHARS=" + str(len(result.output or "")), flush=True)
print("REVIEW_PREVIEW=" + (result.output or "")[-900:], flush=True)
print("REVIEW_ERROR=" + str(result.error), flush=True)
raise SystemExit(0 if result.success else 2)
