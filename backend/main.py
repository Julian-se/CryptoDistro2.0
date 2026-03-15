"""
CryptoDistro 2.0 — FastAPI backend entry point.

Lifespan:
  - Initializes all engine singletons (or sets demo mode)
  - Creates/migrates SQLite tables (WAL mode)
  - Launches two background tasks:
      · every 60s: premium scan → feedforward controllers → WS broadcast
      · every 15s: BTC spot price broadcast
  - Graceful shutdown: cancels background tasks

WebSocket: /ws
API:       /api/*
"""

import asyncio
import logging
import os
import sqlite3
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

import backend.api.deps as deps
from backend.api.routes import dashboard, health, intelligence, markets, refill, simulation, trades
from backend.api.websocket.events import (
    BTC_PRICE, BALANCE_UPDATE, CONTROLLER_SIGNAL, MARKET_UPDATE, TRADE_LOGGED,
)
from backend.api.websocket.manager import ConnectionManager
from backend.schemas.dashboard import (
    ControllerSignals, DashboardSnapshot, PlatformBalance, MarketSummary, PaymentMethod,
)
from src.core.config import get_config

logger = logging.getLogger(__name__)

# ── Database setup ─────────────────────────────────────────────────────────────

_NEW_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS scan_log (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        currency    TEXT    NOT NULL,
        premium_pct REAL    NOT NULL,
        btc_spot    REAL    NOT NULL,
        action      TEXT    NOT NULL,
        offer_count INTEGER NOT NULL DEFAULT 0,
        scanned_at  REAL    NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS balance_log (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        platform   TEXT NOT NULL,
        btc        REAL NOT NULL DEFAULT 0,
        usdt       REAL NOT NULL DEFAULT 0,
        total_usd  REAL NOT NULL DEFAULT 0,
        logged_at  REAL NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_scan_log_currency ON scan_log(currency, scanned_at)",
    "CREATE INDEX IF NOT EXISTS idx_balance_log_platform ON balance_log(platform, logged_at)",
]


def _init_db(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    for sql in _NEW_TABLES_SQL:
        conn.execute(sql)
    conn.commit()
    conn.close()
    logger.info(f"Database ready: {db_path}")


# ── Singleton initialization ───────────────────────────────────────────────────

def _try_init_real_mode(cfg: dict) -> bool:
    """
    Attempt to initialize all connectors with real API keys.
    Returns True if successful (real mode), False if any key is missing.
    """
    binance_key = cfg.get("binance", {}).get("api_key", "")
    noones_key = cfg.get("noones", {}).get("api_key", "")

    if not binance_key or not noones_key:
        return False

    try:
        from src.connectors.binance import BinanceConnector
        from src.connectors.noones import NoonesConnector
        from src.connectors.fxrates import FxRatesConnector
        from src.core.premium_monitor import PremiumMonitor
        from src.core.balance_manager import BalanceManager
        from src.core.trade_tracker import TradeTracker
        from src.intelligence.agent import IntelligenceAgent

        binance = BinanceConnector()
        noones = NoonesConnector()
        fx = FxRatesConnector()
        pm = PremiumMonitor(binance=binance, noones=noones, fx=fx)
        bm = BalanceManager(binance=binance, noones=noones)
        tt = TradeTracker()

        deps._binance = binance
        deps._noones = noones
        deps._premium_monitor = pm
        deps._balance_manager = bm
        deps._trade_tracker = tt

        # Intelligence agent is optional (Cerebras key may be absent)
        try:
            agent = IntelligenceAgent(
                premium_monitor=pm,
                balance_manager=bm,
                trade_tracker=tt,
                binance=binance,
            )
            deps._intelligence = agent
        except ValueError:
            logger.warning("CEREBRAS_API_KEY not set — intelligence agent disabled")

        logger.info("Real mode: all connectors initialized")
        return True

    except Exception as e:
        logger.warning(f"Real mode init failed ({e}) — falling back to demo mode")
        return False


# ── Background tasks ───────────────────────────────────────────────────────────

async def _scan_loop():
    """Every 60s: scan premiums, run feedforward controllers, broadcast."""
    from backend.controllers.inventory_controller import InventoryController
    from backend.controllers.spread_controller import SpreadController
    from backend.controllers.velocity_controller import VelocityController

    inv_ctrl = InventoryController()
    spread_ctrl = SpreadController()
    vel_ctrl = VelocityController()

    cfg = get_config()
    db_path = cfg["database"]["path"]
    markets_cfg = cfg.get("premium_monitor", {}).get("markets", [])

    while True:
        try:
            await asyncio.sleep(60)
            t0 = time.time()

            # ── Premium scan ────────────────────────────────────────────
            pm = deps.get_premium_monitor()
            if pm and not deps.is_demo_mode():
                try:
                    raw_snap = pm.scan_all()
                    deps._scan_count += 1

                    # Persist to scan_log
                    conn = sqlite3.connect(db_path)
                    for m in raw_snap.markets:
                        conn.execute(
                            "INSERT INTO scan_log (currency, premium_pct, btc_spot, action, offer_count, scanned_at) "
                            "VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                m.currency,
                                float(m.premium_pct),
                                float(raw_snap.btc_spot_usd),
                                m.action.value,
                                m.offer_count,
                                raw_snap.scanned_at,
                            ),
                        )
                    conn.commit()
                    conn.close()

                    # Convert to API schema markets
                    market_premiums = {m.currency: float(m.premium_pct) for m in raw_snap.markets}

                    # ── Spread controller ──────────────────────────────
                    spread_signal = spread_ctrl.run(market_premiums=market_premiums)

                    # ── Velocity controller ────────────────────────────
                    bm = deps.get_balance_manager()
                    noones_usd = 0.0
                    refill_statuses = {}
                    if bm:
                        try:
                            cap = bm.get_snapshot()
                            nb = cap.balances.get("noones")
                            noones_usd = float(nb.total_usd) if nb else 0.0
                        except Exception:
                            pass
                    vel_signal = vel_ctrl.run(
                        noones_balance_usd=noones_usd,
                        market_configs=markets_cfg,
                        market_premiums=market_premiums,
                        refill_statuses=refill_statuses,
                    )

                    # ── Inventory controller ───────────────────────────
                    cutoff = time.time() - 86400
                    conn2 = sqlite3.connect(db_path)
                    conn2.row_factory = sqlite3.Row
                    rows = conn2.execute(
                        "SELECT logged_at, btc FROM balance_log WHERE platform='noones' AND logged_at>? ORDER BY logged_at",
                        (cutoff,),
                    ).fetchall()
                    conn2.close()
                    balance_entries = [dict(r) for r in rows]
                    inv_signal = inv_ctrl.run(
                        balance_log_entries=balance_entries,
                        btc_price=float(raw_snap.btc_spot_usd),
                    )

                    # Build controller signals
                    signals = ControllerSignals(
                        inventory=inv_signal,
                        spread=spread_signal,
                        velocity=vel_signal,
                        last_run_at=time.time(),
                    )
                    deps._last_controller_signals = signals
                    deps._btc_spot = float(raw_snap.btc_spot_usd)

                    # Build DashboardSnapshot
                    from backend.api.routes.dashboard import DEMO_MARKETS
                    from backend.schemas.dashboard import ActiveTrade

                    balances_schema: dict[str, PlatformBalance] = {}
                    if bm:
                        try:
                            cap2 = bm.get_snapshot()
                            for plat, bal in cap2.balances.items():
                                balances_schema[plat] = PlatformBalance(
                                    platform=plat,
                                    btc=float(bal.btc),
                                    usdt=float(bal.usdt),
                                    total_usd=float(bal.total_usd),
                                    updated_at=bal.updated_at,
                                )
                                # Log balance for inventory controller
                                conn3 = sqlite3.connect(db_path)
                                conn3.execute(
                                    "INSERT INTO balance_log (platform, btc, usdt, total_usd, logged_at) VALUES (?,?,?,?,?)",
                                    (plat, float(bal.btc), float(bal.usdt), float(bal.total_usd), time.time()),
                                )
                                conn3.commit()
                                conn3.close()
                        except Exception as e:
                            logger.warning(f"Balance snapshot failed: {e}")

                    # API market schemas from raw scan
                    api_markets = []
                    for m in raw_snap.markets:
                        pms = [
                            PaymentMethod(slug=p["slug"], label=p["label"], risk=p.get("risk", "low"))
                            for p in m.payment_methods
                        ]
                        api_markets.append(MarketSummary(
                            name=m.name, flag=m.flag, currency=m.currency,
                            premium_pct=float(m.premium_pct),
                            action=m.action.value,
                            suggested_margin=m.suggested_margin,
                            offer_count=m.offer_count,
                            fx_rate=m.fx_rate,
                            refill_status="verified",
                            payment_methods=pms,
                        ))

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
                        )
                        for c in open_cycles
                    ]

                    snapshot = DashboardSnapshot(
                        btc_spot_usd=float(raw_snap.btc_spot_usd),
                        markets=api_markets,
                        balances=balances_schema,
                        active_trades=active_trades,
                        open_cycles=len(open_cycles),
                        controller_signals=signals,
                        scanned_at=raw_snap.scanned_at,
                    )
                    deps._last_snapshot = snapshot

                    # Broadcast
                    ws = deps.get_ws_manager()
                    if ws:
                        await ws.broadcast_event(MARKET_UPDATE, [m.model_dump() for m in api_markets])
                        await ws.broadcast_event(CONTROLLER_SIGNAL, signals.model_dump())
                        await ws.broadcast_event(BALANCE_UPDATE, {k: v.model_dump() for k, v in balances_schema.items()})

                    logger.info(f"Scan complete in {(time.time()-t0)*1000:.0f}ms — {len(api_markets)} markets")

                except Exception as e:
                    deps._scan_errors += 1
                    logger.error(f"Scan loop error: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Scan loop outer error: {e}")


async def _btc_price_loop():
    """Every 15s: broadcast current BTC spot price."""
    while True:
        try:
            await asyncio.sleep(15)
            price = deps._btc_spot
            if price > 0:
                ws = deps.get_ws_manager()
                if ws:
                    await ws.broadcast_event(BTC_PRICE, {"price": price, "ts": time.time()})
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"BTC price broadcast error: {e}")


# ── Lifespan ────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────────────
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    deps._start_time = time.time()
    deps._ws_manager = ConnectionManager()

    cfg = get_config()
    db_path = cfg["database"]["path"]
    _init_db(db_path)

    is_real = _try_init_real_mode(cfg)
    deps._demo_mode = not is_real

    if deps._demo_mode:
        logger.info("Demo mode active — no API keys configured")
        # Seed a plausible BTC price (updated when real mode comes online)
        deps._btc_spot = 97500.0

    # Background tasks
    scan_task = asyncio.create_task(_scan_loop())
    price_task = asyncio.create_task(_btc_price_loop())

    logger.info("CryptoDistro 2.0 API started")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────
    scan_task.cancel()
    price_task.cancel()
    try:
        await asyncio.gather(scan_task, price_task, return_exceptions=True)
    except Exception:
        pass
    logger.info("CryptoDistro 2.0 API shutdown complete")


# ── App factory ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="CryptoDistro 2.0",
    description="P2P Bitcoin on/off-ramp operator dashboard — emerging markets",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers
_api_routers = [
    dashboard.router,
    health.router,
    intelligence.router,
    markets.router,
    refill.router,
    simulation.router,
    trades.router,
]
for router in _api_routers:
    app.include_router(router, prefix="/api")


# ── WebSocket endpoint ──────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    manager = deps.get_ws_manager()
    await manager.connect(websocket)
    try:
        # Send initial snapshot on connect
        snapshot = deps.get_last_snapshot()
        if snapshot:
            await websocket.send_json({
                "type": "snapshot",
                "data": snapshot.model_dump(),
                "timestamp": time.time(),
            })
        elif deps.is_demo_mode():
            from backend.api.routes.dashboard import DEMO_MARKETS
            await websocket.send_json({
                "type": "snapshot",
                "data": {
                    "btc_spot_usd": deps._btc_spot,
                    "markets": [m.model_dump() for m in DEMO_MARKETS],
                    "demo": True,
                },
                "timestamp": time.time(),
            })

        # Message loop: handle client commands (subscribe_logs, etc.)
        async for message in websocket.iter_json():
            cmd = message.get("cmd")
            if cmd == "subscribe_logs":
                manager.subscribe_logs(websocket)
            elif cmd == "unsubscribe_logs":
                manager.unsubscribe_logs(websocket)
            elif cmd == "ping":
                await websocket.send_json({"type": "pong", "ts": time.time()})

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.debug(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


# ── Root ─────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "service": "CryptoDistro 2.0 API",
        "version": "2.0.0",
        "demo": deps.is_demo_mode(),
        "docs": "/docs",
        "ws": "/ws",
    }
