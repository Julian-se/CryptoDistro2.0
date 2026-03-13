"""
Trade tracker — SQLite logging of all trades and P&L calculation.

Every buy, sell, and transfer is recorded. P&L calculated per cycle
(buy→transfer→sell) and cumulatively.
"""

import logging
import sqlite3
import time
from decimal import Decimal
from pathlib import Path

from src.core.config import get_config

logger = logging.getLogger(__name__)


class TradeTracker:
    """SQLite-backed trade logging and P&L tracking."""

    def __init__(self):
        cfg = get_config()
        db_path = cfg["database"]["path"]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Trade tracker initialized (db: {db_path})")

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                cycle_id TEXT,
                type TEXT NOT NULL,          -- 'buy', 'sell', 'transfer'
                platform TEXT NOT NULL,       -- 'binance', 'noones', 'lightning'
                asset TEXT NOT NULL,          -- 'BTC', 'USDT'
                quantity TEXT NOT NULL,       -- Decimal as string
                price_usd TEXT,              -- Price per unit in USD
                total_usd TEXT,              -- Total value in USD
                fee_usd TEXT DEFAULT '0',
                order_id TEXT,
                offer_id TEXT,
                counterparty TEXT,
                notes TEXT
            );

            CREATE TABLE IF NOT EXISTS cycles (
                id TEXT PRIMARY KEY,
                started_at REAL NOT NULL,
                completed_at REAL,
                status TEXT DEFAULT 'open',   -- 'open', 'completed', 'failed'
                buy_platform TEXT,
                sell_platform TEXT,
                asset TEXT,
                buy_price TEXT,
                sell_price TEXT,
                quantity TEXT,
                gross_profit_usd TEXT,
                fees_usd TEXT,
                net_profit_usd TEXT,
                duration_sec REAL,
                notes TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_trades_cycle ON trades(cycle_id);
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
            CREATE INDEX IF NOT EXISTS idx_cycles_status ON cycles(status);
        """)
        self.conn.commit()

    # --- Cycle Management ---

    def start_cycle(self, cycle_id: str, buy_platform: str, sell_platform: str, asset: str) -> str:
        """Start a new arbitrage cycle."""
        self.conn.execute(
            "INSERT INTO cycles (id, started_at, buy_platform, sell_platform, asset) VALUES (?, ?, ?, ?, ?)",
            (cycle_id, time.time(), buy_platform, sell_platform, asset),
        )
        self.conn.commit()
        logger.info(f"Cycle {cycle_id} started: {buy_platform} → {sell_platform}")
        return cycle_id

    def complete_cycle(self, cycle_id: str) -> dict:
        """
        Complete a cycle — calculate P&L from its trades.
        Returns the cycle summary.
        """
        trades = self.get_cycle_trades(cycle_id)
        if not trades:
            logger.warning(f"No trades found for cycle {cycle_id}")
            return {}

        buys = [t for t in trades if t["type"] == "buy"]
        sells = [t for t in trades if t["type"] == "sell"]
        all_fees = sum(Decimal(t["fee_usd"] or "0") for t in trades)

        total_buy = sum(Decimal(t["total_usd"] or "0") for t in buys)
        total_sell = sum(Decimal(t["total_usd"] or "0") for t in sells)
        gross_profit = total_sell - total_buy
        net_profit = gross_profit - all_fees

        buy_price = Decimal(buys[0]["price_usd"]) if buys else Decimal("0")
        sell_price = Decimal(sells[0]["price_usd"]) if sells else Decimal("0")
        quantity = Decimal(buys[0]["quantity"]) if buys else Decimal("0")
        started = float(trades[0]["timestamp"])
        duration = time.time() - started

        self.conn.execute(
            """UPDATE cycles SET
                completed_at = ?, status = 'completed',
                buy_price = ?, sell_price = ?, quantity = ?,
                gross_profit_usd = ?, fees_usd = ?, net_profit_usd = ?,
                duration_sec = ?
            WHERE id = ?""",
            (
                time.time(), str(buy_price), str(sell_price), str(quantity),
                str(gross_profit), str(all_fees), str(net_profit),
                duration, cycle_id,
            ),
        )
        self.conn.commit()

        summary = {
            "cycle_id": cycle_id,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "quantity": quantity,
            "gross_profit": gross_profit,
            "fees": all_fees,
            "net_profit": net_profit,
            "duration_sec": duration,
        }
        logger.info(
            f"Cycle {cycle_id} completed: net ${net_profit:.2f} "
            f"({duration:.0f}s)"
        )
        return summary

    def fail_cycle(self, cycle_id: str, reason: str):
        """Mark a cycle as failed."""
        self.conn.execute(
            "UPDATE cycles SET status = 'failed', notes = ?, completed_at = ? WHERE id = ?",
            (reason, time.time(), cycle_id),
        )
        self.conn.commit()
        logger.warning(f"Cycle {cycle_id} failed: {reason}")

    # --- Trade Logging ---

    def log_trade(
        self,
        trade_type: str,
        platform: str,
        asset: str,
        quantity: Decimal,
        price_usd: Decimal | None = None,
        total_usd: Decimal | None = None,
        fee_usd: Decimal = Decimal("0"),
        cycle_id: str | None = None,
        order_id: str | None = None,
        offer_id: str | None = None,
        counterparty: str | None = None,
        notes: str | None = None,
    ) -> int:
        """Log a single trade (buy, sell, or transfer)."""
        if total_usd is None and price_usd is not None:
            total_usd = quantity * price_usd

        cursor = self.conn.execute(
            """INSERT INTO trades
            (timestamp, cycle_id, type, platform, asset, quantity, price_usd,
             total_usd, fee_usd, order_id, offer_id, counterparty, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(), cycle_id, trade_type, platform, asset,
                str(quantity), str(price_usd) if price_usd else None,
                str(total_usd) if total_usd else None, str(fee_usd),
                order_id, offer_id, counterparty, notes,
            ),
        )
        self.conn.commit()
        trade_id = cursor.lastrowid
        logger.info(f"Logged {trade_type} on {platform}: {quantity} {asset} @ ${price_usd}")
        return trade_id

    # --- Queries ---

    def get_cycle_trades(self, cycle_id: str) -> list[dict]:
        """Get all trades in a cycle."""
        rows = self.conn.execute(
            "SELECT * FROM trades WHERE cycle_id = ? ORDER BY timestamp", (cycle_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_pnl_summary(self, days: int = 30) -> dict:
        """Get P&L summary for the last N days."""
        cutoff = time.time() - (days * 86400)
        rows = self.conn.execute(
            "SELECT * FROM cycles WHERE status = 'completed' AND started_at > ?",
            (cutoff,),
        ).fetchall()

        cycles = [dict(r) for r in rows]
        total_net = sum(Decimal(c["net_profit_usd"] or "0") for c in cycles)
        total_gross = sum(Decimal(c["gross_profit_usd"] or "0") for c in cycles)
        total_fees = sum(Decimal(c["fees_usd"] or "0") for c in cycles)
        avg_duration = (
            sum(c["duration_sec"] or 0 for c in cycles) / len(cycles) if cycles else 0
        )

        return {
            "period_days": days,
            "total_cycles": len(cycles),
            "total_gross_profit": total_gross,
            "total_fees": total_fees,
            "total_net_profit": total_net,
            "avg_cycle_duration_sec": avg_duration,
            "avg_profit_per_cycle": total_net / len(cycles) if cycles else Decimal("0"),
            "cycles_per_day": len(cycles) / days if days > 0 else 0,
        }

    def get_recent_trades(self, limit: int = 20) -> list[dict]:
        """Get most recent trades."""
        rows = self.conn.execute(
            "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_open_cycles(self) -> list[dict]:
        """Get all currently open (in-progress) cycles."""
        rows = self.conn.execute(
            "SELECT * FROM cycles WHERE status = 'open' ORDER BY started_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.conn.close()
