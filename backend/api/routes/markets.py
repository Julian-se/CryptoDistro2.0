import time
import sqlite3
from fastapi import APIRouter, HTTPException
from backend.schemas.market import MarketDetail, PremiumPoint, CompetitorOffer
from backend.schemas.dashboard import MarketSummary, PaymentMethod
from backend.api.routes.dashboard import DEMO_MARKETS
import backend.api.deps as deps
from src.core.config import get_config

router = APIRouter()

VALID_CURRENCIES = {"NGN", "ARS", "VES", "KES", "SEK"}


@router.get("/markets")
async def get_markets():
    snapshot = deps.get_last_snapshot()
    if snapshot:
        return snapshot.markets
    return DEMO_MARKETS


@router.get("/markets/{currency}", response_model=MarketDetail)
async def get_market_detail(currency: str):
    currency = currency.upper()
    if currency not in VALID_CURRENCIES:
        raise HTTPException(status_code=404, detail=f"Unknown market: {currency}")

    # Find market summary
    snapshot = deps.get_last_snapshot()
    markets = snapshot.markets if snapshot else DEMO_MARKETS
    market = next((m for m in markets if m.currency == currency), None)
    if not market:
        market = next((m for m in DEMO_MARKETS if m.currency == currency), DEMO_MARKETS[0])

    # Premium history from scan_log
    history: list[PremiumPoint] = []
    try:
        cfg = get_config()
        conn = sqlite3.connect(cfg["database"]["path"])
        conn.row_factory = sqlite3.Row
        cutoff = time.time() - 86400  # last 24h
        rows = conn.execute(
            "SELECT * FROM scan_log WHERE currency=? AND scanned_at>? ORDER BY scanned_at",
            (currency, cutoff),
        ).fetchall()
        conn.close()
        history = [
            PremiumPoint(
                timestamp=r["scanned_at"],
                premium_pct=r["premium_pct"],
                btc_spot=r["btc_spot"],
                action=r["action"],
                offer_count=r["offer_count"],
            )
            for r in rows
        ]
    except Exception:
        pass

    # Competitor offers — from live monitor or empty
    competitors: dict[str, list[CompetitorOffer]] = {"noones": [], "binance_p2p": []}
    pm = deps.get_premium_monitor()
    if pm and not deps.is_demo_mode():
        try:
            noones_offers = pm.noones.get_offers(
                offer_type="sell", currency_code=currency, crypto_currency_code="BTC", limit=10
            )
            competitors["noones"] = [
                CompetitorOffer(
                    seller=o["seller"], price=float(o["price"]),
                    margin=float(o.get("margin", 0)) if o.get("margin") is not None else None,
                    trades=o["seller_trades"], score=float(o["seller_score"]),
                    method=o["payment_method"],
                    min_amount=float(o["min_amount"]), max_amount=float(o["max_amount"]),
                    platform="noones",
                )
                for o in noones_offers
            ]
        except Exception:
            pass

    return MarketDetail(market=market, competitors=competitors, premium_history=history)
