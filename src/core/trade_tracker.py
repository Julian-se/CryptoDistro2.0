"""
Trade tracker — SQLite logging of all trades and P&L calculation.

Supports two schemas:
  1. Legacy cycles (buy→transfer→sell across platforms)
  2. P2P trades synced from Noones (the actual business model)
"""

import logging
import sqlite3
import time
from datetime import datetime, timezone
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
                type TEXT NOT NULL,
                platform TEXT NOT NULL,
                asset TEXT NOT NULL,
                quantity TEXT NOT NULL,
                price_usd TEXT,
                total_usd TEXT,
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
                status TEXT DEFAULT 'open',
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

            CREATE TABLE IF NOT EXISTS p2p_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_hash TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                asset TEXT NOT NULL,
                fiat_amount REAL NOT NULL,
                fiat_currency TEXT NOT NULL,
                crypto_amount REAL NOT NULL,
                fiat_rate REAL NOT NULL,
                counterparty TEXT,
                payment_method TEXT,
                opened_at REAL NOT NULL,
                paid_at REAL,
                released_at REAL,
                completed_at REAL,
                confirmation_lag_sec REAL,
                profit_usd REAL,
                fee_usd REAL DEFAULT 0,
                offer_hash TEXT,
                synced_at REAL NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_trades_cycle ON trades(cycle_id);
            CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);
            CREATE INDEX IF NOT EXISTS idx_cycles_status ON cycles(status);
            CREATE INDEX IF NOT EXISTS idx_p2p_trade_hash ON p2p_trades(trade_hash);
            CREATE INDEX IF NOT EXISTS idx_p2p_completed ON p2p_trades(completed_at);
            CREATE INDEX IF NOT EXISTS idx_p2p_status ON p2p_trades(status);
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

    # --- P2P Trade Sync (Noones) ---

    def upsert_p2p_trade(self, trade: dict) -> bool:
        """
        Insert or update a P2P trade from Noones.
        Returns True if this was a new trade, False if updated.
        """
        trade_hash = trade["trade_hash"]
        existing = self.conn.execute(
            "SELECT id FROM p2p_trades WHERE trade_hash = ?", (trade_hash,)
        ).fetchone()

        opened_at = trade.get("opened_at", 0)
        paid_at = trade.get("paid_at")
        released_at = trade.get("released_at")
        completed_at = trade.get("completed_at")

        # Calculate confirmation lag: paid → released
        confirmation_lag = None
        if paid_at and released_at:
            confirmation_lag = released_at - paid_at

        if existing:
            # Preserve existing non-zero fee if new value is 0 (list endpoint lacks fee data)
            new_fee = trade.get("fee_usd", 0) or 0
            self.conn.execute(
                """UPDATE p2p_trades SET
                    status = ?, paid_at = ?, released_at = ?, completed_at = ?,
                    confirmation_lag_sec = ?, profit_usd = ?,
                    fee_usd = CASE WHEN ? > 0 THEN ? ELSE fee_usd END,
                    synced_at = ?
                WHERE trade_hash = ?""",
                (
                    trade["status"], paid_at, released_at, completed_at,
                    confirmation_lag, trade.get("profit_usd"),
                    new_fee, new_fee, time.time(), trade_hash,
                ),
            )
            self.conn.commit()
            return False

        self.conn.execute(
            """INSERT INTO p2p_trades
            (trade_hash, status, trade_type, asset, fiat_amount, fiat_currency,
             crypto_amount, fiat_rate, counterparty, payment_method,
             opened_at, paid_at, released_at, completed_at,
             confirmation_lag_sec, profit_usd, fee_usd, offer_hash, synced_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trade_hash, trade["status"], trade.get("trade_type", "sell"),
                trade.get("asset", "USDT"),
                trade["fiat_amount"], trade["fiat_currency"],
                trade["crypto_amount"], trade.get("fiat_rate", 0),
                trade.get("counterparty"), trade.get("payment_method"),
                opened_at, paid_at, released_at, completed_at,
                confirmation_lag, trade.get("profit_usd"),
                trade.get("fee_usd", 0), trade.get("offer_hash"),
                time.time(),
            ),
        )
        self.conn.commit()
        logger.info(f"Synced P2P trade {trade_hash}: {trade['fiat_amount']} {trade['fiat_currency']}")
        return True

    def get_p2p_trades(self, limit: int = 50, days: int | None = None) -> list[dict]:
        """Get P2P trades, optionally filtered by recency."""
        if days:
            cutoff = time.time() - (days * 86400)
            rows = self.conn.execute(
                "SELECT * FROM p2p_trades WHERE completed_at > ? ORDER BY completed_at DESC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM p2p_trades ORDER BY opened_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_p2p_pnl(self, days: int = 30) -> dict:
        """P&L summary from P2P trades."""
        cutoff = time.time() - (days * 86400)
        rows = self.conn.execute(
            "SELECT * FROM p2p_trades WHERE status = 'completed' AND completed_at > ?",
            (cutoff,),
        ).fetchall()
        trades = [dict(r) for r in rows]

        total_volume_fiat = sum(t["fiat_amount"] for t in trades)
        total_crypto = sum(t["crypto_amount"] for t in trades)
        total_profit = sum(t["profit_usd"] or 0 for t in trades)
        total_fees = sum(t["fee_usd"] or 0 for t in trades)
        avg_lag = (
            sum(t["confirmation_lag_sec"] or 0 for t in trades) / len(trades)
            if trades else 0
        )

        # Daily breakdown
        daily: dict[str, dict] = {}
        for t in trades:
            ts = t["completed_at"] or t["opened_at"]
            day = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            if day not in daily:
                daily[day] = {"date": day, "cycles": 0, "profit": 0.0, "volume": 0.0}
            daily[day]["cycles"] += 1
            daily[day]["profit"] += t["profit_usd"] or 0
            daily[day]["volume"] += t["fiat_amount"]

        daily_pnl = sorted(daily.values(), key=lambda x: x["date"])

        # Counterparty breakdown
        counterparties: dict[str, dict] = {}
        for t in trades:
            cp = t["counterparty"] or "unknown"
            if cp not in counterparties:
                counterparties[cp] = {"name": cp, "trades": 0, "volume": 0.0, "avg_lag_sec": 0.0, "lags": []}
            counterparties[cp]["trades"] += 1
            counterparties[cp]["volume"] += t["fiat_amount"]
            if t["confirmation_lag_sec"]:
                counterparties[cp]["lags"].append(t["confirmation_lag_sec"])

        for cp in counterparties.values():
            cp["avg_lag_sec"] = sum(cp["lags"]) / len(cp["lags"]) if cp["lags"] else 0
            del cp["lags"]

        # Payment method breakdown — with profit, fees, and volume per method
        methods: dict[str, dict] = {}
        for t in trades:
            m = t["payment_method"] or "unknown"
            if m not in methods:
                methods[m] = {"count": 0, "volume": 0.0, "profit": 0.0, "fees": 0.0}
            methods[m]["count"] += 1
            methods[m]["volume"] += t["fiat_amount"]
            methods[m]["profit"] += t["profit_usd"] or 0
            methods[m]["fees"] += t["fee_usd"] or 0

        actual_days = max(1, len(daily))

        return {
            "period_days": days,
            "total_trades": len(trades),
            "total_volume_fiat": round(total_volume_fiat, 2),
            "total_crypto_sold": round(total_crypto, 6),
            "total_profit_usd": round(total_profit, 4),
            "total_fees": round(total_fees, 4),
            "net_profit_usd": round(total_profit - total_fees, 4),
            "avg_confirmation_lag_sec": round(avg_lag, 1),
            "trades_per_day": round(len(trades) / actual_days, 1),
            "avg_profit_per_trade": round(total_profit / len(trades), 4) if trades else 0,
            "daily_pnl": daily_pnl,
            "counterparties": list(counterparties.values()),
            "payment_methods": methods,
        }

    def get_p2p_trade_count(self) -> int:
        """Get total number of synced P2P trades."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM p2p_trades").fetchone()
        return row["cnt"] if row else 0

    def close(self):
        self.conn.close()
