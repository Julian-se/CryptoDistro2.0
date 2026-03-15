from fastapi import APIRouter, Query
import backend.api.deps as deps

router = APIRouter()


@router.get("/trades")
async def get_trades(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    days: int = Query(default=30),
):
    tracker = deps.get_trade_tracker()
    if not tracker:
        return {"trades": [], "total": 0}
    try:
        trades = tracker.get_recent_trades(limit=limit)
        return {"trades": trades, "total": len(trades)}
    except Exception:
        return {"trades": [], "total": 0}


@router.get("/trades/pnl")
async def get_trades_pnl(days: int = Query(default=30)):
    tracker = deps.get_trade_tracker()
    if not tracker:
        return {
            "period_days": days, "total_cycles": 0,
            "total_gross_profit": "0", "total_fees": "0", "total_net_profit": "0",
            "avg_cycle_duration_sec": 0, "avg_profit_per_cycle": "0", "cycles_per_day": 0,
            "daily_pnl": [],
        }
    try:
        summary = tracker.get_pnl_summary(days=days)
        return {**{k: str(v) if hasattr(v, '__round__') else v for k, v in summary.items()}, "daily_pnl": []}
    except Exception:
        return {"period_days": days, "total_cycles": 0, "total_net_profit": "0", "daily_pnl": []}


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
