"""
Feedforward BTC Inventory Controller.
Predicts hours until Noones BTC balance hits zero using linear regression.
Fires a refill alert before depletion, not after.
"""
import time
import numpy as np
from backend.schemas.dashboard import InventorySignal


class InventoryController:
    SAFETY_BUFFER_HOURS = 2.0
    CONFIDENCE_THRESHOLD = 0.5
    TARGET_HOURS = 8.0

    def run(
        self,
        balance_log_entries: list[dict],
        btc_price: float,
    ) -> InventorySignal:
        """
        Args:
            balance_log_entries: list of dicts with keys: logged_at, btc
                                 (filtered to 'noones' platform, last 24h)
            btc_price: current BTC/USD spot price
        """
        if not balance_log_entries or len(balance_log_entries) < 2:
            return InventorySignal(
                predicted_hours_to_empty=99.0,
                refill_needed=False,
                confidence=0.0,
            )

        timestamps = np.array([e["logged_at"] for e in balance_log_entries], dtype=float)
        balances = np.array([e["btc"] for e in balance_log_entries], dtype=float)

        # Normalize timestamps to hours from first point
        t0 = timestamps[0]
        hours = (timestamps - t0) / 3600.0

        # Linear fit: balance = slope * hours + intercept
        try:
            coeffs = np.polyfit(hours, balances, deg=1)
            slope = float(coeffs[0])   # BTC/hour change
            intercept = float(coeffs[1])

            # Compute R² as confidence measure
            predicted = np.polyval(coeffs, hours)
            ss_res = np.sum((balances - predicted) ** 2)
            ss_tot = np.sum((balances - np.mean(balances)) ** 2)
            r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 1e-10 else 0.0
            confidence = max(0.0, min(1.0, r2))
        except Exception:
            return InventorySignal(predicted_hours_to_empty=99.0, refill_needed=False, confidence=0.0)

        current_btc = float(balances[-1])

        # If balance is flat or growing, no refill needed
        if slope >= 0.0:
            return InventorySignal(
                predicted_hours_to_empty=99.0,
                refill_needed=False,
                confidence=confidence,
                consumption_rate_btc_per_hour=0.0,
            )

        consumption_rate = abs(slope)  # BTC/hour
        hours_to_empty = current_btc / consumption_rate if consumption_rate > 0 else 99.0
        hours_to_empty = min(hours_to_empty, 99.0)

        refill_needed = (
            hours_to_empty < self.SAFETY_BUFFER_HOURS
            and confidence > self.CONFIDENCE_THRESHOLD
        )

        # Recommended refill: cover TARGET_HOURS at current consumption rate
        target_btc = consumption_rate * self.TARGET_HOURS
        shortfall_btc = max(0.0, target_btc - current_btc)
        recommended_refill_usd = shortfall_btc * btc_price

        return InventorySignal(
            predicted_hours_to_empty=round(hours_to_empty, 1),
            refill_needed=refill_needed,
            confidence=round(confidence, 2),
            recommended_refill_usd=round(recommended_refill_usd, 2),
            consumption_rate_btc_per_hour=round(consumption_rate, 6),
        )
