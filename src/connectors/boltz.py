"""
Boltz connector — STUB for on-chain <-> Lightning swaps.

Boltz.exchange provides trustless submarine swaps:
- On-chain BTC → Lightning BTC
- Lightning BTC → On-chain BTC

Useful for rebalancing between layers without a counterparty.
Implementation deferred to Phase 2 alongside LND integration.
"""

import logging

logger = logging.getLogger(__name__)


class BoltzConnector:
    """Placeholder for Boltz swap API integration."""

    def __init__(self):
        logger.info("Boltz connector initialized (STUB — not connected)")

    def get_pairs(self) -> dict:
        """Get available swap pairs and fees."""
        raise NotImplementedError("Boltz not connected — Phase 2")

    def create_swap(self, from_asset: str, to_asset: str, amount_sats: int) -> dict:
        """Create a submarine swap."""
        raise NotImplementedError("Boltz not connected — Phase 2")

    def get_swap_status(self, swap_id: str) -> dict:
        """Check status of an existing swap."""
        raise NotImplementedError("Boltz not connected — Phase 2")
