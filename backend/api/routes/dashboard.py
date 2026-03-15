import time
from fastapi import APIRouter
from backend.schemas.dashboard import DashboardSnapshot, MarketSummary, PlatformBalance, ActiveTrade, ControllerSignals, PaymentMethod
import backend.api.deps as deps
from src.core.config import get_config

router = APIRouter()

# Demo data for when no API keys are configured
DEMO_MARKETS = [
    MarketSummary(name="Nigeria", flag="🇳🇬", currency="NGN", premium_pct=7.8, action="ACT_NOW",
                  suggested_margin=6.2, offer_count=24, fx_rate=1620.5, refill_status="verified",
                  payment_methods=[PaymentMethod(slug="first-bank-of-nigeria", label="First Bank", risk="low"),
                                   PaymentMethod(slug="opay", label="OPay", risk="low"),
                                   PaymentMethod(slug="gtbank-guaranty-trust-bank", label="GTBank", risk="low")]),
    MarketSummary(name="Argentina", flag="🇦🇷", currency="ARS", premium_pct=9.4, action="ACT_NOW",
                  suggested_margin=7.5, offer_count=18, fx_rate=1050.2, refill_status="partial",
                  payment_methods=[PaymentMethod(slug="mercado-pago", label="MercadoPago", risk="medium"),
                                   PaymentMethod(slug="cbu-cvu", label="CBU/CVU", risk="low")]),
    MarketSummary(name="Venezuela", flag="🇻🇪", currency="VES", premium_pct=11.2, action="WATCH",
                  suggested_margin=9.0, offer_count=8, fx_rate=36.8, refill_status="partial",
                  payment_methods=[PaymentMethod(slug="pago-movil", label="Pago Movil", risk="low"),
                                   PaymentMethod(slug="zelle", label="Zelle", risk="medium")]),
    MarketSummary(name="Kenya", flag="🇰🇪", currency="KES", premium_pct=6.1, action="WATCH",
                  suggested_margin=4.9, offer_count=12, fx_rate=129.4, refill_status="verified",
                  payment_methods=[PaymentMethod(slug="mpesa", label="M-Pesa", risk="low"),
                                   PaymentMethod(slug="airtel-money-kenya", label="Airtel Money", risk="low")]),
    MarketSummary(name="Sverige", flag="🇸🇪", currency="SEK", premium_pct=4.2, action="AVOID",
                  suggested_margin=3.4, offer_count=5, fx_rate=10.3, refill_status="partial",
                  payment_methods=[PaymentMethod(slug="swish", label="Swish", risk="low"),
                                   PaymentMethod(slug="revolut", label="Revolut", risk="low")]),
]


@router.get("/dashboard/snapshot", response_model=DashboardSnapshot)
async def get_dashboard_snapshot():
    demo = deps.is_demo_mode()

    if demo:
        return DashboardSnapshot(
            btc_spot_usd=deps._btc_spot or 97500.0,
            markets=DEMO_MARKETS,
            balances={
                "binance": PlatformBalance(platform="binance", btc=0.0025, usdt=250.0, total_usd=493.75, updated_at=time.time()),
                "noones": PlatformBalance(platform="noones", btc=0.0025, usdt=0.0, total_usd=243.75, updated_at=time.time()),
            },
            active_trades=[],
            open_cycles=0,
            controller_signals=deps.get_controller_signals(),
            scanned_at=time.time(),
        )

    # Real mode — read from last scan results
    snapshot = deps.get_last_snapshot()
    if snapshot:
        return snapshot

    # Fallback: build from live data
    tracker = deps.get_trade_tracker()
    open_cycles = []
    if tracker:
        try:
            open_cycles = tracker.get_open_cycles()
        except Exception:
            pass

    active_trades = [
        ActiveTrade(
            cycle_id=c.get("id", ""),
            started_at=c.get("started_at", 0),
            status=c.get("status", "open"),
            buy_platform=c.get("buy_platform", ""),
            sell_platform=c.get("sell_platform", ""),
            asset=c.get("asset", "BTC"),
            notes=c.get("notes"),
        )
        for c in open_cycles
    ]

    balances: dict[str, PlatformBalance] = {}
    bm = deps.get_balance_manager()
    if bm:
        try:
            cap = bm.get_snapshot()
            for plat, bal in cap.balances.items():
                balances[plat] = PlatformBalance(
                    platform=plat,
                    btc=float(bal.btc),
                    usdt=float(bal.usdt),
                    total_usd=float(bal.total_usd),
                    updated_at=bal.updated_at,
                )
        except Exception:
            pass

    return DashboardSnapshot(
        btc_spot_usd=deps._btc_spot or 0.0,
        markets=DEMO_MARKETS,
        balances=balances,
        active_trades=active_trades,
        open_cycles=len(open_cycles),
        controller_signals=deps.get_controller_signals(),
        scanned_at=time.time(),
    )
