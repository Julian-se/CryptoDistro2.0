"""
Balance manager — cross-platform balance tracking and rebalancing alerts.

Tracks capital across Noones, Binance, and (future) LND.
Alerts when one platform runs low and rebalancing is needed.
"""

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal

from src.connectors.binance import BinanceConnector
from src.connectors.noones import NoonesConnector
from src.core.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class PlatformBalance:
    platform: str
    btc: Decimal = Decimal("0")
    usdt: Decimal = Decimal("0")
    total_usd: Decimal = Decimal("0")  # Estimated total in USD
    updated_at: float = 0.0


@dataclass
class CapitalSnapshot:
    """Complete view of capital across all platforms."""
    balances: dict[str, PlatformBalance] = field(default_factory=dict)
    total_usd: Decimal = Decimal("0")
    btc_price_usd: Decimal = Decimal("0")
    timestamp: float = 0.0

    def summary(self) -> str:
        lines = [f"Total capital: ${self.total_usd:.2f} (BTC @ ${self.btc_price_usd:.2f})"]
        for name, bal in self.balances.items():
            pct = (bal.total_usd / self.total_usd * 100) if self.total_usd > 0 else Decimal("0")
            lines.append(
                f"  {name}: {bal.btc:.6f} BTC + {bal.usdt:.2f} USDT = ${bal.total_usd:.2f} ({pct:.0f}%)"
            )
        return "\n".join(lines)


class BalanceManager:
    """Tracks and reports balances across all platforms."""

    def __init__(self, binance: BinanceConnector, noones: NoonesConnector):
        self.binance = binance
        self.noones = noones
        cfg = get_config()
        self.low_balance_pct = cfg["balance"]["low_balance_pct"]
        self.target_split = cfg["balance"]["target_split"]
        self._last_snapshot: CapitalSnapshot | None = None

    def get_snapshot(self) -> CapitalSnapshot:
        """Fetch current balances from all platforms and build a snapshot."""
        snapshot = CapitalSnapshot(timestamp=time.time())

        # Get BTC price for USD conversion
        try:
            snapshot.btc_price_usd = self.binance.get_spot_price("BTCUSDT")
        except Exception as e:
            logger.error(f"Failed to get BTC price: {e}")
            if self._last_snapshot:
                snapshot.btc_price_usd = self._last_snapshot.btc_price_usd

        # Binance balances
        try:
            btc_bal = self.binance.get_balance("BTC")
            usdt_bal = self.binance.get_balance("USDT")
            binance_btc = btc_bal["free"]
            binance_usdt = usdt_bal["free"]
            binance_usd = binance_btc * snapshot.btc_price_usd + binance_usdt
            snapshot.balances["binance"] = PlatformBalance(
                platform="binance",
                btc=binance_btc,
                usdt=binance_usdt,
                total_usd=binance_usd,
                updated_at=time.time(),
            )
        except Exception as e:
            logger.error(f"Failed to get Binance balances: {e}")
            snapshot.balances["binance"] = PlatformBalance(platform="binance")

        # Noones balances
        try:
            noones_bal = self.noones.get_balance()
            noones_btc = noones_bal["btc"]
            noones_usdt = noones_bal["usdt"]
            noones_usd = noones_btc * snapshot.btc_price_usd + noones_usdt
            snapshot.balances["noones"] = PlatformBalance(
                platform="noones",
                btc=noones_btc,
                usdt=noones_usdt,
                total_usd=noones_usd,
                updated_at=time.time(),
            )
        except Exception as e:
            logger.error(f"Failed to get Noones balances: {e}")
            snapshot.balances["noones"] = PlatformBalance(platform="noones")

        snapshot.total_usd = sum(b.total_usd for b in snapshot.balances.values())
        self._last_snapshot = snapshot
        return snapshot

    def check_rebalance_needed(self, snapshot: CapitalSnapshot | None = None) -> list[str]:
        """
        Check if capital distribution is off-target and return alert messages.
        """
        if snapshot is None:
            snapshot = self.get_snapshot()

        if snapshot.total_usd <= 0:
            return ["WARNING: Total capital is $0 across all platforms"]

        alerts = []
        for platform, target_frac in self.target_split.items():
            bal = snapshot.balances.get(platform)
            if not bal:
                continue

            actual_pct = float(bal.total_usd / snapshot.total_usd * 100)
            target_pct = target_frac * 100

            if actual_pct < self.low_balance_pct:
                alerts.append(
                    f"LOW BALANCE: {platform} has ${bal.total_usd:.2f} "
                    f"({actual_pct:.0f}% — target {target_pct:.0f}%). "
                    f"Consider rebalancing."
                )

        return alerts

    def get_capital_utilization(self) -> dict:
        """How much capital is actively available vs locked."""
        snapshot = self.get_snapshot()
        free_binance = snapshot.balances.get("binance", PlatformBalance(platform="binance"))
        free_noones = snapshot.balances.get("noones", PlatformBalance(platform="noones"))

        return {
            "total_usd": snapshot.total_usd,
            "binance_free_usd": free_binance.total_usd,
            "noones_free_usd": free_noones.total_usd,
            "btc_price": snapshot.btc_price_usd,
        }
