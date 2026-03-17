"""
CryptoDistro 2.0 — MCP stdio server for Claude terminal diagnostics.

Connect from Claude Code (or any MCP client) via stdio transport.
Exposes 5 read-only tools that let Claude inspect the live system.

Usage (stdio):
    python -m backend.mcp_server.server

Add to Claude Code ~/.claude/settings.json:
    {
      "mcpServers": {
        "cryptodistro": {
          "command": "python",
          "args": ["-m", "backend.mcp_server.server"],
          "cwd": "/path/to/CryptoDistro2.0"
        }
      }
    }
"""

import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
from pathlib import Path

# Ensure project root is on the path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
logger = logging.getLogger(__name__)

server = Server("cryptodistro")


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_db_path() -> str:
    try:
        from src.core.config import get_config
        return get_config()["database"]["path"]
    except Exception:
        return str(_PROJECT_ROOT / "db" / "trades.db")


def _api_base() -> str:
    return os.getenv("CRYPTODISTRO_API_URL", "http://localhost:8000")


async def _http_get(path: str) -> dict:
    """Async HTTP GET to the running backend API."""
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{_api_base()}{path}")
        resp.raise_for_status()
        return resp.json()


async def _http_post(path: str, payload: dict) -> dict:
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{_api_base()}{path}", json=payload)
        resp.raise_for_status()
        return resp.json()


# ── Tool definitions ─────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_system_status",
            description=(
                "Get full system health: API component statuses (Binance, Noones, DB, FX), "
                "uptime, scan metrics, demo mode flag, BTC spot price, and feedforward controller signals."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        Tool(
            name="run_simulation",
            description=(
                "Run the CryptoDistro P2P cycle simulation. "
                "Parameters: spread (market premium %, default 9), "
                "fiat_minutes (fiat verification time, default 20), "
                "active_hours (trading hours per day, default 10), "
                "days (simulation period, default 30), runs (Monte Carlo iterations, default 100). "
                "Returns capital curve, P10/P90 confidence bands, milestones, and stats."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "spread": {"type": "number", "description": "Market premium %", "default": 9},
                    "fiat_minutes": {"type": "number", "description": "Fiat verification minutes", "default": 20},
                    "active_hours": {"type": "number", "description": "Active hours per day", "default": 10},
                    "days": {"type": "integer", "description": "Simulation days", "default": 30},
                    "runs": {"type": "integer", "description": "Monte Carlo runs", "default": 100},
                    "scenario": {
                        "type": "string",
                        "enum": ["conservative", "realistic", "optimistic"],
                        "description": "Use a preset scenario (overrides other params)",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_market_data",
            description=(
                "Get live market data for all configured markets (or a specific currency). "
                "Returns: premium %, action signal (ACT_NOW/WATCH/AVOID), offer count, FX rate, "
                "suggested margin, payment methods. Pass currency='NGN' for a single market."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "Optional 3-letter currency code (NGN, ARS, VES, KES, SEK). Omit for all markets.",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="trigger_refill_scan",
            description=(
                "Trigger a fresh BTC refill pipeline scan for a specific payment method or all methods. "
                "Uses the IntelligenceAgent to verify routes. "
                "Pass method='all' to scan everything, or e.g. method='M-Pesa' for a single method. "
                "Returns the pipeline card with route, fees, KYC level, and status."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "Payment method name or 'all'. E.g. 'M-Pesa', 'OPay', 'Zelle', 'all'",
                        "default": "all",
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="get_trade_history",
            description=(
                "Query trade history and PnL from the SQLite database. "
                "Returns recent completed trades and a PnL summary "
                "(total cycles, gross profit, fees, net profit, cycles/day)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of recent trades to return (default 20, max 100)",
                        "default": 20,
                    },
                    "days": {
                        "type": "integer",
                        "description": "PnL summary period in days (default 30)",
                        "default": 30,
                    },
                },
                "required": [],
            },
        ),
    ]


# ── Tool handlers ─────────────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "get_system_status":
            result = await _tool_system_status()
        elif name == "run_simulation":
            result = await _tool_run_simulation(arguments)
        elif name == "get_market_data":
            result = await _tool_get_market_data(arguments)
        elif name == "trigger_refill_scan":
            result = await _tool_refill_scan(arguments)
        elif name == "get_trade_history":
            result = await _tool_trade_history(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        logger.error(f"Tool {name} error: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]


async def _tool_system_status() -> dict:
    try:
        health = await _http_get("/api/health")
        snapshot_req = await _http_get("/api/dashboard/snapshot")
        return {
            "health": health,
            "btc_spot_usd": snapshot_req.get("btc_spot_usd"),
            "demo_mode": snapshot_req.get("demo", False),
            "markets_count": len(snapshot_req.get("markets", [])),
            "open_cycles": snapshot_req.get("open_cycles", 0),
            "controller_signals": snapshot_req.get("controller_signals"),
            "timestamp": time.time(),
        }
    except Exception as e:
        # Fallback: read DB directly
        db_path = _get_db_path()
        db_ok = False
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("SELECT 1").fetchone()
            conn.close()
            db_ok = True
        except Exception:
            pass
        return {
            "api_reachable": False,
            "api_url": _api_base(),
            "database_ok": db_ok,
            "error": str(e),
            "hint": "Start the backend: uvicorn backend.main:app --reload",
        }


async def _tool_run_simulation(args: dict) -> dict:
    # Map scenario shorthand to params
    scenario = args.get("scenario")
    SCENARIOS = {
        "conservative": {"spread": 6.0, "fiat_minutes": 25, "active_hours": 8},
        "realistic":    {"spread": 9.0, "fiat_minutes": 20, "active_hours": 10},
        "optimistic":   {"spread": 12.0, "fiat_minutes": 15, "active_hours": 12},
    }
    if scenario and scenario in SCENARIOS:
        params = {**SCENARIOS[scenario], "days": args.get("days", 30), "runs": args.get("runs", 100)}
    else:
        params = {
            "spread": args.get("spread", 9.0),
            "fiat_minutes": args.get("fiat_minutes", 20),
            "active_hours": args.get("active_hours", 10),
            "days": args.get("days", 30),
            "runs": args.get("runs", 100),
        }

    try:
        result = await _http_post("/api/simulation/run", params)
        # Summarize for readability
        stats = result.get("stats", {})
        return {
            "params": params,
            "final_capital_median": stats.get("final_capital_median"),
            "final_capital_p10": stats.get("final_capital_p10"),
            "final_capital_p90": stats.get("final_capital_p90"),
            "total_profit_median": stats.get("total_profit_median"),
            "roi_pct": stats.get("roi_pct"),
            "cycles_completed": stats.get("cycles_completed"),
            "milestones": result.get("milestones", []),
            "days_simulated": params["days"],
            "full_result_available_at": f"{_api_base()}/api/simulation/run",
        }
    except Exception as e:
        # Run simulation locally if API is unreachable
        try:
            from backend.simulation.runner import run_simulation_full
            result = run_simulation_full(**params)
            return {
                "params": params,
                "final_capital_median": result.stats.final_capital_median,
                "final_capital_p10": result.stats.final_capital_p10,
                "final_capital_p90": result.stats.final_capital_p90,
                "total_profit_median": result.stats.total_profit_median,
                "roi_pct": result.stats.roi_pct,
                "cycles_completed": result.stats.cycles_completed,
                "milestones": [m.model_dump() for m in result.milestones],
                "note": "Ran locally (API unreachable)",
            }
        except Exception as e2:
            return {"error": str(e2)}


async def _tool_get_market_data(args: dict) -> dict:
    currency = args.get("currency", "").upper()
    try:
        if currency:
            return await _http_get(f"/api/markets/{currency}")
        else:
            markets = await _http_get("/api/markets")
            return {"markets": markets, "count": len(markets)}
    except Exception as e:
        return {"error": str(e), "hint": f"API may be offline. Try {_api_base()}/api/markets"}


async def _tool_refill_scan(args: dict) -> dict:
    method = args.get("method", "all")
    try:
        result = await _http_post("/api/refill/scan", {"method": method})
        return result
    except Exception as e:
        # Fallback: return from hardcoded pipeline data
        try:
            from backend.services.refill_parser import parse_pipeline
            pipeline = parse_pipeline()
            if method.lower() == "all":
                return {
                    "markets": [m.model_dump() for m in pipeline.markets],
                    "source": "local_cache",
                }
            # Find specific method
            for market in pipeline.markets:
                for m in market.methods:
                    if method.lower() in m.name.lower():
                        return {"method": m.model_dump(), "source": "local_cache"}
            return {"error": f"Method '{method}' not found in pipeline data"}
        except Exception as e2:
            return {"error": str(e2)}


async def _tool_trade_history(args: dict) -> dict:
    limit = min(int(args.get("limit", 20)), 100)
    days = int(args.get("days", 30))
    try:
        trades = await _http_get(f"/api/trades?limit={limit}")
        pnl = await _http_get(f"/api/trades/pnl?days={days}")
        return {"recent_trades": trades, "pnl_summary": pnl}
    except Exception as e:
        # Read directly from DB
        try:
            db_path = _get_db_path()
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cutoff = time.time() - (days * 86400)
            rows = conn.execute(
                "SELECT * FROM trades ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            conn.close()
            return {
                "recent_trades": [dict(r) for r in rows],
                "note": "Read from DB directly (API unreachable)",
                "error_reaching_api": str(e),
            }
        except Exception as e2:
            return {"error": str(e2)}


# ── Entry point ──────────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
