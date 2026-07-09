"""
LuckyHelper - Database Manager
SQLite CRUD operations for trade journal
"""

import sqlite3
import os
from datetime import datetime, date
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "luckyhelper.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db():
    """Create tables if they don't exist, and migrate if needed."""
    conn = get_connection()
    cursor = conn.cursor()

    # ── Trades table ───────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            date        TEXT NOT NULL,
            symbol      TEXT NOT NULL DEFAULT '',
            direction   TEXT NOT NULL DEFAULT 'LONG',
            entry_price REAL DEFAULT 0.0,
            exit_price  REAL DEFAULT 0.0,
            quantity    REAL DEFAULT 0.0,
            tp_price    REAL DEFAULT 0.0,
            sl_price    REAL DEFAULT 0.0,
            pnl         REAL DEFAULT 0.0,
            notes       TEXT DEFAULT '',
            size_type   TEXT DEFAULT 'ADET',
            size_value  REAL DEFAULT 0.0,
            risk_pct    REAL DEFAULT 0.0,
            leverage    INTEGER DEFAULT 1,
            img_path    TEXT DEFAULT '',
            created_at  TEXT DEFAULT (datetime('now'))
        )
    """)

    # Migrations for existing databases (safe: fails silently if column exists)
    for migration in [
        "ALTER TABLE trades ADD COLUMN size_type TEXT DEFAULT 'ADET'",
        "ALTER TABLE trades ADD COLUMN size_value REAL DEFAULT 0.0",
        "ALTER TABLE trades ADD COLUMN risk_pct REAL DEFAULT 0.0",
        "ALTER TABLE trades ADD COLUMN leverage INTEGER DEFAULT 1",
        "ALTER TABLE trades ADD COLUMN img_path TEXT DEFAULT ''",
    ]:
        try:
            cursor.execute(migration)
        except sqlite3.OperationalError:
            pass  # Column already exists

    # ── Settings table ─────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


def get_trades_for_date(trade_date: str) -> list[dict]:
    """
    Return all trades for a specific date.
    trade_date: 'YYYY-MM-DD'
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM trades WHERE date = ? ORDER BY created_at ASC",
        (trade_date,)
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_monthly_summary(year: int, month: int) -> dict[str, dict]:
    """
    Return {date_str: {"total_pnl": float, "trade_count": int}} for every day in the given month that has trades.
    """
    month_str = f"{year}-{month:02d}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT date, SUM(pnl) as total_pnl, COUNT(*) as trade_count
        FROM trades
        WHERE date LIKE ?
        GROUP BY date
        """,
        (f"{month_str}-%",)
    )
    result = {
        row["date"]: {
            "total_pnl": row["total_pnl"] or 0.0,
            "trade_count": row["trade_count"] or 0
        }
        for row in cursor.fetchall()
    }
    conn.close()
    return result


def add_trade(
    trade_date: str,
    symbol: str,
    direction: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    tp_price: float,
    sl_price: float,
    pnl: float,
    notes: str,
    size_type: str = "ADET",
    size_value: float = 0.0,
    risk_pct: float = 0.0,
    leverage: int = 1,
    img_path: str = "",
) -> int:
    """Insert a new trade."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO trades
            (date, symbol, direction, entry_price, exit_price, quantity,
             tp_price, sl_price, pnl, notes, size_type, size_value, risk_pct, leverage, img_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (trade_date, symbol, direction, entry_price, exit_price, quantity,
         tp_price, sl_price, pnl, notes, size_type, size_value, risk_pct, leverage, img_path)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_trade(
    trade_id: int,
    symbol: str,
    direction: str,
    entry_price: float,
    exit_price: float,
    quantity: float,
    tp_price: float,
    sl_price: float,
    pnl: float,
    notes: str,
    size_type: str = "ADET",
    size_value: float = 0.0,
    risk_pct: float = 0.0,
    leverage: int = 1,
    img_path: str = "",
):
    """Update an existing trade by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE trades
        SET symbol=?, direction=?, entry_price=?, exit_price=?,
            quantity=?, tp_price=?, sl_price=?, pnl=?, notes=?,
            size_type=?, size_value=?, risk_pct=?, leverage=?, img_path=?
        WHERE id=?
        """,
        (symbol, direction, entry_price, exit_price, quantity,
         tp_price, sl_price, pnl, notes, size_type, size_value, risk_pct, leverage, img_path, trade_id)
    )
    conn.commit()
    conn.close()


def delete_trade(trade_id: int):
    """Delete a trade by id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM trades WHERE id=?", (trade_id,))
    conn.commit()
    conn.close()


def get_overall_stats() -> dict:
    """Return global statistics across all trades, safely handling None values."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            COUNT(*) as total_trades,
            SUM(pnl) as total_pnl,
            SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning_trades,
            SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing_trades,
            MAX(pnl) as best_trade,
            MIN(pnl) as worst_trade
        FROM trades
    """)
    row = dict(cursor.fetchone())
    conn.close()
    
    # Safe defaults for None values
    row["total_trades"] = row["total_trades"] or 0
    row["total_pnl"] = row["total_pnl"] or 0.0
    row["winning_trades"] = row["winning_trades"] or 0
    row["losing_trades"] = row["losing_trades"] or 0
    row["best_trade"] = row["best_trade"] or 0.0
    row["worst_trade"] = row["worst_trade"] or 0.0
    
    return row


def get_setting(key: str, default: str = "") -> str:
    """Read a setting value by key. Returns default if not found."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    """Write or update a setting value."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value)
    )
    conn.commit()
    conn.close()
