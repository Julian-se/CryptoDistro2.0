"""
CryptoDistro 2.0 — Main entry point.

On/Off-Ramp Operator: buy/sell BTC at local premiums in emerging markets.

Components:
- Premium Monitor: live spread per market (Nigeria, Argentina, Venezuela, Kenya, Sweden)
- Trade Tracker: log every trade, track P&L
- Balance Manager: monitor capital across platforms
- Telegram Bot: commands + push alerts
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

from src.core.config import load_config
from src.core.premium_monitor import PremiumMonitor
from src.core.market_discovery import MarketDiscoveryEngine
from src.core.trade_tracker import TradeTracker
from src.core.balance_manager import BalanceManager
from src.connectors.binance import BinanceConnector
from src.connectors.noones import NoonesConnector
from src.connectors.fxrates import FxRatesConnector
from src.alerts.telegram_bot import TelegramBot
from src.intelligence.agent import IntelligenceAgent


def setup_logging(cfg: dict):
    log_file = cfg["logging"]["file"]
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, cfg["logging"]["level"]),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


logger = logging.getLogger("cryptodistro")


class CryptoDistroEngine:

    def __init__(self):
        self.cfg = load_config()
        setup_logging(self.cfg)
        logger.info("=" * 60)
        logger.info("CryptoDistro 2.0 — On/Off-Ramp Operator starting")
        logger.info("=" * 60)

        # Connectors
        self.binance = BinanceConnector()
        self.noones = NoonesConnector()
        self.fx = FxRatesConnector()

        # Core components
        self.trade_tracker = TradeTracker()
        self.balance_manager = BalanceManager(self.binance, self.noones)
        self.premium_monitor = PremiumMonitor(
            binance=self.binance,
            noones=self.noones,
            fx=self.fx,
        )
        self.discovery_engine = MarketDiscoveryEngine(
            binance=self.binance,
            noones=self.noones,
            fx=self.fx,
        )

        # Intelligence agent (read-only LLM — no write access)
        try:
            self.intelligence = IntelligenceAgent(
                premium_monitor=self.premium_monitor,
                balance_manager=self.balance_manager,
                trade_tracker=self.trade_tracker,
                binance=self.binance,
            )
            logger.info("Intelligence agent initialized")
        except ValueError as e:
            logger.warning(f"Intelligence agent disabled: {e}")
            self.intelligence = None

        # Telegram bot (inject all components)
        self.telegram = TelegramBot(
            balance_manager=self.balance_manager,
            trade_tracker=self.trade_tracker,
            premium_monitor=self.premium_monitor,
            discovery_engine=self.discovery_engine,
            intelligence=self.intelligence,
        )

        # Give premium monitor a reference to telegram for push alerts
        self.premium_monitor.telegram = self.telegram

        self._running = False

    async def run(self):
        self._running = True

        # Start Telegram bot
        app = self.telegram.build()
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        logger.info("Telegram bot online")

        await self.telegram.send_alert(
            "CryptoDistro 2.0 started.\n"
            "Use /premium for live market spreads.\n"
            "Use /help for all commands."
        )

        refresh = self.cfg.get("premium_monitor", {}).get("refresh_interval_sec", 60)
        logger.info(f"Premium monitor loop starting (every {refresh}s)")

        try:
            while self._running:
                try:
                    snapshot = self.premium_monitor.scan_all()
                    if snapshot.act_now:
                        logger.info(
                            f"ACT NOW markets: "
                            f"{[m.name for m in snapshot.act_now]}"
                        )
                except Exception as e:
                    logger.error(f"Premium scan error: {e}")
                await asyncio.sleep(refresh)
        finally:
            logger.info("Shutting down...")
            await app.updater.stop()
            await app.stop()
            await app.shutdown()
            self.noones.close()
            self.binance.close()
            self.fx.close()
            self.trade_tracker.close()
            self.discovery_engine.close()

    def stop(self):
        self._running = False


def main():
    engine = CryptoDistroEngine()

    def signal_handler(sig, frame):
        logger.info(f"Signal {sig} received, shutting down...")
        engine.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    asyncio.run(engine.run())


if __name__ == "__main__":
    main()
