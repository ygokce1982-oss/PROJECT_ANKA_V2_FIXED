"""Source-backed local research records. No remote requests or live claims."""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

KINDS = ("NEWS", "KAP", "CALENDAR")
MAX_IMPORT_BYTES = 2 * 1024 * 1024


def publication_age_label(published_at, *, now):
    """Age of an imported publication timestamp; never a live-source health claim.

    The 24-hour boundary is a display bucket, not a market freshness SLA.
    CALENDAR uses the same publication field, not an inferred event time.
    """
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("Referans saat zaman dilimi içermeli")
    reference = now.astimezone(UTC)
    try:
        stamp = datetime.fromisoformat(published_at)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            return "Tarih geçersiz"
        age = reference - stamp.astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        return "Tarih geçersiz"
    if age < timedelta(0):
        return "Gelecek tarih"
    return "Son 24 saat" if age < timedelta(hours=24) else "24 saatten eski"


def search_normalize(text):
    """Canonical Unicode and Turkish casing, preserving dotted/dotless distinction."""
    return (
        unicodedata.normalize("NFC", text).translate(str.maketrans({"I": "ı", "İ": "i"})).casefold()
    )


def _text(value, field, maximum, required=True):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise ValueError(f"Geçersiz {field}")
    return value.strip()


def validate_record(record):
    if not isinstance(record, dict):
        raise ValueError("Her kayıt bir JSON nesnesi olmalı")
    title = _text(record.get("title"), "title", 500)
    kind = record.get("kind")
    if kind not in KINDS:
        raise ValueError("kind NEWS, KAP veya CALENDAR olmalı")
    stamp = _text(record.get("published_at"), "published_at", 100)
    try:
        timestamp = datetime.fromisoformat(stamp)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError()
        stamp = timestamp.astimezone(UTC).isoformat()
    except (ValueError, OverflowError) as error:
        raise ValueError("published_at geçerli ve zaman dilimi içeren tarih olmalı") from error
    source = _text(record.get("source_url", record.get("source")), "source_url", 2048)
    try:
        parsed = urlsplit(source)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(char.isspace() or ord(char) < 32 for char in source)
        ):
            raise ValueError()
        _ = parsed.port
    except ValueError as error:
        raise ValueError("Kaynak güvenli http/https URL olmalı") from error
    symbol = _text(record.get("symbol") or "", "symbol", 40, False).upper()
    summary = _text(record.get("summary", ""), "summary", 20000, False)
    return (title, kind, stamp, source, symbol, summary)


class ResearchStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS research_records (
                id INTEGER PRIMARY KEY, title TEXT NOT NULL, kind TEXT NOT NULL,
                published_at TEXT NOT NULL, source_url TEXT NOT NULL,
                symbol TEXT NOT NULL, summary TEXT NOT NULL,
                origin TEXT NOT NULL DEFAULT 'LOCAL_IMPORT',
                UNIQUE(source_url, kind, published_at))""")

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.create_function("search_normalize", 1, search_normalize, deterministic=True)
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def import_json(self, path):
        with Path(path).open("rb") as stream:
            payload = stream.read(MAX_IMPORT_BYTES + 1)
        if len(payload) > MAX_IMPORT_BYTES:
            raise ValueError("JSON boyutu 2 MB sınırını aşıyor")
        try:
            records = json.loads(payload.decode("utf-8-sig"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("Geçerli UTF-8 JSON gerekli") from error
        return self.import_records(records)

    def import_records(self, records):
        if not isinstance(records, list) or not records or len(records) > 10000:
            raise ValueError("JSON 1–10000 kayıttan oluşan liste olmalı")
        validated = [validate_record(record) for record in records]
        with self._connect() as connection:
            before = connection.total_changes
            connection.executemany(
                """INSERT INTO research_records
                (title,kind,published_at,source_url,symbol,summary)
                VALUES (?,?,?,?,?,?) ON CONFLICT(source_url,kind,published_at) DO NOTHING""",
                validated,
            )
            inserted = connection.total_changes - before
        return {
            "inserted": inserted,
            "duplicates": len(validated) - inserted,
            "origin": "LOCAL_IMPORT",
            "live": False,
        }

    def query(self, *, kind=None, symbol=None, text="", limit=200):
        if kind is not None and kind not in KINDS:
            raise ValueError("Geçersiz tür")
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("limit 1–1000 olmalı")
        clauses, values = [], []
        if kind:
            clauses.append("kind=?")
            values.append(kind)
        if symbol:
            clauses.append("symbol=?")
            values.append(symbol.strip().upper())
        if text:
            clauses.append(
                "(instr(search_normalize(title),search_normalize(?))>0 "
                "OR instr(search_normalize(summary),search_normalize(?))>0)"
            )
            values.extend([text, text])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                "SELECT * FROM research_records"
                + where
                + " ORDER BY published_at DESC,id DESC LIMIT ?",
                [*values, limit],
            ).fetchall()
        return [dict(row, live=False) for row in rows]
