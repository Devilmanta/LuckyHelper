"""
LuckyHelper - Database Manager
SQLite CRUD operations for trade journal
"""

import sqlite3
import os
import math
from datetime import datetime, date
from typing import Optional



def _get_app_data_dir() -> str:
    """
    Returns the persistent data directory for LuckyHelper.
    - Windows: %APPDATA%/LuckyHelper
    - macOS:   ~/Library/Application Support/LuckyHelper
    - Linux:   ~/.local/share/LuckyHelper
    Always creates the directory if it doesn't exist.
    """
    import platform
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))

    app_dir = os.path.join(base, "LuckyHelper")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


APP_DATA_DIR = _get_app_data_dir()
DB_PATH = os.path.join(APP_DATA_DIR, "luckyhelper.db")

# Screenshots (trade images) stored alongside the DB
SCREENSHOTS_DIR = os.path.join(APP_DATA_DIR, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)




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


def get_advanced_stats() -> dict:
    """
    Return a comprehensive set of trading statistics for the stats dashboard.
    Includes: Profit Factor, Expectancy, Sharpe Ratio, Max Drawdown,
    avg win/loss, streaks, symbol performance, and monthly breakdown.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # ── All trades ordered by date ─────────────────────────────
    cursor.execute("""
        SELECT date, symbol, direction, pnl, entry_price, exit_price,
               sl_price, tp_price, quantity, risk_pct, leverage
        FROM trades
        ORDER BY date ASC, created_at ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()

    if not rows:
        return {}

    pnls = [r["pnl"] for r in rows]
    wins  = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    breakevens = [p for p in pnls if p == 0]

    total = len(pnls)
    win_count  = len(wins)
    loss_count = len(losses)
    total_pnl  = sum(pnls)

    # ── Win Rate ───────────────────────────────────────────────
    win_rate = (win_count / total * 100) if total > 0 else 0.0

    # ── Profit Factor ──────────────────────────────────────────
    gross_profit = sum(wins)
    gross_loss   = abs(sum(losses)) if losses else 0.0
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

    # ── Average Win / Loss ─────────────────────────────────────
    avg_win  = (gross_profit / win_count)  if win_count  > 0 else 0.0
    avg_loss = (gross_loss   / loss_count) if loss_count > 0 else 0.0

    # ── Risk/Reward Ratio (average) ────────────────────────────
    rr_ratio = (avg_win / avg_loss) if avg_loss > 0 else 0.0

    # ── Expectancy per trade ───────────────────────────────────
    # Expectancy = (Win Rate × Avg Win) − (Loss Rate × Avg Loss)
    loss_rate = (loss_count / total) if total > 0 else 0.0
    expectancy = (win_rate / 100 * avg_win) - (loss_rate * avg_loss)

    # ── Largest Win / Loss ─────────────────────────────────────
    best_trade  = max(pnls)
    worst_trade = min(pnls)

    # ── Max Drawdown ──────────────────────────────────────────
    peak = 0.0
    running = 0.0
    max_drawdown = 0.0
    for p in pnls:
        running += p
        if running > peak:
            peak = running
        dd = peak - running
        if dd > max_drawdown:
            max_drawdown = dd

    # ── Sharpe Ratio (simplified daily, risk-free=0) ──────────
    # Group PnL by day
    from collections import defaultdict
    daily_pnl: dict = defaultdict(float)
    for r in rows:
        daily_pnl[r["date"]] += r["pnl"]
    daily_returns = list(daily_pnl.values())
    if len(daily_returns) > 1:
        mean_r  = sum(daily_returns) / len(daily_returns)
        variance = sum((x - mean_r) ** 2 for x in daily_returns) / len(daily_returns)
        std_r = math.sqrt(variance) if variance > 0 else 0.0
        sharpe = (mean_r / std_r * math.sqrt(252)) if std_r > 0 else 0.0
    else:
        sharpe = 0.0

    # ── Consecutive Win/Loss Streaks ──────────────────────────
    max_win_streak  = 0
    max_loss_streak = 0
    cur_win = 0
    cur_loss = 0
    for p in pnls:
        if p > 0:
            cur_win += 1
            cur_loss = 0
        elif p < 0:
            cur_loss += 1
            cur_win = 0
        else:
            cur_win = 0
            cur_loss = 0
        max_win_streak  = max(max_win_streak,  cur_win)
        max_loss_streak = max(max_loss_streak, cur_loss)

    # ── Symbol Performance ────────────────────────────────────
    sym_stats: dict = defaultdict(lambda: {"pnl": 0.0, "count": 0, "wins": 0})
    for r in rows:
        sym = r["symbol"] or "?"
        sym_stats[sym]["pnl"]   += r["pnl"]
        sym_stats[sym]["count"] += 1
        if r["pnl"] > 0:
            sym_stats[sym]["wins"] += 1
    symbol_performance = [
        {"symbol": s, **v, "win_rate": (v["wins"] / v["count"] * 100) if v["count"] > 0 else 0}
        for s, v in sym_stats.items()
    ]
    symbol_performance.sort(key=lambda x: x["pnl"], reverse=True)

    # ── Direction Stats ───────────────────────────────────────
    long_trades  = [r for r in rows if r["direction"] == "LONG"]
    short_trades = [r for r in rows if r["direction"] == "SHORT"]
    long_pnl  = sum(r["pnl"] for r in long_trades)
    short_pnl = sum(r["pnl"] for r in short_trades)
    long_wins  = sum(1 for r in long_trades  if r["pnl"] > 0)
    short_wins = sum(1 for r in short_trades if r["pnl"] > 0)

    # ── Monthly PnL breakdown ─────────────────────────────────
    monthly_pnl: dict = defaultdict(float)
    for r in rows:
        month_key = r["date"][:7]  # "YYYY-MM"
        monthly_pnl[month_key] += r["pnl"]
    monthly_breakdown = sorted(
        [{"month": k, "pnl": v} for k, v in monthly_pnl.items()],
        key=lambda x: x["month"]
    )

    # ── Avg trades per day ────────────────────────────────────
    active_days = len(daily_pnl)
    avg_trades_per_day = (total / active_days) if active_days > 0 else 0.0

    # ── Recovery Factor ──────────────────────────────────────
    recovery_factor = (total_pnl / max_drawdown) if max_drawdown > 0 else 0.0

    return {
        "total_trades":       total,
        "win_count":          win_count,
        "loss_count":         loss_count,
        "breakeven_count":    len(breakevens),
        "win_rate":           win_rate,
        "total_pnl":          total_pnl,
        "gross_profit":       gross_profit,
        "gross_loss":         gross_loss,
        "profit_factor":      profit_factor,
        "avg_win":            avg_win,
        "avg_loss":           avg_loss,
        "rr_ratio":           rr_ratio,
        "expectancy":         expectancy,
        "best_trade":         best_trade,
        "worst_trade":        worst_trade,
        "max_drawdown":       max_drawdown,
        "sharpe":             sharpe,
        "max_win_streak":     max_win_streak,
        "max_loss_streak":    max_loss_streak,
        "active_days":        active_days,
        "avg_trades_per_day": avg_trades_per_day,
        "recovery_factor":    recovery_factor,
        "symbol_performance": symbol_performance,
        "monthly_breakdown":  monthly_breakdown,
        "long_count":         len(long_trades),
        "short_count":        len(short_trades),
        "long_pnl":           long_pnl,
        "short_pnl":          short_pnl,
        "long_wins":          long_wins,
        "short_wins":         short_wins,
        "long_win_rate":      (long_wins  / len(long_trades)  * 100) if long_trades  else 0.0,
        "short_win_rate":     (short_wins / len(short_trades) * 100) if short_trades else 0.0,
    }


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
