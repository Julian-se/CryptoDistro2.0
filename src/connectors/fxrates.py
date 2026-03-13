"""
FX rates connector — free, no API key required.
Uses open.er-api.com to convert local currencies to USD.

Used by the premium monitor to compare Noones local prices
against Binance USD spot price.
"""

import logging
import time

import httpx

from src.core.config import get_config

logger = logging.getLogger(__name__)

_CACHE: dict = {}
_CACHE_TTL = 300  # refresh FX every 5 minutes


class FxRatesConnector:
    """Fetches USD-based FX rates for local currency conversion."""

    def __init__(self):
        cfg = get_config()
        self.api_url = cfg.get("premium_monitor", {}).get(
            "fx_api_url", "https://open.er-api.com/v6/latest/USD"
        )
        self._client = httpx.Client(timeout=10)
        self._rates: dict[str, float] = {}
        self._fetched_at: float = 0

    def get_rates(self) -> dict[str, float]:
        """Return USD-based rates, refreshing cache if stale."""
        if time.time() - self._fetched_at < _CACHE_TTL and self._rates:
            return self._rates

        try:
            resp = self._client.get(self.api_url)
            resp.raise_for_status()
            data = resp.json()
            self._rates = data.get("rates", {})
            self._fetched_at = time.time()
            logger.debug(f"FX rates refreshed ({len(self._rates)} currencies)")
        except Exception as e:
            logger.error(f"Failed to fetch FX rates: {e}")
            # Return stale cache if available
            if not self._rates:
                raise

        return self._rates

    def usd_to(self, currency: str) -> float:
        """How many units of currency per 1 USD."""
        rates = self.get_rates()
        rate = rates.get(currency.upper())
        if rate is None:
            raise ValueError(f"Currency {currency} not found in FX rates")
        return float(rate)

    def local_to_usd(self, amount: float, currency: str) -> float:
        """Convert local currency amount to USD."""
        return amount / self.usd_to(currency)

    def close(self):
        self._client.close()
