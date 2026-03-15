import time
import sqlite3
from fastapi import APIRouter
from backend.schemas.health import HealthResponse, HealthComponent, ScanMetrics
import backend.api.deps as deps
from src.core.config import get_config

router = APIRouter()


def _check_component(name: str, fn) -> HealthComponent:
    t0 = time.time()
    try:
        fn()
        latency = (time.time() - t0) * 1000
        status = "slow" if latency > 2000 else "ok"
        return HealthComponent(status=status, latency_ms=round(latency, 1), last_check_at=time.time())
    except Exception as e:
        return HealthComponent(
            status="error",
            latency_ms=round((time.time() - t0) * 1000, 1),
            last_check_at=time.time(),
            error=str(e)[:200],
        )


@router.get("/health", response_model=HealthResponse)
async def get_health():
    demo = deps.is_demo_mode()

    components: dict[str, HealthComponent] = {}

    if not demo:
        binance = deps.get_binance()
        if binance:
            components["binance_api"] = _check_component(
                "binance", lambda: binance.get_spot_price("BTCUSDT")
            )
        else:
            components["binance_api"] = HealthComponent(
                status="error", latency_ms=0, last_check_at=time.time(), error="Not initialized"
            )

        noones = deps.get_noones()
        if noones:
            components["noones_api"] = _check_component(
                "noones", lambda: noones.get_profile()
            )
        else:
            components["noones_api"] = HealthComponent(
                status="error", latency_ms=0, last_check_at=time.time(), error="Not initialized"
            )
    else:
        components["binance_api"] = HealthComponent(status="ok", latency_ms=1.0, last_check_at=time.time())
        components["noones_api"] = HealthComponent(status="ok", latency_ms=1.0, last_check_at=time.time())

    # Database check
    try:
        cfg = get_config()
        db_path = cfg["database"]["path"]
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        components["database"] = HealthComponent(status="ok", latency_ms=1.0, last_check_at=time.time())
    except Exception as e:
        components["database"] = HealthComponent(
            status="error", latency_ms=0, last_check_at=time.time(), error=str(e)[:200]
        )

    # FX rates check
    try:
        import httpx
        t0 = time.time()
        r = httpx.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        r.raise_for_status()
        latency = (time.time() - t0) * 1000
        components["fx_rates"] = HealthComponent(
            status="slow" if latency > 2000 else "ok",
            latency_ms=round(latency, 1),
            last_check_at=time.time(),
        )
    except Exception as e:
        components["fx_rates"] = HealthComponent(
            status="error", latency_ms=0, last_check_at=time.time(), error=str(e)[:100]
        )

    # Intelligence
    agent = deps.get_intelligence()
    components["intelligence"] = HealthComponent(
        status="ok" if agent else "error",
        latency_ms=0,
        last_check_at=time.time(),
        error=None if agent else "CEREBRAS_API_KEY not configured",
    )

    overall_status = "healthy"
    for comp in components.values():
        if comp.status == "error":
            overall_status = "degraded"
            break

    scan_count = deps._scan_count
    scan_errors = deps._scan_errors
    uptime = time.time() - deps._start_time if deps._start_time else 0

    return HealthResponse(
        status=overall_status,
        components=components,
        scan_metrics=ScanMetrics(
            last_scan_at=0,
            scan_interval_sec=60,
            scans_last_hour=scan_count,
            scan_errors_last_hour=scan_errors,
        ),
        api_latency_ms={k: v.latency_ms for k, v in components.items()},
        uptime_sec=uptime,
    )
