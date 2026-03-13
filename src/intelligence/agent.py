"""
Intelligence agent — LLM with clean read-only boundaries.

Uses Cerebras inference (OpenAI-compatible API).
Model: gpt-oss-120b (fast, large context, free tier available)

The agent can READ anything: prices, offers, balances, trade history.
The agent cannot WRITE anything: no orders, no offers, no transfers.

Tools (read-only):
  get_market_intel   — live premiums across configured markets
  get_sellers        — competitor offer data for a currency (Noones + Binance P2P)
  get_balance        — capital snapshot across platforms
  get_recent_trades  — last N logged trades
  get_pnl            — profit & loss summary
  get_spot_price     — current BTC spot price
"""

import json
import logging

from openai import OpenAI

from src.core.config import get_config

logger = logging.getLogger(__name__)

CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"

# Tools in OpenAI function-calling format
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_market_intel",
            "description": (
                "Scan all configured emerging markets and return live BTC premium data. "
                "Shows which markets are in range to post a sell offer (ACT_NOW), "
                "which are building up (WATCH), and which to skip (AVOID). "
                "Also flags markets where the official FX rate is unreliable (parallel rate markets)."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_sellers",
            "description": (
                "Fetch active sell offers from both Noones and Binance P2P for a specific currency. "
                "Returns competitor data: usernames, trade counts, scores, margins, payment methods. "
                "Use this to understand who the dominant players are and at what price they operate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "currency": {
                        "type": "string",
                        "description": "3-letter fiat currency code, e.g. NGN, KES, SEK, ARS",
                    }
                },
                "required": ["currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": (
                "Get current capital snapshot: BTC and USDT balances on Binance and Noones, "
                "total capital in USD, and any rebalancing alerts."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_trades",
            "description": "Retrieve the most recently logged trades.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of trades to return (default 10, max 50)",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pnl",
            "description": "Get profit & loss summary for the last N days.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back (default 30)",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_spot_price",
            "description": "Get the current BTC/USDT spot price from Binance.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

SYSTEM_PROMPT = """You are a market intelligence assistant for a Bitcoin P2P on/off-ramp operation in emerging markets.

The business: buy BTC at spot on Binance, sell to customers on P2P platforms (Noones, Binance P2P) at a premium. Markets in Africa, Latin America, Southeast Asia pay 5–12% above spot due to currency controls and limited USD access. That spread is the profit.

Your role: analyze market data and give actionable, concise advice. Use the tools to fetch live data before answering.

You have read-only access. You cannot execute trades, move funds, or post offers.

Keep answers short and concrete. Lead with the action or insight, not the explanation. Use numbers when you have them."""


class IntelligenceAgent:
    """
    LLM agent with read-only tool access via Cerebras.

    Inject the same component instances used by the rest of the system.
    The agent reads from them but never calls any method that modifies state.
    """

    def __init__(
        self,
        premium_monitor=None,
        balance_manager=None,
        trade_tracker=None,
        binance=None,
    ):
        self.premium_monitor = premium_monitor
        self.balance_manager = balance_manager
        self.trade_tracker = trade_tracker
        self.binance = binance

        cfg = get_config()
        api_key = cfg.get("intelligence", {}).get("api_key", "")
        if not api_key:
            raise ValueError(
                "CEREBRAS_API_KEY not set. Add it to .env: CEREBRAS_API_KEY=..."
            )

        self.model = cfg.get("intelligence", {}).get("model", "qwen-3-235b-a22b-instruct-2507")
        self.client = OpenAI(api_key=api_key, base_url=CEREBRAS_BASE_URL)

        # Conversation history — persists within a process lifetime
        # Each entry: {"role": "user"|"assistant"|"tool", "content": ...}
        self._history: list[dict] = []

    def chat(self, message: str) -> str:
        """
        Send a message in ongoing conversation. History is preserved
        across calls so the agent remembers context from earlier messages.
        """
        self._history.append({"role": "user", "content": message})
        answer = self._run(self._history)
        self._history.append({"role": "assistant", "content": answer})
        # Cap history at 40 messages to avoid token bloat
        if len(self._history) > 40:
            self._history = self._history[-40:]
        return answer

    def ask(self, question: str) -> str:
        """One-shot question with no history (used by /ask command)."""
        return self._run([
            {"role": "user", "content": question},
        ])

    def _run(self, messages: list[dict]) -> str:
        """
        Agentic loop: send messages, handle tool calls, return final answer.
        """
        working = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        for _ in range(6):  # max 6 tool-call rounds
            response = self.client.chat.completions.create(
                model=self.model,
                messages=working,
                tools=TOOLS,
                tool_choice="auto",
                max_tokens=1024,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or "No response generated."

            # Append assistant message and resolve tool calls
            working.append(msg)
            for tc in msg.tool_calls:
                try:
                    inputs = json.loads(tc.function.arguments) if tc.function.arguments else {}
                except json.JSONDecodeError:
                    inputs = {}
                result = self._call_tool(tc.function.name, inputs)
                working.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        return "Agent loop ended without a final answer."

    # ── Tool dispatcher ───────────────────────────────────────────────────

    def _call_tool(self, name: str, inputs: dict) -> str:
        try:
            if name == "get_market_intel":
                return self._tool_market_intel()
            if name == "get_sellers":
                return self._tool_sellers(inputs.get("currency", "NGN"))
            if name == "get_balance":
                return self._tool_balance()
            if name == "get_recent_trades":
                return self._tool_recent_trades(inputs.get("limit", 10))
            if name == "get_pnl":
                return self._tool_pnl(inputs.get("days", 30))
            if name == "get_spot_price":
                return self._tool_spot_price()
            return f"Unknown tool: {name}"
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return f"Tool error: {e}"

    def _tool_market_intel(self) -> str:
        if not self.premium_monitor:
            return "Premium monitor not available."
        snapshot = self.premium_monitor.scan_all()
        lines = [f"BTC spot: ${snapshot.btc_spot_usd:,.0f}"]
        for m in snapshot.markets:
            lines.append(
                f"{m.name} ({m.currency}): premium {float(m.premium_pct):+.1f}% "
                f"(expected {m.expected_low:.0f}–{m.expected_high:.0f}%), "
                f"action={m.action.value}, offers={m.offer_count}"
            )
        return "\n".join(lines)

    def _tool_sellers(self, currency: str) -> str:
        if not self.premium_monitor:
            return "Premium monitor not available."
        noones_offers = self.premium_monitor.noones.get_offers(
            offer_type="sell",
            currency_code=currency.upper(),
            crypto_currency_code="BTC",
            limit=20,
        )
        binance_offers = self.premium_monitor.binance.get_p2p_offers(
            fiat=currency.upper(),
            asset="BTC",
            trade_type="SELL",
            rows=20,
        )
        data = {
            "currency": currency.upper(),
            "noones": [
                {
                    "seller": o["seller"],
                    "price": float(o["price"]),
                    "margin": float(o["margin"]) if o.get("margin") is not None else None,
                    "trades": o["seller_trades"],
                    "score": o["seller_score"],
                    "method": o["payment_method"],
                    "min": float(o["min_amount"]),
                    "max": float(o["max_amount"]),
                }
                for o in noones_offers[:10]
            ],
            "binance_p2p": [
                {
                    "seller": o["seller"],
                    "price": float(o["price"]),
                    "trades": o["seller_trades"],
                    "month_trades": o["month_trades"],
                    "score_pct": o["seller_score"],
                    "finish_rate": o["finish_rate"],
                    "method": o["payment_method"],
                    "merchant": o["is_merchant"],
                    "online": o["is_online"],
                    "min": float(o["min_amount"]),
                    "max": float(o["max_amount"]),
                }
                for o in binance_offers[:10]
            ],
        }
        return json.dumps(data)

    def _tool_balance(self) -> str:
        if not self.balance_manager:
            return "Balance manager not available."
        snapshot = self.balance_manager.get_snapshot()
        lines = [
            f"Total capital: ${snapshot.total_usd:.2f}",
            f"BTC price: ${snapshot.btc_price_usd:.2f}",
        ]
        for p in snapshot.platforms:
            lines.append(
                f"{p.name}: {p.btc_balance} BTC + {p.usdt_balance} USDT = ${p.total_usd:.2f}"
            )
        alerts = self.balance_manager.check_rebalance_needed(snapshot)
        if alerts:
            lines.append("Rebalance alerts: " + "; ".join(alerts))
        return "\n".join(lines)

    def _tool_recent_trades(self, limit: int) -> str:
        if not self.trade_tracker:
            return "Trade tracker not available."
        trades = self.trade_tracker.get_recent_trades(limit=min(limit, 50))
        if not trades:
            return "No trades recorded."
        return json.dumps(trades, default=str)

    def _tool_pnl(self, days: int) -> str:
        if not self.trade_tracker:
            return "Trade tracker not available."
        pnl = self.trade_tracker.get_pnl_summary(days=days)
        return json.dumps(pnl, default=str)

    def _tool_spot_price(self) -> str:
        if not self.binance:
            return "Binance connector not available."
        price = self.binance.get_spot_price("BTCUSDT")
        return f"BTC/USDT: ${float(price):,.2f}"
