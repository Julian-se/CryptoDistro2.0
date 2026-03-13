"""
Spread scanner — Lager 1 automation (automatisera allt).

Continuously polls Noones P2P offers and Binance spot price,
calculates the spread, and flags opportunities above threshold.

"var femte minut hämtar alla aktiva säljares priser, jämför mot aktuellt
Binance-spotpris, och räknar ut den faktiska spreaden i procent."
"""

import logging
import time
from dataclasses import dataclass
from decimal import Decimal

from src.connectors.binance import BinanceConnector
from src.connectors.noones import NoonesConnector
from src.core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ArbOpportunity:
    """A detected arbitrage opportunity."""
    direction: str          # "noones_to_binance" or "binance_to_noones"
    buy_platform: str
    sell_platform: str
    buy_price: Decimal
    sell_price: Decimal
    spread_pct: Decimal
    net_spread_pct: Decimal  # After fees
    potential_profit_usd: Decimal
    offer_id: str           # Noones offer_hash (if applicable)
    seller: str             # Noones seller username
    seller_score: int
    seller_trades: int
    currency: str
    min_amount: Decimal
    max_amount: Decimal
    timestamp: float

    def __str__(self) -> str:
        return (
            f"ARB {self.direction}: buy@{self.buy_platform} ${self.buy_price:.2f} → "
            f"sell@{self.sell_platform} ${self.sell_price:.2f} | "
            f"spread {self.spread_pct:.2f}% (net {self.net_spread_pct:.2f}%) | "
            f"profit ~${self.potential_profit_usd:.2f} on ${self.max_amount}"
        )


class SpreadScanner:
    """
    Scans for arbitrage opportunities between Noones and Binance.

    Two directions:
    1. Buy on Noones (P2P discount) → Sell on Binance (spot price)
    2. Buy on Binance (spot) → Sell on Noones (P2P premium) [reverse arb]
    """

    def __init__(self, binance: BinanceConnector, noones: NoonesConnector):
        self.binance = binance
        self.noones = noones
        cfg = get_config()
        trading = cfg["trading"]
        self.min_spread_pct = Decimal(str(trading["min_spread_pct"]))
        self.max_trade_usd = Decimal(str(trading["max_trade_usd"]))
        self.currencies = cfg["scanner"]["noones_currencies"]
        self.offers_limit = cfg["scanner"]["noones_offers_limit"]

        fees = cfg["fees"]
        # Total round-trip fee estimate as percentage
        self.total_fee_pct = Decimal(str(
            fees["binance_trading_pct"] + fees["noones_fee_pct"]
        ))

    def scan(self) -> list[ArbOpportunity]:
        """
        Run a full scan: fetch Binance spot + Noones offers, find opportunities.
        Returns list of opportunities sorted by net spread (best first).
        """
        opportunities = []

        # Get Binance spot price
        try:
            binance_price = self.binance.get_spot_price("BTCUSDT")
        except Exception as e:
            logger.error(f"Failed to get Binance price: {e}")
            return []

        logger.info(f"Binance BTC/USDT spot: ${binance_price:.2f}")

        # Scan each currency on Noones
        for currency in self.currencies:
            noones_offers = self.noones.get_offers(
                offer_type="sell",  # We buy from sellers
                currency_code=currency,
                crypto_currency_code="BTC",
                limit=self.offers_limit,
            )

            for offer in noones_offers:
                opp = self._evaluate_offer(offer, binance_price, currency)
                if opp:
                    opportunities.append(opp)

        # Sort by net spread, best first
        opportunities.sort(key=lambda o: o.net_spread_pct, reverse=True)

        if opportunities:
            logger.info(f"Found {len(opportunities)} opportunities above {self.min_spread_pct}% threshold")
        else:
            logger.debug("No opportunities above threshold")

        return opportunities

    def _evaluate_offer(
        self, offer: dict, binance_price: Decimal, currency: str
    ) -> ArbOpportunity | None:
        """
        Evaluate a single Noones offer against Binance spot.
        Returns an ArbOpportunity if the spread exceeds threshold.
        """
        noones_price = offer["price"]
        if noones_price <= 0:
            return None

        # For non-USD currencies, we'd need FX conversion.
        # For now, focus on USD-denominated offers (simplest path).
        # TODO: Add FX rate conversion for EUR/SEK offers
        if currency != "USD":
            return None

        # Direction 1: Noones price < Binance spot → buy Noones, sell Binance
        if noones_price < binance_price:
            spread_pct = ((binance_price - noones_price) / noones_price) * 100
            net_spread_pct = spread_pct - self.total_fee_pct

            if net_spread_pct < self.min_spread_pct:
                return None

            trade_amount = min(offer["max_amount"], self.max_trade_usd)
            potential_profit = trade_amount * (net_spread_pct / 100)

            return ArbOpportunity(
                direction="noones_to_binance",
                buy_platform="noones",
                sell_platform="binance",
                buy_price=noones_price,
                sell_price=binance_price,
                spread_pct=spread_pct,
                net_spread_pct=net_spread_pct,
                potential_profit_usd=potential_profit,
                offer_id=offer["offer_id"],
                seller=offer["seller"],
                seller_score=offer["seller_score"],
                seller_trades=offer["seller_trades"],
                currency=currency,
                min_amount=offer["min_amount"],
                max_amount=offer["max_amount"],
                timestamp=time.time(),
            )

        return None

    def scan_loop(self, callback=None):
        """
        Continuous scanning loop. Calls callback with opportunities.
        This is the main monitoring process.
        """
        cfg = get_config()
        interval = cfg["scanner"]["poll_interval_sec"]
        logger.info(f"Starting scan loop (interval: {interval}s, min spread: {self.min_spread_pct}%)")

        while True:
            try:
                opportunities = self.scan()
                if callback and opportunities:
                    callback(opportunities)
            except Exception as e:
                logger.error(f"Scan error: {e}")

            time.sleep(interval)
