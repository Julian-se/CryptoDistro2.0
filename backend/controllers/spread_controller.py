"""
Feedforward Spread Controller.
Recommends optimal Noones sell margin per market based on live premiums
and historical fill rate calibration.
"""
import numpy as np
from backend.schemas.dashboard import SpreadSignal

# Minimum viable net margin above all fees
BINANCE_FEE = 0.001   # 0.1% taker
NOONES_FEE = 0.0      # no platform fee for sellers
LN_FEE = 0.0001       # negligible
MIN_NET_TARGET = 0.005  # 0.5% net profit floor
MIN_VIABLE_MARGIN = (BINANCE_FEE + NOONES_FEE + LN_FEE + MIN_NET_TARGET) * 100  # ~0.6%

# Target: capture 80% of the structural market premium
MARGIN_CAPTURE_RATE = 0.80


class SpreadController:
    def run(
        self,
        market_premiums: dict[str, float],   # {currency: premium_pct}
        trade_history: list[dict] | None = None,
    ) -> SpreadSignal:
        """
        Args:
            market_premiums: live premium % per currency from PremiumMonitor
            trade_history: completed cycles, each with 'market', 'buy_price', 'sell_price'
        """
        trade_history = trade_history or []
        recommended: dict[str, float] = {}
        notes: dict[str, str] = {}

        for currency, raw_premium in market_premiums.items():
            # Cap anomalously high premiums at 1.5× expected max (prevents overpricing)
            effective_premium = min(raw_premium, 15.0)

            # Historical calibration: check if realized margins suggest room to adjust
            adjustment = 0.0
            market_cycles = [
                c for c in trade_history
                if c.get("market") == currency and c.get("buy_price") and c.get("sell_price")
            ]

            if len(market_cycles) >= 5:
                realized = []
                for c in market_cycles[-20:]:  # last 20 cycles
                    try:
                        margin = float(c["sell_price"]) / float(c["buy_price"]) - 1.0
                        realized.append(margin * 100)
                    except (ValueError, ZeroDivisionError):
                        continue
                if realized:
                    avg_realized = float(np.mean(realized))
                    # If realised < 75% of market, we have room to push up
                    if avg_realized < effective_premium * 0.75:
                        adjustment = +0.5
                        notes[currency] = f"history: +0.5% adj (avg realized {avg_realized:.1f}% < 75% of market)"
                    else:
                        notes[currency] = f"history: no adj (avg realized {avg_realized:.1f}%)"
            else:
                notes[currency] = "no history — using 80% of market"

            candidate = effective_premium * MARGIN_CAPTURE_RATE + adjustment
            margin = max(MIN_VIABLE_MARGIN, round(candidate, 1))
            recommended[currency] = margin

        return SpreadSignal(
            recommended_margins=recommended,
            market_premiums=market_premiums,
            calibration_notes=notes,
        )
