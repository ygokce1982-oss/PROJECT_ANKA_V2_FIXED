"""Local research pipeline. Explicit sample data; no provider or order connections."""

from __future__ import annotations

import csv
import hashlib
import heapq
import io
import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Bar:
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float


def validated(bars: list[Bar]) -> list[Bar]:
    if len(bars) < 35:
        raise ValueError("Analiz için en az 35 mum gerekli")
    previous = None
    for bar in bars:
        timestamp = datetime.fromisoformat(bar.time)
        if timestamp.tzinfo is None:
            raise ValueError("Zaman dilimi gerekli")
        if previous is not None and timestamp <= previous:
            raise ValueError("Mum zamanları sıralı ve benzersiz olmalı")
        values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Geçersiz sayısal veri")
        if min(values[:4]) <= 0 or bar.volume < 0:
            raise ValueError("Fiyat pozitif, hacim negatif olmayan sayı olmalı")
        if bar.low > min(bar.open, bar.close) or bar.high < max(bar.open, bar.close):
            raise ValueError("OHLC sınırları tutarsız")
        previous = timestamp
    return bars


def sample_bars() -> list[Bar]:
    bars = []
    start = datetime(2025, 1, 1, tzinfo=UTC)
    previous = 100.0
    for index in range(120):
        close = 100 + index * 0.15 + math.sin(index / 7) * 4
        bars.append(
            Bar(
                (start + timedelta(days=index)).isoformat(),
                previous,
                max(previous, close) + 1,
                min(previous, close) - 1,
                close,
                1000 + index * 5,
            )
        )
        previous = close
    return bars


def read_csv(path: Path) -> list[Bar]:
    if path.stat().st_size > 10_000_000:
        raise ValueError("CSV boyutu 10 MB sınırını aşıyor")
    text = path.read_text(encoding="utf-8-sig")
    rows = csv.DictReader(io.StringIO(text))
    if not {"time", "open", "high", "low", "close", "volume"} <= set(rows.fieldnames or []):
        raise ValueError("CSV başlıkları: time,open,high,low,close,volume")
    result = []
    for row in rows:
        if len(result) >= 20000:
            raise ValueError("En fazla 20000 mum destekleniyor")
        try:
            result.append(
                Bar(
                    row["time"],
                    *(float(row[key]) for key in ("open", "high", "low", "close", "volume")),
                )
            )
        except (ValueError, TypeError, KeyError) as error:
            raise ValueError("CSV satırı eksik veya sayısal alan geçersiz") from error
    return validated(result)


def analysis(bars: list[Bar]) -> dict:
    validated(bars)
    closes = [bar.close for bar in bars]
    sma20 = sum(closes[-20:]) / 20
    sma35 = sum(closes[-35:]) / 35
    changes = [closes[i] - closes[i - 1] for i in range(len(closes) - 14, len(closes))]
    gain = sum(max(change, 0) for change in changes) / 14
    loss = sum(max(-change, 0) for change in changes) / 14
    rsi = 50 if gain == loss == 0 else 100 if loss == 0 else 100 - 100 / (1 + gain / loss)
    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    mean = sum(returns) / len(returns)
    volatility = math.sqrt(sum((value - mean) ** 2 for value in returns) / len(returns))
    peak, drawdown = closes[0], 0.0
    for close in closes:
        peak = max(peak, close)
        drawdown = min(drawdown, close / peak - 1)
    regime = "yatay"
    if abs(sma20 / sma35 - 1) > 0.01:
        regime = "yükseliş" if sma20 > sma35 else "düşüş"
    return {
        "close": closes[-1],
        "sma20": sma20,
        "sma35": sma35,
        "rsi14_simple": rsi,
        "bar_volatility": volatility,
        "maximum_drawdown": drawdown,
        "regime": regime,
        "explanation": "Rejim: SMA20/SMA35 farkı %1 eşiği. RSI: 14 mum basit ortalama."
        " Volatilite mum frekansındadır; yıllıklandırılmamıştır.",
        "last_bar_at": bars[-1].time,
        "rows": len(bars),
    }


def backtest(bars: list[Bar], fee: float = 0.001) -> dict:
    """SMA20 decision at close, execution on next open; long/cash, no leverage."""
    validated(bars)
    if not math.isfinite(fee) or not 0 <= fee < 0.1:
        raise ValueError("Komisyon oranı geçersiz")
    cash, quantity, orders = 10000.0, 0.0, 0
    equity = [cash]
    for index in range(20, len(bars)):
        previous_closes = [bar.close for bar in bars[index - 20 : index]]
        enter = previous_closes[-1] > sum(previous_closes) / 20
        if enter and quantity == 0:
            quantity = cash / (bars[index].open * (1 + fee))
            cash = 0.0
            orders += 1
        elif not enter and quantity > 0:
            cash = quantity * bars[index].open * (1 - fee)
            quantity = 0.0
            orders += 1
        equity.append(cash + quantity * bars[index].close)
    peak, drawdown = equity[0], 0.0
    for value in equity:
        peak = max(peak, value)
        drawdown = min(drawdown, value / peak - 1)
    return {
        "initial_cash": 10000,
        "equity": equity[-1],
        "return": equity[-1] / 10000 - 1,
        "maximum_drawdown": drawdown,
        "orders": orders,
        "fee_rate": fee,
        "open_position": quantity > 0,
        "equity_curve": equity,
        "method": "SMA20; önceki kapanışta karar, sonraki açılışta işlem."
        " Son açık pozisyon kapanışla değerlenir; satış komisyonu henüz düşülmez.",
    }


class LocalStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path, timeout=5)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS runs(
                digest TEXT PRIMARY KEY, recorded_at TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account(
                id INTEGER PRIMARY KEY CHECK(id=1), cash REAL NOT NULL CHECK(cash>=0));
            INSERT OR IGNORE INTO account VALUES(1,100000);
            CREATE TABLE IF NOT EXISTS holdings(
                symbol TEXT PRIMARY KEY, quantity REAL NOT NULL CHECK(quantity>=0));
            CREATE TABLE IF NOT EXISTS trades(
                id INTEGER PRIMARY KEY, at TEXT, symbol TEXT, side TEXT, quantity REAL, price REAL);
            CREATE TABLE IF NOT EXISTS alerts(
                id INTEGER PRIMARY KEY, symbol TEXT, threshold REAL, previous REAL, last_time TEXT);
            CREATE TABLE IF NOT EXISTS alert_events(
                alert_id INTEGER, bar_time TEXT, price REAL,
                PRIMARY KEY(alert_id,bar_time));
        """)
        self.connection.execute("""CREATE TABLE IF NOT EXISTS assets(
            symbol TEXT PRIMARY KEY, currency TEXT NOT NULL)""")
        # Legacy paper positions and trades were denominated in TRY.
        self.connection.execute("INSERT OR IGNORE INTO assets SELECT symbol,'TRY' FROM holdings")
        self.connection.execute("INSERT OR IGNORE INTO assets SELECT DISTINCT symbol,'TRY' FROM trades")
        columns = {row[1] for row in self.connection.execute("PRAGMA table_info(trades)")}
        for column, declaration in (("currency", "TEXT NOT NULL DEFAULT 'TRY'"),
                                    ("fx_rate", "REAL NOT NULL DEFAULT 1")):
            if column not in columns:
                self.connection.execute(f"ALTER TABLE trades ADD COLUMN {column} {declaration}")
        for (payload,) in self.connection.execute("SELECT payload FROM runs"):
            run = json.loads(payload)
            self.connection.execute("INSERT OR IGNORE INTO assets VALUES(?,?)",
                                    (run["symbol"], run.get("currency", "TRY")))
        self.connection.commit()

    @staticmethod
    def _currency(currency: str) -> str:
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isascii() or not currency.isalpha():
            raise ValueError("Para birimi üç harfli kod olmalı")
        return currency.upper()

    def _asset_currency(self, symbol: str, currency: str | None = None) -> str:
        row = self.connection.execute("SELECT currency FROM assets WHERE symbol=?", (symbol,)).fetchone()
        declared = self._currency(currency) if currency is not None else (row[0] if row else "TRY")
        if row and row[0] != declared:
            raise ValueError("Sembolün kayıtlı para birimi farklı")
        return declared

    @staticmethod
    def _fx(currency: str, fx_rates: dict[str, float] | None) -> float:
        rate = 1.0 if currency == "TRY" else (fx_rates or {}).get(currency)
        if rate is None or not math.isfinite(rate) or rate <= 0:
            raise ValueError("TRY dönüşümü için geçerli açık kur gerekli")
        return rate

    def close(self):
        self.connection.close()

    def execute(
        self, bars: list[Bar], symbol: str = "DEMO1", origin: str = "SAMPLE", fee: float = 0.001, currency: str = "TRY"
    ) -> dict:
        if origin not in {"SAMPLE", "LOCAL_CSV"}:
            raise ValueError("Yalnız örnek veya yerel CSV veri kabul edilir")
        if not symbol or len(symbol) > 32:
            raise ValueError("Sembol geçersiz")
        currency = self._asset_currency(symbol, currency)
        result = {
            "schema": 2,
            "engine": "local-v1",
            "symbol": symbol,
            "origin": origin,
            "live": False,
            "currency": currency,
            "source": origin,
            "as_of": bars[-1].time if bars else None,
            "bars": [asdict(bar) for bar in bars],
            "analysis": analysis(bars),
            "strategy": backtest(bars, fee),
        }
        encoded = json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False)
        digest = hashlib.sha256(encoded.encode()).hexdigest()
        with self.connection:
            self.connection.execute("INSERT OR IGNORE INTO assets VALUES(?,?)", (symbol, currency))
            self.connection.execute(
                "INSERT OR IGNORE INTO runs VALUES(?,?,?)",
                (digest, datetime.now(UTC).isoformat(), encoded),
            )
        result["digest"] = digest
        return result

    def latest(self, symbol: str | None = None) -> dict | None:
        for payload, digest in self.connection.execute(
            "SELECT payload,digest FROM runs ORDER BY rowid DESC"
        ):
            run = dict(json.loads(payload), digest=digest)
            if symbol is None or run["symbol"] == symbol:
                run.setdefault("currency", "TRY")
                run.setdefault("source", run["origin"])
                run.setdefault("as_of", run["analysis"]["last_bar_at"])
                return run
        return None

    def latest_by_symbol(self) -> dict[str, dict]:
        result = {}
        for payload, digest in self.connection.execute("SELECT payload,digest FROM runs ORDER BY rowid DESC"):
            run = dict(json.loads(payload), digest=digest)
            if run["symbol"] not in result:
                run.setdefault("currency", "TRY")
                run.setdefault("source", run["origin"])
                run.setdefault("as_of", run["analysis"]["last_bar_at"])
                result[run["symbol"]] = run
        return result

    def trade(self, symbol: str, side: str, quantity: float, price: float,
              currency: str | None = None, fx_rates: dict[str, float] | None = None):
        if side not in {"BUY", "SELL"} or not symbol or len(symbol) > 32:
            raise ValueError("Deneme işlemi geçersiz")
        if not all(math.isfinite(value) and value > 0 for value in (quantity, price)):
            raise ValueError("Miktar ve fiyat pozitif olmalı")
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            currency = self._asset_currency(symbol, currency)
            fx_rate = self._fx(currency, fx_rates)
            cost = quantity * price * fx_rate
            if not math.isfinite(cost):
                raise ValueError("Deneme işlemi sayısal sınırı aşıyor")
            cash = self.connection.execute("SELECT cash FROM account").fetchone()[0]
            row = self.connection.execute(
                "SELECT quantity FROM holdings WHERE symbol=?", (symbol,)
            ).fetchone()
            held = row[0] if row else 0
            if side == "BUY" and cost > cash:
                raise ValueError("Deneme bakiyesi yetersiz")
            if side == "SELL" and quantity > held:
                raise ValueError("Deneme pozisyonu yetersiz")
            sign = 1 if side == "BUY" else -1
            if not all(
                math.isfinite(value)
                for value in (cash - sign * cost, held + sign * quantity)
            ):
                raise ValueError("Deneme işlemi sayısal sınırı aşıyor")
            self.connection.execute("INSERT OR IGNORE INTO assets VALUES(?,?)", (symbol, currency))
            self.connection.execute(
                "UPDATE account SET cash=?", (max(0, cash - sign * cost),)
            )
            self.connection.execute(
                "INSERT OR REPLACE INTO holdings VALUES(?,?)",
                (symbol, max(0, held + sign * quantity)),
            )
            self.connection.execute(
                "INSERT INTO trades(at,symbol,side,quantity,price,currency,fx_rate) VALUES(?,?,?,?,?,?,?)",
                (datetime.now(UTC).isoformat(), symbol, side, quantity, price, currency, fx_rate),
            )
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    def portfolio(self, prices: dict[str, float], stress: float = -0.2,
                  fx_rates: dict[str, float] | None = None) -> dict:
        if not math.isfinite(stress) or not -1 <= stress <= 1:
            raise ValueError("Stres oranı -1 ile 1 arasında olmalı")
        cash = self.connection.execute("SELECT cash FROM account").fetchone()[0]
        positions, missing, missing_fx = [], [], []
        for symbol, quantity in self.connection.execute("SELECT symbol,quantity FROM holdings"):
            if quantity <= 0:
                continue
            price = prices.get(symbol)
            if price is None or not math.isfinite(price) or price <= 0:
                missing.append(symbol)
                continue
            currency = self._asset_currency(symbol)
            try:
                fx_rate = self._fx(currency, fx_rates)
            except ValueError:
                missing_fx.append(symbol)
                continue
            positions.append(
                {"symbol": symbol, "quantity": quantity, "price": price,
                 "currency": currency, "fx_rate": fx_rate, "value": quantity * price * fx_rate}
            )
            if not math.isfinite(positions[-1]["value"]):
                raise ValueError("Pozisyon değeri sayısal sınırı aşıyor")
        assets = sum(position["value"] for position in positions)
        total = cash + assets
        stress_total = cash + assets * (1 + stress)
        if not all(math.isfinite(value) for value in (cash, assets, total, stress_total)):
            raise ValueError("Portföy toplamı sayısal sınırı aşıyor")
        return {
            "cash": cash,
            "known_equity": total,
            "unpriced": missing,
            "missing_fx": missing_fx,
            "valuation_complete": not missing and not missing_fx,
            "positions": positions,
            "stress_equity": stress_total,
            "stress": stress,
            "currency": "TRY",
            "paper_only": True,
        }

    def add_alert(self, symbol: str, threshold: float, previous: float):
        if not symbol or not all(
            math.isfinite(value) and value > 0 for value in (threshold, previous)
        ):
            raise ValueError("Alarm değerleri geçersiz")
        with self.connection:
            return self.connection.execute(
                "INSERT INTO alerts(symbol,threshold,previous) VALUES(?,?,?)",
                (symbol, threshold, previous),
            ).lastrowid

    def alert_history(self, limit: int = 100) -> list[dict]:
        """Read persisted crossings, newest bar instant then alert ID first.

        A bounded heap preserves check_alerts' ISO timestamp/offset precision
        without loading the whole event history into memory.
        """
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 500:
            raise ValueError("Alarm geçmişi sınırı 1 ile 500 arasında tam sayı olmalı")
        rows = self.connection.execute(
            """SELECT a.id,a.symbol,a.threshold,e.price,e.bar_time
               FROM alert_events AS e JOIN alerts AS a ON a.id=e.alert_id"""
        )
        newest = heapq.nlargest(
            limit, rows,
            key=lambda row: (datetime.fromisoformat(row[4]), row[0], row[4]),
        )
        return [
            {"alert_id": identifier, "symbol": symbol, "threshold": threshold,
             "price": price, "bar_time": bar_time}
            for identifier, symbol, threshold, price, bar_time in newest
        ]

    def check_alerts(self, symbol: str, price: float, bar_time: str) -> int:
        if not math.isfinite(price) or price <= 0:
            raise ValueError("Alarm fiyatı geçersiz")
        timestamp = datetime.fromisoformat(bar_time)
        if timestamp.tzinfo is None:
            raise ValueError("Alarm zamanı için zaman dilimi gerekli")
        count = 0
        with self.connection:
            for identifier, threshold, previous, last_time in self.connection.execute(
                "SELECT id,threshold,previous,last_time FROM alerts WHERE symbol=?", (symbol,)
            ).fetchall():
                if last_time is not None and timestamp <= datetime.fromisoformat(last_time):
                    continue
                if previous < threshold <= price:
                    cursor = self.connection.execute(
                        "INSERT OR IGNORE INTO alert_events VALUES(?,?,?)",
                        (identifier, bar_time, price),
                    )
                    count += cursor.rowcount
                self.connection.execute(
                    "UPDATE alerts SET previous=?,last_time=? WHERE id=?",
                    (price, bar_time, identifier),
                )
        return count
