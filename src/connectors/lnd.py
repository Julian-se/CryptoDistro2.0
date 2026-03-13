"""
LND connector — STUB for Phase 2 Lightning integration.

"Bygg arkitekturen med Lightning-integration i åtanke, men bygg det som
en modulär anslutningspunkt snarare än som ett inbyggt beroende från dag ett."

The interface is defined here so the rest of the system can reference it.
Actual implementation comes when capital reaches ~$4k and Lightning
channels become worthwhile.
"""

import logging
from decimal import Decimal

logger = logging.getLogger(__name__)


class LndConnector:
    """Placeholder for LND Lightning Network integration."""

    def __init__(self):
        logger.info("LND connector initialized (STUB — not connected)")
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    def get_info(self) -> dict:
        """Get node info. Returns empty dict until connected."""
        return {}

    def get_balance(self) -> dict:
        """Get on-chain + channel balances."""
        return {
            "onchain_btc": Decimal("0"),
            "channel_local_btc": Decimal("0"),
            "channel_remote_btc": Decimal("0"),
            "total_btc": Decimal("0"),
        }

    def send_payment(self, invoice: str) -> dict:
        """Pay a Lightning invoice."""
        raise NotImplementedError("LND not connected — Phase 2")

    def create_invoice(self, amount_sats: int, memo: str = "") -> dict:
        """Create a Lightning invoice for receiving payments."""
        raise NotImplementedError("LND not connected — Phase 2")

    def get_channel_list(self) -> list[dict]:
        """List all Lightning channels."""
        return []
