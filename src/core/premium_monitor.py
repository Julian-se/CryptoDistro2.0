"""
Premium Monitor — actionable market intelligence, not just numbers.

Output is structured as decisions, not data:
  - ACT NOW: which market to post offers in, at what margin, via what method
  - WATCH: markets approaching opportunity
  - DATA ISSUE: markets where FX rate is unreliable (parallel rate problem)
  - AVOID: low demand, not worth spreading today

Venezuela/Argentina FX note:
  Official rates (from er-api) don't reflect real P2P rates. These markets
  use black market / parallel rates. We flag these as DATA_ISSUE until
  a parallel rate source is integrated.
"""

import logging
import time
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from src.connectors.binance import BinanceConnector
from src.connectors.fxrates import FxRatesConnector
from src.connectors.noones import NoonesConnector
from src.core.config import get_config

logger = logging.getLogger(__name__)

# Markets where official FX rates are unreliable (parallel/black market exists)
PARALLEL_RATE_MARKETS = {"VES", "ARS"}


class Action(Enum):
    ACT_NOW   = "ACT_NOW"
    WATCH     = "WATCH"
    AVOID     = "AVOID"
    DATA_ISSUE = "DATA_ISSUE"


@dataclass
class MarketPremium:
    name: str
    flag: str
    currency: str
    btc_spot_usd: Decimal
    btc_local_price: Decimal
    btc_local_in_usd: Decimal
    premium_pct: Decimal
    expected_low: float
    expected_high: float
    payment_methods: list[dict]   # [{slug, label, risk}]
    active_payment_method: str    # What was seen on best offer
    offer_count: int
    fx_rate: float
    timestamp: float = field(default_factory=time.time)

    @property
    def action(self) -> Action:
        if self.currency in PARALLEL_RATE_MARKETS:
            return Action.DATA_ISSUE
        p = float(self.premium_pct)
        if p >= self.expected_low:
            return Action.ACT_NOW
        if p >= (self.expected_low * 0.7):
            return Action.WATCH
        return Action.AVOID

    @property
    def is_anomaly(self) -> bool:
        """Premium is more than 2x above expected high — verify before acting."""
        return float(self.premium_pct) > self.expected_high * 2

    @property
    def suggested_margin(self) -> float:
        """
        Suggested Noones offer margin.
        Post slightly below current market premium to attract volume,
        but ensure it covers our CEX buy cost + fees.
        """
        p = float(self.premium_pct)
        # Cap suggestion at 2x expected high to avoid acting on anomalies blindly
        effective = min(p, self.expected_high * 1.5)
        # Post at 80% of observed premium to be competitive
        return round(effective * 0.80, 1)

    @property
    def tier1_methods(self) -> list[str]:
        """Payment methods rated 'low' risk."""
        return [m["label"] for m in self.payment_methods if m.get("risk") == "low"]


@dataclass
class PremiumSnapshot:
    """Full market scan result."""
    markets: list[MarketPremium]
    btc_spot_usd: Decimal
    scanned_at: float = field(default_factory=time.time)

    @property
    def act_now(self) -> list[MarketPremium]:
        return [m for m in self.markets if m.action == Action.ACT_NOW]

    @property
    def watching(self) -> list[MarketPremium]:
        return [m for m in self.markets if m.action == Action.WATCH]

    @property
    def data_issues(self) -> list[MarketPremium]:
        return [m for m in self.markets if m.action == Action.DATA_ISSUE]

    @property
    def avoid(self) -> list[MarketPremium]:
        return [m for m in self.markets if m.action == Action.AVOID]


class PremiumMonitor:

    def __init__(
        self,
        binance: BinanceConnector,
        noones: NoonesConnector,
        fx: FxRatesConnector,
        telegram=None,
    ):
        self.binance = binance
        self.noones = noones
        self.fx = fx
        self.telegram = telegram
        cfg = get_config()
        self.markets_cfg = cfg.get("premium_monitor", {}).get("markets", [])
        self.refresh_interval = cfg.get("premium_monitor", {}).get("refresh_interval_sec", 60)
        self.alert_above_pct = cfg.get("premium_monitor", {}).get("alert_above_pct", 5.0)
        self._last_snapshot: PremiumSnapshot | None = None

    def _fetch_market(self, market: dict, spot_usd: Decimal) -> MarketPremium | None:
        currency = market["currency"]

        try:
            fx_rate = self.fx.usd_to(currency)
        except Exception as e:
            logger.warning(f"{market['name']}: FX rate unavailable — {e}")
            return None

        offers = self.noones.get_offers(
            offer_type="sell",
            currency_code=currency,
            crypto_currency_code="BTC",
            limit=10,
        )

        if not offers:
            logger.debug(f"{market['name']}: no offers")
            return None

        prices = sorted([o["price"] for o in offers if o["price"] > 0])
        if not prices:
            return None

        local_price = prices[len(prices) // 2]  # median
        local_in_usd = Decimal(str(self.fx.local_to_usd(float(local_price), currency)))
        premium_pct = ((local_in_usd - spot_usd) / spot_usd) * 100
        active_method = offers[0].get("payment_method", "—") if offers else "—"

        return MarketPremium(
            name=market["name"],
            flag=market["flag"],
            currency=currency,
            btc_spot_usd=spot_usd,
            btc_local_price=local_price,
            btc_local_in_usd=local_in_usd,
            premium_pct=premium_pct,
            expected_low=market["expected_spread_low"],
            expected_high=market["expected_spread_high"],
            payment_methods=market.get("payment_methods", []),
            active_payment_method=active_method,
            offer_count=len(offers),
            fx_rate=fx_rate,
        )

    def scan_all(self) -> PremiumSnapshot:
        try:
            spot_usd = self.binance.get_spot_price("BTCUSDT")
        except Exception as e:
            logger.error(f"Cannot fetch Binance spot: {e}")
            return PremiumSnapshot(markets=[], btc_spot_usd=Decimal("0"))

        markets = []
        for cfg in self.markets_cfg:
            try:
                m = self._fetch_market(cfg, spot_usd)
                if m:
                    markets.append(m)
            except Exception as e:
                logger.error(f"Error scanning {cfg['name']}: {e}")

        # Sort: ACT_NOW first (by premium desc), then WATCH, then others
        markets.sort(
            key=lambda m: (
                0 if m.action == Action.ACT_NOW else
                1 if m.action == Action.WATCH else
                2 if m.action == Action.DATA_ISSUE else 3,
                -float(m.premium_pct)
            )
        )

        snapshot = PremiumSnapshot(markets=markets, btc_spot_usd=spot_usd)
        self._last_snapshot = snapshot
        return snapshot

    def get_last_snapshot(self) -> PremiumSnapshot | None:
        return self._last_snapshot

    # ------------------------------------------------------------------ #
    #  Actionable formatting                                               #
    # ------------------------------------------------------------------ #

    def format_actionable(self, snapshot: PremiumSnapshot) -> str:
        """
        Explain-mode output: not just numbers, but why and what to do.

        Markdown rule enforced here: every _italic_ span must open AND close
        in the same string — never split across separate append() calls.
        """
        import datetime
        ts = datetime.datetime.fromtimestamp(snapshot.scanned_at).strftime("%H:%M")
        lines = [
            f"📊 *MARKET INTEL* — {ts}",
            f"BTC spot: *${snapshot.btc_spot_usd:,.0f}* (Binance)",
            "_Cost basis. The gap between this and what P2P customers pay is your margin._",
        ]

        # ── ACT NOW ──────────────────────────────────────────────────────
        if snapshot.act_now:
            lines.append(f"\n🟢 *ACT NOW — {len(snapshot.act_now)} market(s) in range*")
            lines.append("─" * 36)
            lines.append("_Premium within historical range. Post a sell offer now._")
            for m in snapshot.act_now:
                p = float(m.premium_pct)
                methods = ", ".join(m.tier1_methods) if m.tier1_methods else m.active_payment_method
                reason = _premium_reason(m.currency)
                net = max(0, m.suggested_margin - 1.0)

                anomaly_line = ""
                if m.is_anomaly:
                    anomaly_line = (
                        f"\n  ⚠️ _Anomaly: {p:.0f}% is {p/m.expected_high:.1f}x above normal — verify before large trades_"
                    )

                lines.append(
                    f"\n{m.flag} *{m.name}*\n"
                    f"  Premium: `{p:+.1f}%` _(expected {m.expected_low:.0f}–{m.expected_high:.0f}%)_\n"
                    f"  _Why: {reason}_\n"
                    f"  Active offers on Noones: {m.offer_count}"
                    f"{anomaly_line}\n"
                    f"  *What to do:*\n"
                    f"  1. Noones → New sell offer\n"
                    f"  2. Margin `+{m.suggested_margin:.0f}%` _(80% of observed — competitive)_\n"
                    f"  3. Method: *{methods}* _(irreversible = no chargeback risk)_\n"
                    f"  4. After sale: rebuy BTC on Binance at spot\n"
                    f"  _Net margin after fees: ~{net:.0f}%_"
                )

        # ── WATCH ────────────────────────────────────────────────────────
        if snapshot.watching:
            lines.append(f"\n👁 *WATCH — {len(snapshot.watching)} market(s) building*")
            lines.append("─" * 36)
            lines.append("_Positive premium but below your threshold. Check back in 30–60 min._")
            for m in snapshot.watching:
                p = float(m.premium_pct)
                needed = m.expected_low - p
                lines.append(
                    f"\n{m.flag} *{m.name}*  `{p:+.1f}%`\n"
                    f"  _Needs +{needed:.1f}% more to reach {m.expected_low:.0f}% threshold_\n"
                    f"  {m.offer_count} active offers on Noones"
                )

        # ── DATA ISSUES ──────────────────────────────────────────────────
        if snapshot.data_issues:
            lines.append("\n⚙️ *PARALLEL RATE MARKETS*")
            lines.append("─" * 36)
            lines.append(
                "_Official FX rate is fiction here. The government rate and real street rate diverge massively. "
                "The number below is unreliable — check Noones directly for real price._"
            )
            for m in snapshot.data_issues:
                p = float(m.premium_pct)
                lines.append(
                    f"\n{m.flag} *{m.name}*\n"
                    f"  Official FX shows: `{p:+.1f}%` _(unreliable)_\n"
                    f"  Real P2P premium est: *{m.expected_low:.0f}–{m.expected_high:.0f}%*\n"
                    f"  Search {m.currency} sellers on Noones and compare vs your USD cost"
                )

        # ── AVOID ────────────────────────────────────────────────────────
        if snapshot.avoid:
            lines.append(f"\n🔴 *AVOID — {len(snapshot.avoid)} market(s)*")
            lines.append("─" * 36)
            lines.append("_Premium too low to cover fees. Skip these today._")
            for m in snapshot.avoid:
                p = float(m.premium_pct)
                lines.append(f"  {m.flag} {m.name}  `{p:+.1f}%`")

        return "\n".join(lines)

    def scan_players(self, currency: str, limit: int = 20) -> str:
        """
        Fetch active sellers for a currency from both Noones and Binance P2P.
        Shows who the dominant players are, their trade counts, scores, payment
        methods — so you can position your offers competitively.
        """
        noones_offers = self.noones.get_offers(
            offer_type="sell",
            currency_code=currency.upper(),
            crypto_currency_code="BTC",
            limit=limit,
        )
        for o in noones_offers:
            o.setdefault("platform", "Noones")

        binance_offers = self.binance.get_p2p_offers(
            fiat=currency.upper(),
            asset="BTC",
            trade_type="SELL",
            rows=limit,
        )

        all_offers = noones_offers + binance_offers
        if not all_offers:
            return f"No sell offers found for {currency} on either platform."

        return _format_players(currency, all_offers)

    # Backward-compat alias used by old code
    def format_table(self, snapshot_or_list) -> str:
        if isinstance(snapshot_or_list, list):
            # old call signature passed a list — wrap it
            if not snapshot_or_list:
                return "No market data available."
            snapshot = PremiumSnapshot(
                markets=snapshot_or_list,
                btc_spot_usd=snapshot_or_list[0].btc_spot_usd if snapshot_or_list else Decimal("0"),
            )
        else:
            snapshot = snapshot_or_list
        return self.format_actionable(snapshot)

    def run_loop(self):
        logger.info(f"Premium monitor starting (refresh: {self.refresh_interval}s)")
        while True:
            snapshot = self.scan_all()
            if snapshot.act_now and self.telegram:
                msg = self.format_actionable(snapshot)
                self.telegram.send_alert_sync(msg)
            time.sleep(self.refresh_interval)


# ── Module-level helpers ──────────────────────────────────────────────────────

_PREMIUM_REASONS: dict[str, str] = {
    "NGN": "Nigeria limits USD access via official channels — locals pay a premium to get BTC as a dollar substitute",
    "KES": "Kenya has strong mobile money (M-Pesa) but limited crypto on-ramps, creating consistent P2P demand",
    "GHS": "Ghana restricts forex outflows — BTC is used to preserve value and move money abroad",
    "ZAR": "South Africa has capital controls limiting offshore transfers — BTC is used to bypass them",
    "TZS": "Tanzania has limited USD access and growing crypto adoption among youth",
    "UGX": "Uganda has high remittance demand and limited banking — P2P premium reflects access scarcity",
    "ETB": "Ethiopia has strict forex controls and a parallel dollar market",
    "XOF": "West Africa CFA zone — pegged to EUR but BTC demand driven by cross-border payments",
    "ARS": "Argentina inflation is 100%+ per year — people buy BTC to escape peso devaluation; parallel dollar rate creates a hidden premium",
    "VES": "Venezuela hyperinflation — the official bolivar rate is fiction; real USD value is 5-10x the official rate",
    "COP": "Colombia has high remittance inflows and strong P2P market, especially for Venezuelan migrants",
    "PEN": "Peru has a dollarized economy with stable P2P demand for cross-border value transfer",
    "PKR": "Pakistan restricts crypto officially but has massive underground P2P market driven by remittances",
    "BDT": "Bangladesh has one of the world's largest remittance markets — P2P BTC used to receive value faster",
    "LKR": "Sri Lanka had a major forex crisis in 2022 — BTC is now used as a USD substitute",
    "PHP": "Philippines is one of the top remittance-receiving countries globally — P2P BTC used by OFW workers",
    "VND": "Vietnam has capital controls and high P2P BTC volume, especially for cross-border e-commerce",
    "IDR": "Indonesia restricts crypto trading but has huge P2P volume — premium reflects demand vs. limited supply",
    "THB": "Thailand has strong gaming/online commerce demand for fast dollar-equivalent transfers",
    "TRY": "Turkey has had severe lira devaluation — locals pay premium for BTC as inflation hedge",
    "EGP": "Egypt devalued the pound multiple times since 2022 — P2P BTC demand driven by USD access scarcity",
    "MAD": "Morocco has strict capital controls — BTC used to send money abroad",
    "SEK": "Sweden has mature P2P market via Swish — premium is modest but reliable and low-risk",
}

_DEFAULT_REASON = "limited local banking infrastructure and restricted USD access drive demand for P2P BTC"


def _premium_reason(currency: str) -> str:
    """One-line explanation of why a premium exists in this market."""
    return _PREMIUM_REASONS.get(currency.upper(), _DEFAULT_REASON)


def _format_players(currency: str, offers: list[dict]) -> str:
    """
    Format cross-platform competitor intelligence for a given market.

    Shows sellers from Noones and Binance P2P side by side.
    Sorted by trade count — most experienced players first.
    """
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M")

    noones = [o for o in offers if o.get("platform") == "Noones"]
    binance = [o for o in offers if o.get("platform") == "Binance P2P"]

    # Sort each platform by trade count
    noones_ranked = sorted(noones, key=lambda o: o.get("seller_trades", 0), reverse=True)
    binance_ranked = sorted(binance, key=lambda o: o.get("seller_trades", 0), reverse=True)

    prices = [float(o["price"]) for o in offers if o.get("price", 0) > 0]
    price_min = min(prices) if prices else 0
    price_max = max(prices) if prices else 0

    noones_margins = [float(o["margin"]) for o in noones if o.get("margin") is not None]
    margin_str = (
        f"  Noones margin spread: `{min(noones_margins):+.1f}%` to `{max(noones_margins):+.1f}%`"
        if noones_margins else ""
    )

    lines = [
        f"👥 *{currency} MARKET PLAYERS* — {ts}",
        f"_{len(noones)} Noones offers + {len(binance)} Binance P2P offers_",
        f"_Price range across both: {price_min:,.0f}–{price_max:,.0f} {currency}_",
        margin_str,
        "_Sorted by lifetime trade count — veterans at the top_",
    ]

    # ── Noones ───────────────────────────────────────────────────────────
    if noones_ranked:
        lines.append("\n*NOONES*")
        lines.append("─" * 30)
        for i, o in enumerate(noones_ranked[:8], 1):
            seller = o.get("seller", "?")
            score = o.get("seller_score", 0)
            trades = o.get("seller_trades", 0)
            margin = o.get("margin")
            method = o.get("payment_method", "?")
            lo = float(o.get("min_amount", 0))
            hi = float(o.get("max_amount", 0))
            score_bar = "★" * min(5, int(score / 20)) if score else "—"
            margin_str_line = f"`{float(margin):+.1f}%`" if margin is not None else "_no margin data_"
            lines.append(
                f"*{i}. {seller}*  {score_bar} ({score})  {trades} trades\n"
                f"  Margin {margin_str_line}  |  {method}\n"
                f"  Range: {lo:,.0f}–{hi:,.0f} {currency}"
            )
    else:
        lines.append("\n*NOONES* — no offers found")

    # ── Binance P2P ───────────────────────────────────────────────────────
    if binance_ranked:
        lines.append("\n*BINANCE P2P*")
        lines.append("─" * 30)
        for i, o in enumerate(binance_ranked[:8], 1):
            seller = o.get("seller", "?")
            score = o.get("seller_score", 0)
            trades = o.get("seller_trades", 0)
            month = o.get("month_trades", 0)
            finish = o.get("finish_rate", 0)
            method = o.get("payment_method", "?") or "—"
            lo = float(o.get("min_amount", 0))
            hi = float(o.get("max_amount", 0))
            price = float(o.get("price", 0))
            merchant = " 🏪" if o.get("is_merchant") else ""
            online = " 🟢" if o.get("is_online") else ""
            score_bar = "★" * min(5, int(score / 20)) if score else "—"
            lines.append(
                f"*{i}. {seller}*{merchant}{online}  {score_bar} ({score}%)\n"
                f"  {trades} total trades  |  {month} this month  |  {finish}% completion\n"
                f"  Price: {price:,.0f} {currency}  |  {method}\n"
                f"  Range: {lo:,.0f}–{hi:,.0f} {currency}"
            )
    else:
        lines.append("\n*BINANCE P2P* — no offers found")

    # ── Positioning tip ───────────────────────────────────────────────────
    if noones_margins:
        min_m = min(noones_margins)
        max_m = max(noones_margins)
        lines.append(
            f"\n_Positioning: Noones margins run {min_m:+.1f}% to {max_m:+.1f}%. "
            f"Post near {min_m + (max_m - min_m) * 0.3:+.1f}% to be competitive without racing to the bottom._"
        )

    return "\n".join(lines)
