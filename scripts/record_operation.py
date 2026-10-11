"""ANKA Finans public, append-only operation journal (safe metadata only)."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
JOURNAL = ROOT / "docs" / "ANKA_OPERATIONS.jsonl"
STATUSES = {"PASS", "FAIL", "BLOCKED", "IN_PROGRESS"}
SENSITIVE = re.compile(
    r"(?i)(sk-proj-|gh[pousr]_[A-Za-z0-9]{12,}|AIza[A-Za-z0-9_-]{12,}"
    r"|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"
    r"|(?:authorization|x-api-key|api[_-]?key|password|passwd|secret|token)"
    r"\s*[:=]\s*\S+)"
)


def validate_field(name: str, value: str, limit: int = 480) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: nonempty text required")
    if len(value) > limit or "\n" in value or "\r" in value:
        raise ValueError(f"{name}: overlength or multiline")
    if SENSITIVE.search(value):
        raise ValueError(f"{name}: sensitive value pattern rejected")
    return value.strip()


@contextmanager
def journal_lock():
    # Single-writer lock for local concurrent agents. This lock is not committed.
    path = Path(tempfile.gettempdir()) / "anka_finans_journal.lock"
    with path.open("a+b") as f:
        if not f.tell() and path.stat().st_size == 0:
            f.write(b"0")
            f.flush()
        f.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            f.seek(0)
            if os.name == "nt":
                msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def append_event(*, actor: str, action: str, status: str, evidence: str,
                 next_step: str, rollback: str = "none", source: str = "agent",
                 journal: Path = JOURNAL) -> dict:
    if status not in STATUSES:
        raise ValueError("status must be PASS, FAIL, BLOCKED or IN_PROGRESS")
    record = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "id": str(uuid.uuid4()),
        "actor": validate_field("actor", actor, 80),
        "action": validate_field("action", action),
        "status": status,
        "evidence": validate_field("evidence", evidence),
        "next": validate_field("next", next_step),
        "rollback": validate_field("rollback", rollback),
        "source": validate_field("source", source, 80),
    }
    journal.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
    with journal_lock():
        with journal.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
    return record


def verify(journal: Path = JOURNAL) -> int:
    if not journal.is_file():
        raise ValueError("journal does not exist")
    ids = set()
    count = 0
    for number, raw in enumerate(journal.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        entry = json.loads(raw)
        for key in ("timestamp", "actor", "action", "status", "evidence", "next"):
            if key not in entry:
                raise ValueError(f"line {number}: missing {key}")
        if entry["status"] not in STATUSES:
            raise ValueError(f"line {number}: invalid status")
        if entry.get("id"):
            if entry["id"] in ids:
                raise ValueError(f"line {number}: duplicate id")
            ids.add(entry["id"])
        for key, value in entry.items():
            if isinstance(value, str) and SENSITIVE.search(value):
                raise ValueError(f"line {number}: sensitive pattern in {key}")
        count += 1
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--actor")
    parser.add_argument("--action")
    parser.add_argument("--status", choices=sorted(STATUSES))
    parser.add_argument("--evidence")
    parser.add_argument("--next", dest="next_step")
    parser.add_argument("--rollback", default="none")
    parser.add_argument("--source", default="agent")
    args = parser.parse_args()
    try:
        if args.verify:
            print("JOURNAL_VERIFY=PASS ROWS=" + str(verify()))
            return 0
        mandatory = (args.actor, args.action, args.status, args.evidence, args.next_step)
        if any(not x for x in mandatory):
            parser.error("--actor --action --status --evidence --next are mandatory")
        entry = append_event(
            actor=args.actor, action=args.action, status=args.status,
            evidence=args.evidence, next_step=args.next_step,
            rollback=args.rollback, source=args.source,
        )
        print("JOURNAL_RECORD=PASS ID=" + entry["id"])
        print("GIT_COMMIT_AND_PUSH_REQUIRED=true")
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("JOURNAL_RECORD=BLOCKED ERROR=" + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
