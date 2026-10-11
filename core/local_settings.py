"""Local preferences and SQLite snapshots; no provider or network configuration."""

from __future__ import annotations

import json
import math
import os
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

DEFAULT_SETTINGS = {"default_symbol": "DEMO1", "default_currency": "TRY"}
_REQUIRED = {
    "runs": {"digest", "recorded_at", "payload"},
    "account": {"id", "cash"},
    "holdings": {"symbol", "quantity"},
    "trades": {"id", "at", "symbol", "side", "quantity", "price"},
    "alerts": {"id", "symbol", "threshold", "previous", "last_time"},
    "alert_events": {"alert_id", "bar_time", "price"},
}


def validate_settings(values: dict) -> dict:
    if not isinstance(values, dict) or set(values) != set(DEFAULT_SETTINGS):
        raise ValueError("Ayar alanları geçersiz")
    symbol = values["default_symbol"]
    currency = values["default_currency"]
    if not isinstance(symbol, str) or not symbol.strip() or len(symbol.strip()) > 32:
        raise ValueError("Varsayılan sembol 1–32 karakter olmalı")
    if any(ord(char) < 32 for char in symbol):
        raise ValueError("Sembol kontrol karakteri içeremez")
    if currency not in {"TRY", "USD", "EUR"}:
        raise ValueError("Para birimi TRY, USD veya EUR olmalı")
    return {"default_symbol": symbol.strip(), "default_currency": currency}


def load_settings(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        return dict(DEFAULT_SETTINGS)
    try:
        return validate_settings(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as error:
        raise ValueError("Yerel ayarlar okunamadı veya geçersiz") from error


def save_settings(path: Path, values: dict) -> dict:
    values = validate_settings(values)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    name = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", delete=False
        ) as output:
            name = output.name
            json.dump(values, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if name and Path(name).exists():
            Path(name).unlink()
    return values


def _validate_database(connection: sqlite3.Connection):
    if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
        raise ValueError("Yedek veritabanı bütünlüğü geçersiz")
    tables = {
        row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    if not set(_REQUIRED) <= tables:
        raise ValueError("Yedek ANKA tablolarını içermiyor")
    for table, required in _REQUIRED.items():
        columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if not required <= columns:
            raise ValueError("Yedek ANKA yerel veritabanı şemasıyla uyumsuz")
    accounts = connection.execute("SELECT id,cash FROM account").fetchall()
    if (
        len(accounts) != 1
        or accounts[0][0] != 1
        or not isinstance(accounts[0][1], (int, float))
        or not math.isfinite(accounts[0][1])
        or accounts[0][1] < 0
    ):
        raise ValueError("Yedek hesap verisi geçersiz")
    for symbol, quantity in connection.execute("SELECT symbol,quantity FROM holdings"):
        if (
            not isinstance(symbol, str)
            or not symbol
            or not isinstance(quantity, (int, float))
            or not math.isfinite(quantity)
            or quantity < 0
        ):
            raise ValueError("Yedek pozisyon verisi geçersiz")
    for (payload,) in connection.execute("SELECT payload FROM runs"):
        run = json.loads(payload)
        if not isinstance(run, dict) or not {"symbol", "analysis", "origin"} <= set(run):
            raise ValueError("Yedek analiz kaydı geçersiz")


def _snapshot(path: Path) -> sqlite3.Connection:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Yerel veritabanı dosyası bulunamadı")
    snapshot = sqlite3.connect(":memory:")
    try:
        with closing(
            sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
        ) as source:
            source.backup(snapshot)
        _validate_database(snapshot)
        return snapshot
    except (sqlite3.Error, ValueError, TypeError) as error:
        snapshot.close()
        raise ValueError("Dosya geçerli bir ANKA yerel SQLite yedeği değil") from error


def backup_database(database_path: Path, destination: Path):
    database_path, destination = Path(database_path), Path(destination)
    if database_path.resolve() == destination.resolve():
        raise ValueError("Yedek hedefi etkin veritabanından farklı olmalı")
    snapshot = _snapshot(database_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        descriptor, name = tempfile.mkstemp(dir=destination.parent, prefix=destination.name + ".")
        os.close(descriptor)
        temporary = Path(name)
        with closing(sqlite3.connect(temporary)) as target:
            snapshot.backup(target)
        os.replace(temporary, destination)
    finally:
        snapshot.close()
        if temporary and temporary.exists():
            temporary.unlink()


def restore_database(database_path: Path, source: Path):
    database_path, source = Path(database_path), Path(source)
    if database_path.resolve() == source.resolve():
        raise ValueError("Geri yükleme kaynağı etkin veritabanından farklı olmalı")
    snapshot = _snapshot(source)  # Reject before opening or changing the target.
    try:
        database_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(database_path, timeout=5)) as target:
            snapshot.backup(target)
    finally:
        snapshot.close()
