"""
Feedforward Velocity Controller.
Recommends optimal active trading hours per market and ranks markets by
revenue/hour adjusted for refill complexity.
"""
from backend.schemas.dashboard import VelocitySignal

BASE_TRADE = 60.0
MAX_TRADE = 200.0
MIN_REVENUE_PER_HOUR = 2.0   # USD — opportunity cost threshold

REFILL_DISCOUNT = {
    "verified": 1.0,
    "partial": 0.85,
    "unverified": 0.70,
}

CB_RATE_LN = 0.012 / 7  # daily chargeback rate


class VelocityController:
    def run(
        self,
        noones_balance_usd: float,
        market_configs: list[dict],          # from settings.yaml premium_monitor.markets
        market_premiums: dict[str, float],   # {currency: premium_pct}
        refill_statuses: dict[str, str],     # {currency: "verified"|"partial"|"unverified"}
    ) -> VelocitySignal:
        recommended_hours: dict[str, int] = {}
        revenue_per_hour: dict[str, float] = {}
        priority_scores: dict[str, float] = {}

        for market in market_configs:
            currency = market["currency"]
            name = market["name"]

            # Fiat verification minutes (from market config or default)
            fiat_minutes = _fiat_minutes_for_market(market)
            if fiat_minutes <= 0:
                continue

            # Effective spread
            spread = market_premiums.get(currency, 0.0)
            if spread <= 0:
                spread = (
                    float(market.get("expected_spread_low", 6))
                    + float(market.get("expected_spread_high", 8))
                ) / 2.0

            # Trade size given current capital
            trade_size = min(MAX_TRADE, BASE_TRADE + (noones_balance_usd - 500) * 0.05)
            trade_size = max(BASE_TRADE, trade_size)

            # Cycles per hour
            cycles_per_hour = 60.0 / fiat_minutes

            # Revenue per hour = (spread/100 × trade_size) × cycles
            gross_per_hour = (spread / 100.0) * trade_size * cycles_per_hour
            cb_per_hour = CB_RATE_LN * trade_size * cycles_per_hour
            net_per_hour = gross_per_hour - cb_per_hour
            revenue_per_hour[currency] = round(net_per_hour, 2)

            # Recommended hours: trade until marginal net revenue < threshold
            if net_per_hour > MIN_REVENUE_PER_HOUR:
                hours = min(12, max(4, int(noones_balance_usd / (trade_size * (spread / 100.0) * cycles_per_hour + 0.01))))
                hours = min(hours, 16)
            else:
                hours = 4  # minimum

            recommended_hours[currency] = hours

            # Priority score: revenue × refill_discount
            status = refill_statuses.get(currency, "unverified")
            discount = REFILL_DISCOUNT.get(status, 0.7)
            priority_scores[currency] = net_per_hour * discount

        # Sort by priority
        market_priority = sorted(priority_scores.keys(), key=lambda c: priority_scores[c], reverse=True)

        capital_note = ""
        if noones_balance_usd < 100:
            capital_note = "Low capital — focus on 1 market only"
        elif noones_balance_usd < 300:
            capital_note = "Limited capital — 2 markets max"

        return VelocitySignal(
            recommended_hours=recommended_hours,
            market_priority=market_priority,
            revenue_per_hour=revenue_per_hour,
            capital_constraint_note=capital_note,
        )


def _fiat_minutes_for_market(market: dict) -> float:
    """Infer fiat verification minutes from CLAUDE.md scenario defaults."""
    DEFAULTS = {
        "Nigeria": 25.0, "NGN": 25.0,
        "Argentina": 20.0, "ARS": 20.0,
        "Venezuela": 15.0, "VES": 15.0,
        "Kenya": 20.0, "KES": 20.0,
        "Sverige": 25.0, "SEK": 25.0,
        "Sweden": 25.0,
    }
    key = market.get("currency") or market.get("name", "")
    return DEFAULTS.get(key, 20.0)
