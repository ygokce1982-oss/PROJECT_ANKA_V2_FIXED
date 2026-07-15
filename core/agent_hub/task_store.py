from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Any

from .models import TaskRecord, TaskStatus


class TaskStore:
    DB_FILENAME = "agent_hub.db"

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, "data", self.DB_FILENAME)
        self._ensure_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _ensure_database(self) -> None:
        folder = Path(self.db_path).parent
        folder.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
                """
            )
            
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    role TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result TEXT,
                    error TEXT,
                    requires_approval INTEGER NOT NULL,
                    locked_by TEXT,
                    locked_at TEXT,
                    lease_expires_at TEXT,
                    next_run_at TEXT,
                    approved_by TEXT,
                    approved_at TEXT,
                    approval_reason TEXT
                )
                """
            )
            
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_approvals (
                    task_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    note TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(task_id) REFERENCES tasks(id)
                )
                """
            )
            
            conn.execute("CREATE INDEX IF NOT EXISTS ix_tasks_status ON tasks(status);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_tasks_role ON tasks(role);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_tasks_priority ON tasks(priority);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_tasks_created_at ON tasks(created_at);")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_tasks_next_run_at ON tasks(next_run_at);")
            
            cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
            row = cursor.fetchone()
            version = row[0] if row else 0
            
            if version < 2:
                cursor = conn.execute("PRAGMA table_info(tasks)")
                columns = [r[1] for r in cursor.fetchall()]
                
                new_columns = {
                    "locked_by": "TEXT",
                    "locked_at": "TEXT",
                    "lease_expires_at": "TEXT",
                    "next_run_at": "TEXT",
                    "approved_by": "TEXT",
                    "approved_at": "TEXT",
                    "approval_reason": "TEXT"
                }
                for col, col_type in new_columns.items():
                    if col not in columns:
                        conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {col_type}")
                
                if version == 0:
                    conn.execute("INSERT INTO schema_version (version) VALUES (2)")
                else:
                    conn.execute("UPDATE schema_version SET version = 2")
            
            conn.commit()
        finally:
            conn.close()

    def add_task(
        self,
        title: str,
        description: str,
        role: str,
        priority: int = 100,
        max_attempts: int = 3,
        requires_approval: bool = False,
    ) -> TaskRecord:
        now = datetime.utcnow().isoformat()
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    title, description, role, priority, status, attempts, max_attempts, 
                    created_at, updated_at, requires_approval
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, description, role, priority, TaskStatus.QUEUED.value, 0, max_attempts, now, now, int(requires_approval)),
            )
            conn.commit()
            task_id = cursor.lastrowid
            return self.get_task(task_id)
        finally:
            conn.close()

    def get_task(self, task_id: int) -> TaskRecord:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            row = cursor.fetchone()
            if row is None:
                raise KeyError(f"Task not found: {task_id}")
            return self._row_to_task(row)
        finally:
            conn.close()

    def list_tasks(self, statuses: Iterable[TaskStatus] | None = None) -> list[TaskRecord]:
        conn = self._get_connection()
        try:
            if statuses is None:
                cursor = conn.execute("SELECT * FROM tasks ORDER BY priority DESC, created_at ASC")
            else:
                placeholders = ",".join("?" for _ in statuses)
                cursor = conn.execute(
                    f"SELECT * FROM tasks WHERE status IN ({placeholders}) ORDER BY priority DESC, created_at ASC",
                    tuple(status.value for status in statuses),
                )
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]
        finally:
            conn.close()

    def update_task(
        self,
        task_id: int,
        status: TaskStatus | None = None,
        attempts: int | None = None,
        result: str | None = None,
        error: str | None = None,
        requires_approval: bool | None = None,
        locked_by: str | None = None,
        locked_at: datetime | None = None,
        lease_expires_at: datetime | None = None,
        next_run_at: datetime | None = None,
        approved_by: str | None = None,
        approved_at: datetime | None = None,
        approval_reason: str | None = None,
        clear_lock: bool = False,
    ) -> TaskRecord:
        task = self.get_task(task_id)
        updated_at = datetime.utcnow().isoformat()
        
        new_status = status.value if status is not None else task.status.value
        new_attempts = attempts if attempts is not None else task.attempts
        new_result = result if result is not None else task.result
        new_error = error if error is not None else task.error
        new_requires_approval = int(requires_approval) if requires_approval is not None else int(task.requires_approval)
        
        new_locked_by = None if clear_lock else (locked_by if locked_by is not None else task.locked_by)
        new_locked_at = None if clear_lock else (locked_at.isoformat() if locked_at is not None else (task.locked_at.isoformat() if task.locked_at else None))
        new_lease_expires_at = None if clear_lock else (lease_expires_at.isoformat() if lease_expires_at is not None else (task.lease_expires_at.isoformat() if task.lease_expires_at else None))
        new_next_run_at = next_run_at.isoformat() if next_run_at is not None else (task.next_run_at.isoformat() if task.next_run_at else None)
        new_approved_by = approved_by if approved_by is not None else task.approved_by
        new_approved_at = approved_at.isoformat() if approved_at is not None else (task.approved_at.isoformat() if task.approved_at else None)
        new_approval_reason = approval_reason if approval_reason is not None else task.approval_reason

        conn = self._get_connection()
        try:
            conn.execute(
                """
                UPDATE tasks SET 
                    status = ?, 
                    attempts = ?, 
                    result = ?, 
                    error = ?, 
                    requires_approval = ?, 
                    locked_by = ?,
                    locked_at = ?, 
                    lease_expires_at = ?,
                    next_run_at = ?, 
                    approved_by = ?, 
                    approved_at = ?, 
                    approval_reason = ?, 
                    updated_at = ? 
                WHERE id = ?
                """,
                (
                    new_status,
                    new_attempts,
                    new_result,
                    new_error,
                    new_requires_approval,
                    new_locked_by,
                    new_locked_at,
                    new_lease_expires_at,
                    new_next_run_at,
                    new_approved_by,
                    new_approved_at,
                    new_approval_reason,
                    updated_at,
                    task_id,
                ),
            )
            conn.commit()
            return self.get_task(task_id)
        finally:
            conn.close()

    def claim_next_task(self, worker_id: str, lease_seconds: int = 300) -> TaskRecord | None:
        conn = self._get_connection()
        try:
            conn.execute("BEGIN IMMEDIATE")
            now_dt = datetime.utcnow()
            now_iso = now_dt.isoformat()
            lease_expires = (now_dt + timedelta(seconds=lease_seconds)).isoformat()
            
            cursor = conn.execute(
                """
                SELECT * FROM tasks 
                WHERE status = ? AND (next_run_at IS NULL OR next_run_at <= ?)
                ORDER BY priority DESC, created_at ASC 
                LIMIT 1
                """,
                (TaskStatus.QUEUED.value, now_iso),
            )
            row = cursor.fetchone()
            if row:
                task_id = row["id"]
                conn.execute(
                    """
                    UPDATE tasks SET 
                        status = ?, 
                        locked_by = ?, 
                        locked_at = ?, 
                        lease_expires_at = ?, 
                        updated_at = ? 
                    WHERE id = ?
                    """,
                    (TaskStatus.RUNNING.value, worker_id, now_iso, lease_expires, now_iso, task_id),
                )
                conn.commit()
                
                cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
                updated_row = cursor.fetchone()
                return self._row_to_task(updated_row)
            else:
                conn.commit()
                return None
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def lock_next_task(self) -> TaskRecord | None:
        return self.claim_next_task("scheduler-default", lease_seconds=300)

    def recover_expired_tasks(self, now: datetime | None = None) -> list[int]:
        conn = self._get_connection()
        recovered_ids = []
        try:
            conn.execute("BEGIN IMMEDIATE")
            
            if now is None:
                now_dt = datetime.utcnow()
            else:
                if now.tzinfo is not None:
                    now_dt = now.astimezone(timezone.utc).replace(tzinfo=None)
                else:
                    now_dt = now

            now_iso = now_dt.isoformat()
            
            cursor = conn.execute("SELECT * FROM tasks WHERE status = ?", (TaskStatus.RUNNING.value,))
            rows = cursor.fetchall()
            for row in rows:
                task_id = row["id"]
                lease_expires_at_str = row["lease_expires_at"]
                attempts = row["attempts"]
                max_attempts = row["max_attempts"]
                
                expired = False
                if lease_expires_at_str:
                    lease_dt = self._parse_iso_to_utc_naive(lease_expires_at_str)
                    if lease_dt and lease_dt < now_dt:
                        expired = True
                
                if expired:
                    new_attempts = attempts + 1
                    if new_attempts < max_attempts:
                        backoff = 2 ** new_attempts
                        next_run = (now_dt + timedelta(seconds=backoff)).isoformat()
                        conn.execute(
                            """
                            UPDATE tasks 
                            SET status = ?, attempts = ?, locked_by = NULL, locked_at = NULL, 
                                lease_expires_at = NULL, next_run_at = ?, error = ?, updated_at = ? 
                            WHERE id = ?
                            """,
                            (TaskStatus.QUEUED.value, new_attempts, next_run, "Lease expired, retrying", now_iso, task_id),
                        )
                    else:
                        conn.execute(
                            """
                            UPDATE tasks 
                            SET status = ?, attempts = ?, locked_by = NULL, locked_at = NULL, 
                                lease_expires_at = NULL, error = ?, updated_at = ? 
                            WHERE id = ?
                            """,
                            (TaskStatus.FAILED.value, new_attempts, "Lease expired, max attempts reached", now_iso, task_id),
                        )
                    recovered_ids.append(task_id)
            conn.commit()
            return recovered_ids
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def recover_expired_leases(self, lease_duration_seconds: int = 300) -> list[int]:
        # Maintain compatibility for internal calls, delegates to recover_expired_tasks
        return self.recover_expired_tasks()

    def record_approval_action(self, task_id: int, action: str, user_id: str, note: str | None = None) -> None:
        conn = self._get_connection()
        try:
            now = datetime.utcnow().isoformat()
            conn.execute(
                """
                INSERT INTO task_approvals (task_id, action, user_id, note, timestamp) 
                VALUES (?, ?, ?, ?, ?)
                """,
                (task_id, action, user_id, note, now),
            )
            conn.commit()
        finally:
            conn.close()

    def get_approval_audit(self, task_id: int) -> list[tuple[str, str, str | None, str]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT action, user_id, note, timestamp FROM task_approvals WHERE task_id = ? ORDER BY timestamp ASC",
                (task_id,)
            )
            return [tuple(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def _parse_iso_to_utc_naive(self, val: str) -> datetime | None:
        val_clean = val
        if val_clean.endswith('Z'):
            val_clean = val_clean[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(val_clean)
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except ValueError:
            return None

    def _row_to_task(self, row: Any) -> TaskRecord:
        def parse_dt(val: str | None) -> datetime | None:
            if val is None:
                return None
            try:
                return datetime.fromisoformat(val)
            except ValueError:
                return None

        try:
            r_id = row["id"]
            title = row["title"]
            description = row["description"]
            role = row["role"]
            priority = row["priority"]
            status = row["status"]
            attempts = row["attempts"]
            max_attempts = row["max_attempts"]
            created_at = row["created_at"]
            updated_at = row["updated_at"]
            result = row["result"]
            error = row["error"]
            requires_approval = row["requires_approval"]
            locked_by = row["locked_by"] if "locked_by" in row.keys() else None
            locked_at = row["locked_at"] if "locked_at" in row.keys() else None
            lease_expires_at = row["lease_expires_at"] if "lease_expires_at" in row.keys() else None
            next_run_at = row["next_run_at"] if "next_run_at" in row.keys() else None
            approved_by = row["approved_by"] if "approved_by" in row.keys() else None
            approved_at = row["approved_at"] if "approved_at" in row.keys() else None
            approval_reason = row["approval_reason"] if "approval_reason" in row.keys() else None
        except (TypeError, KeyError, IndexError):
            r_id = row[0]
            title = row[1]
            description = row[2]
            role = row[3]
            priority = row[4]
            status = row[5]
            attempts = row[6]
            max_attempts = row[7]
            created_at = row[8]
            updated_at = row[9]
            result = row[10]
            error = row[11]
            requires_approval = row[12]
            locked_by = row[13] if len(row) > 13 else None
            locked_at = row[14] if len(row) > 14 else None
            lease_expires_at = row[15] if len(row) > 15 else None
            next_run_at = row[16] if len(row) > 16 else None
            approved_by = row[17] if len(row) > 17 else None
            approved_at = row[18] if len(row) > 18 else None
            approval_reason = row[19] if len(row) > 19 else None

        return TaskRecord(
            id=r_id,
            title=title,
            description=description,
            role=role,
            priority=priority,
            status=TaskStatus(status),
            attempts=attempts,
            max_attempts=max_attempts,
            created_at=datetime.fromisoformat(created_at),
            updated_at=datetime.fromisoformat(updated_at),
            result=result,
            error=error,
            requires_approval=bool(requires_approval),
            locked_by=locked_by,
            locked_at=parse_dt(locked_at),
            lease_expires_at=parse_dt(lease_expires_at),
            next_run_at=parse_dt(next_run_at),
            approved_by=approved_by,
            approved_at=parse_dt(approved_at),
            approval_reason=approval_reason,
        )
