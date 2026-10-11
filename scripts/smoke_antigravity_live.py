"""Real but read-only Antigravity/Gemini+Claude acceptance probe."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.agent_hub.adapters.antigravity_adapter import AntigravityAdapter

gates = [
    ("planner", "ANKA_GEMINI_GATE_OK"),
    ("reviewer", "ANKA_CLAUDE_GATE_OK"),
]
results = []
for role, expected in gates:
    adapter = AntigravityAdapter(
        name="anka-" + role, role=role, workspace=ROOT, timeout_seconds=48,
    )
    result = adapter.run("Reply with exactly " + expected + ". Do not use tools or files.")
    relevant = bool(result.success and expected in (result.output or ""))
    print("AGY_" + role.upper() + "_SUCCESS=" + str(relevant), flush=True)
    print("AGY_" + role.upper() + "_RESPONSE_CHARS=" + str(len(result.output or "")), flush=True)
    if result.error:
        print("AGY_" + role.upper() + "_ERROR=" + result.error, flush=True)
    results.append({
        "role": role,
        "model": adapter.model,
        "command_success": result.success,
        "expected_marker_present": relevant,
        "output_length": len(result.output or ""),
        "error": result.error,
    })
    if not relevant:
        break
report = {
    "time": datetime.now(timezone.utc).isoformat(),
    "results": results,
    "model_connectivity_pass": len(results) == 2 and all(x["expected_marker_present"] for x in results),
    "full_autonomy_pass": False,
    "financial_orders_enabled": False,
}
out = ROOT / "docs/ANKA_ANTIGRAVITY_CONNECTIVITY_20261011.json"
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("AGY_FINAL_PASS=" + str(report["model_connectivity_pass"]), flush=True)
raise SystemExit(0 if report["model_connectivity_pass"] else 2)
