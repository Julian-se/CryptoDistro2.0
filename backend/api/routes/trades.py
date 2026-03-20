import logging
from fastapi import APIRouter, Query
import backend.api.deps as deps

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/trades")
async def get_trades(
    limit: int = Query(default=50, le=200),
    days: int = Query(default=30),
):
    """Get P2P trades (synced from Noones). Falls back to legacy trades if none."""
    tracker = deps.get_trade_tracker()
    if not tracker:
        return {"trades": [], "total": 0}
    try:
        p2p_trades = tracker.get_p2p_trades(limit=limit, days=days)
        if p2p_trades:
            return {"trades": p2p_trades, "total": len(p2p_trades)}
        # Fallback to legacy trades table
        trades = tracker.get_recent_trades(limit=limit)
        return {"trades": trades, "total": len(trades)}
    except Exception as e:
        logger.error(f"Failed to get trades: {e}")
        return {"trades": [], "total": 0}


@router.get("/trades/pnl")
async def get_trades_pnl(days: int = Query(default=30)):
    """Get P&L summary from P2P trades."""
    tracker = deps.get_trade_tracker()
    if not tracker:
        return _empty_pnl(days)
    try:
        # Try P2P pnl first
        p2p_count = tracker.get_p2p_trade_count()
        if p2p_count > 0:
            return tracker.get_p2p_pnl(days=days)
        # Fallback to legacy cycles
        summary = tracker.get_pnl_summary(days=days)
        return {
            **{k: str(v) if hasattr(v, '__round__') else v for k, v in summary.items()},
            "daily_pnl": [],
        }
    except Exception as e:
        logger.error(f"Failed to get PnL: {e}")
        return _empty_pnl(days)


@router.get("/trades/cycles")
async def get_cycles(status: str = Query(default="open")):
    tracker = deps.get_trade_tracker()
    if not tracker:
        return []
    try:
        if status == "open":
            return tracker.get_open_cycles()
        return []
    except Exception:
        return []


@router.post("/trades/sync")
async def sync_trades():
    """Pull completed trades from Noones and sync to local database."""
    noones = deps.get_noones()
    tracker = deps.get_trade_tracker()
    fx = deps.get_fx()

    if not noones or not tracker:
        return {"error": "Noones connector or trade tracker not initialized", "synced": 0}

    try:
        from src.core.trade_sync import sync_completed_trades
        result = sync_completed_trades(
            noones, tracker,
            fx=fx,
            btc_spot_usd=deps._btc_spot,
        )
        return result
    except Exception as e:
        logger.error(f"Trade sync failed: {e}")
        return {"error": str(e), "synced": 0}


def _empty_pnl(days: int) -> dict:
    return {
        "period_days": days, "total_trades": 0,
        "total_volume_fiat": 0, "total_crypto_sold": 0,
        "total_profit_usd": 0, "total_fees": 0, "net_profit_usd": 0,
        "avg_confirmation_lag_sec": 0, "trades_per_day": 0,
        "avg_profit_per_trade": 0, "daily_pnl": [],
        "counterparties": [], "payment_methods": {},
    }
