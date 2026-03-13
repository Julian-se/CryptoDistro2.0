"""
Telegram bot — alerts and commands for monitoring the arbitrage system.

Push alerts for opportunities. Commands for checking status.
This is how you stay in the loop without staring at screens.

"Ett monitoring-lager körs kontinuerligt, scannar P2P-plattformar och
pushar notiser till din telefon när ett bra deal dyker upp."
"""

import logging
from decimal import Decimal

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.core.config import get_config

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for alerts and commands."""

    def __init__(
        self,
        balance_manager=None,
        trade_tracker=None,
        spread_scanner=None,
        premium_monitor=None,
        discovery_engine=None,
        intelligence=None,
    ):
        cfg = get_config()["telegram"]
        self.token = cfg["bot_token"]
        self.chat_id = cfg["chat_id"]
        self.balance_manager = balance_manager
        self.trade_tracker = trade_tracker
        self.spread_scanner = spread_scanner
        self.premium_monitor = premium_monitor
        self.discovery_engine = discovery_engine
        self.intelligence = intelligence
        self._app: Application | None = None

    def build(self) -> Application:
        """Build the Telegram application with command handlers."""
        self._app = Application.builder().token(self.token).build()

        self._app.add_handler(CommandHandler("start",    self._cmd_start))
        self._app.add_handler(CommandHandler("status",   self._cmd_status))
        self._app.add_handler(CommandHandler("balance",  self._cmd_balance))
        self._app.add_handler(CommandHandler("scan",     self._cmd_scan))
        self._app.add_handler(CommandHandler("premium",  self._cmd_premium))
        self._app.add_handler(CommandHandler("markets",  self._cmd_markets))
        self._app.add_handler(CommandHandler("discover", self._cmd_discover))
        self._app.add_handler(CommandHandler("sellers",  self._cmd_sellers))
        self._app.add_handler(CommandHandler("ask",      self._cmd_ask))
        self._app.add_handler(CommandHandler("pnl",      self._cmd_pnl))
        self._app.add_handler(CommandHandler("trades",   self._cmd_trades))
        self._app.add_handler(CommandHandler("help",     self._cmd_help))

        # Free-form chat — any non-command text goes to the intelligence agent
        self._app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._chat)
        )

        return self._app

    # --- Push Alerts (called by other components) ---

    async def send_alert(self, message: str):
        """Send a push notification to the configured chat."""
        if not self._app:
            logger.warning("Telegram app not built, cannot send alert")
            return
        try:
            await self._app.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def send_alert_sync(self, message: str):
        """Synchronous wrapper for sending alerts (used from non-async code)."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.send_alert(message))
        except RuntimeError:
            asyncio.run(self.send_alert(message))

    def format_opportunity_alert(self, opp) -> str:
        """Format an arbitrage opportunity as a Telegram message."""
        return (
            f"*ARB OPPORTUNITY*\n"
            f"Direction: `{opp.direction}`\n"
            f"Buy: {opp.buy_platform} @ ${opp.buy_price:.2f}\n"
            f"Sell: {opp.sell_platform} @ ${opp.sell_price:.2f}\n"
            f"Spread: {opp.spread_pct:.2f}% (net {opp.net_spread_pct:.2f}%)\n"
            f"Potential profit: *${opp.potential_profit_usd:.2f}*\n"
            f"Seller: {opp.seller} (score: {opp.seller_score}, trades: {opp.seller_trades})\n"
            f"Range: ${opp.min_amount} - ${opp.max_amount}"
        )

    # --- Command Handlers ---

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "CryptoDistro 2.0 — Arbitrage Bot\n\n"
            "Use /help to see available commands."
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "*Commands:*\n\n"
            "*Intel*\n"
            "/markets — Ranked market opportunities (quick)\n"
            "/discover — Full scan of all ~80 EM currencies (slow)\n"
            "/premium — Live premiums for configured markets\n"
            "/sellers — Competitor intel: who's selling, at what margin\n"
            "/sellers NGN — Sellers in a specific market (e.g. NGN, KES)\n"
            "/ask <question> — Ask the AI agent anything about the markets\n\n"
            "*Operations*\n"
            "/status — System status\n"
            "/balance — Balances across all platforms\n"
            "/pnl — Profit & loss summary\n"
            "/trades — Recent trades\n"
            "/help — This message",
            parse_mode="Markdown",
        )

    async def _cmd_markets(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick scan of top markets — runs in thread so it doesn't block."""
        if not self.discovery_engine:
            await update.message.reply_text("Discovery engine not available.")
            return

        await update.message.reply_text("Scanning top markets...")
        try:
            import asyncio
            markets = await asyncio.to_thread(self.discovery_engine.quick_scan)
            msg = _format_discovery(markets)
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def _cmd_discover(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Full deep scan — runs as background task.
        Telegram gets an immediate ACK, result arrives when done.
        """
        if not self.discovery_engine:
            await update.message.reply_text("Discovery engine not available.")
            return

        await update.message.reply_text(
            "🔍 Full scan started — scanning ~54 currencies.\n"
            "_You'll get the results here when done (2-5 min)._",
            parse_mode="Markdown",
        )

        import asyncio

        async def _run():
            try:
                markets = await asyncio.to_thread(self.discovery_engine.deep_scan)
                msg = _format_discovery(markets)
                await self._app.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=msg,
                    parse_mode="Markdown",
                )
            except Exception as e:
                await self._app.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Scan error: {e}",
                )

        asyncio.create_task(_run())

    async def _cmd_sellers(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Show competitor intel for a market.
        Usage: /sellers NGN  or  /sellers KES
        Without argument: shows all configured markets one by one.
        """
        if not self.premium_monitor:
            await update.message.reply_text("Premium monitor not available.")
            return

        args = context.args
        if args:
            currencies = [args[0].upper()]
        else:
            # Default: all configured markets
            cfg = self.premium_monitor.markets_cfg
            currencies = [m["currency"] for m in cfg]

        await update.message.reply_text(
            f"Fetching seller intel for: {', '.join(currencies)}..."
        )

        import asyncio
        for currency in currencies:
            try:
                msg = await asyncio.to_thread(
                    self.premium_monitor.scan_players, currency
                )
                await update.message.reply_text(msg, parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"{currency} error: {e}")

    async def _chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route free-form messages to the intelligence agent."""
        if not self.intelligence:
            return  # Silently ignore if agent not configured

        text = update.message.text
        import asyncio
        await update.message.chat.send_action("typing")
        try:
            answer = await asyncio.to_thread(self.intelligence.chat, text)
            if len(answer) <= 4096:
                await update.message.reply_text(answer)
            else:
                for chunk in [answer[i:i+4000] for i in range(0, len(answer), 4000)]:
                    await update.message.reply_text(chunk)
        except Exception as e:
            await update.message.reply_text(f"Agent error: {e}")

    async def _cmd_ask(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Ask the intelligence agent a question in plain language.
        Usage: /ask which market should I post in right now?
               /ask who are the top sellers in Nigeria?
               /ask how has my P&L looked this week?
        """
        if not self.intelligence:
            await update.message.reply_text(
                "Intelligence agent not available. Add ANTHROPIC_API_KEY to .env"
            )
            return

        question = " ".join(context.args) if context.args else ""
        if not question:
            await update.message.reply_text(
                "Ask me anything about the markets.\n"
                "Example: `/ask which market should I post in right now?`",
                parse_mode="Markdown",
            )
            return

        await update.message.reply_text("_Thinking..._", parse_mode="Markdown")

        import asyncio
        try:
            answer = await asyncio.to_thread(self.intelligence.ask, question)
            # Telegram messages max 4096 chars — split if needed
            if len(answer) <= 4096:
                await update.message.reply_text(answer)
            else:
                for chunk in [answer[i:i+4000] for i in range(0, len(answer), 4000)]:
                    await update.message.reply_text(chunk)
        except Exception as e:
            await update.message.reply_text(f"Agent error: {e}")

    async def _cmd_premium(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show live actionable market intelligence."""
        if not self.premium_monitor:
            await update.message.reply_text("Premium monitor not available.")
            return

        await update.message.reply_text("Scanning markets...")
        try:
            import asyncio
            snapshot = await asyncio.to_thread(self.premium_monitor.scan_all)
            msg = self.premium_monitor.format_actionable(snapshot)
            await update.message.reply_text(msg, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        import asyncio
        lines = ["*System Status*\n"]

        if self.trade_tracker:
            open_cycles = await asyncio.to_thread(self.trade_tracker.get_open_cycles)
            lines.append(f"Open cycles: {len(open_cycles)}")

        if self.balance_manager:
            try:
                snapshot = await asyncio.to_thread(self.balance_manager.get_snapshot)
                lines.append(f"Total capital: ${snapshot.total_usd:.2f}")
                lines.append(f"BTC price: ${snapshot.btc_price_usd:.2f}")
                alerts = self.balance_manager.check_rebalance_needed(snapshot)
                if alerts:
                    lines.append("\n*Alerts:*")
                    lines.extend(alerts)
            except Exception as e:
                lines.append(f"Balance check failed: {e}")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def _cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        import asyncio
        if not self.balance_manager:
            await update.message.reply_text("Balance manager not available")
            return

        try:
            snapshot = await asyncio.to_thread(self.balance_manager.get_snapshot)
            await update.message.reply_text(
                f"*Balances*\n```\n{snapshot.summary()}\n```",
                parse_mode="Markdown",
            )
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def _cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.spread_scanner:
            await update.message.reply_text("Spread scanner not available")
            return

        await update.message.reply_text("Scanning...")
        try:
            opps = self.spread_scanner.scan()
            if not opps:
                await update.message.reply_text("No opportunities above threshold right now.")
                return

            for opp in opps[:5]:  # Top 5
                await update.message.reply_text(
                    self.format_opportunity_alert(opp),
                    parse_mode="Markdown",
                )
        except Exception as e:
            await update.message.reply_text(f"Scan error: {e}")

    async def _cmd_pnl(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.trade_tracker:
            await update.message.reply_text("Trade tracker not available")
            return

        try:
            pnl = self.trade_tracker.get_pnl_summary(days=30)
            text = (
                f"*P&L (last 30 days)*\n"
                f"Cycles: {pnl['total_cycles']}\n"
                f"Gross profit: ${pnl['total_gross_profit']:.2f}\n"
                f"Fees: ${pnl['total_fees']:.2f}\n"
                f"Net profit: *${pnl['total_net_profit']:.2f}*\n"
                f"Avg per cycle: ${pnl['avg_profit_per_cycle']:.2f}\n"
                f"Cycles/day: {pnl['cycles_per_day']:.1f}\n"
                f"Avg duration: {pnl['avg_cycle_duration_sec']:.0f}s"
            )
            await update.message.reply_text(text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

    async def _cmd_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.trade_tracker:
            await update.message.reply_text("Trade tracker not available")
            return

        try:
            trades = self.trade_tracker.get_recent_trades(limit=10)
            if not trades:
                await update.message.reply_text("No trades recorded yet.")
                return

            lines = ["*Recent Trades*\n"]
            for t in trades:
                lines.append(
                    f"`{t['type']:>8}` {t['quantity']} {t['asset']} "
                    f"on {t['platform']} @ ${t['price_usd'] or '?'}"
                )
            await update.message.reply_text("\n".join(lines), parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")


# ── Module-level formatting helper ─────────────────────────────────────────

def _format_discovery(markets: list) -> str:
    """Format MarketDiscoveryEngine results as actionable Telegram message."""
    import datetime
    if not markets:
        return "No markets found."

    ts = datetime.datetime.now().strftime("%H:%M")
    real    = [m for m in markets if not m.parallel_rate and m.premium_pct > 0]
    parallel = [m for m in markets if m.parallel_rate]
    low     = [m for m in markets if not m.parallel_rate and m.premium_pct <= 0]

    lines = [f"🌍 *MARKET DISCOVERY* — {ts}"]

    # Top opportunities
    if real:
        lines.append(f"\n🟢 *TOP OPPORTUNITIES* ({len(real)} markets with premium)")
        lines.append("─" * 36)
        for m in real[:10]:
            pm = m.top_method
            method_str = pm.label if pm else "—"
            risk_icon = "🔒" if pm and pm.risk == "low" else "⚠️" if pm and pm.risk == "medium" else "🚫"
            lines.append(
                f"{m.flag} *{m.country}* `{m.premium_pct:+.1f}%`  "
                f"score `{m.opportunity_score:.0f}`  "
                f"{risk_icon} {method_str}"
            )
            # Show top 3 payment methods
            if m.tier1_methods:
                pm_list = " · ".join(p.label for p in m.tier1_methods[:3])
                lines.append(f"   _Low-risk methods: {pm_list}_")

    # Parallel rate markets
    if parallel:
        lines.append(f"\n⚙️ *PARALLEL RATE* (official FX unreliable)")
        lines.append("─" * 36)
        for m in parallel:
            lines.append(
                f"{m.flag} {m.country}  "
                f"_Est. {m.premium_pct:.0f}–{m.premium_pct*1.5:.0f}% real_ — manual check needed"
            )

    # Low/negative markets
    if low:
        lines.append(f"\n🔴 *LOW DEMAND* — not worth spreading today")
        for m in low[:5]:
            lines.append(f"{m.flag} {m.country}  `{m.premium_pct:+.1f}%`")
        if len(low) > 5:
            lines.append(f"  _...and {len(low)-5} more_")

    return "\n".join(lines)
