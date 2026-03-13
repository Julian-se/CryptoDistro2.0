"""
Market Discovery Engine — dynamically finds and ranks emerging markets.

Instead of hardcoded countries, this scans ~80 EM currencies against
Noones offer data + Binance spot, then ranks by opportunity score.

Two scan modes:
  DEEP  — scans all currencies, runs every 4-6 hours
  QUICK — refreshes only the top markets, runs every 5-10 min

Opportunity score = premium_pct × sqrt(offer_count) × reliability_factor
  Higher spread + more liquidity + reliable payment methods = higher score.

Results are persisted to SQLite so history can inform confidence:
  A market showing 8% premium consistently for 7 days is more reliable
  than a one-off spike.
"""

import logging
import math
import sqlite3
import time
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from src.connectors.binance import BinanceConnector
from src.connectors.fxrates import FxRatesConnector
from src.connectors.noones import NoonesConnector
from src.core.config import get_config

logger = logging.getLogger(__name__)

# ── Parallel-rate currencies ────────────────────────────────────────────────
# These use black-market rates. Official FX understates the real premium.
# We flag them separately rather than calculating a misleading number.
PARALLEL_RATE_CURRENCIES = {"VES", "ARS", "LBP", "SDG", "IQD"}

# ── Payment method risk classification ─────────────────────────────────────
# Irreversible = low chargeback risk. Reversible = avoid or price-in extra %.
IRREVERSIBLE_METHODS = {
    # African mobile money
    "mpesa", "m-pesa", "airtel-money", "mtn-mobile-money", "orange-money",
    "mtn-momo", "moov-money", "wave", "airtel-money-kenya", "airtel-tigo",
    "tigopesa", "tigo-pesa", "vodacom-m-pesa", "m-pesa-ethiopia",
    # African bank transfers
    "first-bank-of-nigeria", "gtbank-guaranty-trust-bank", "zenith-bank",
    "access-bank", "uba-united-bank-for-africa", "opay", "kuda",
    "first-bank", "wema-bank", "sterling-bank",
    "ghipss-instant-pay", "nip-nibss-instant-payment",
    # Latin American
    "pago-movil", "pagomovil",
    "cbu-cvu",
    "transferencia-bancaria",
    "spei-sistema-de-pagos-electronicos-interbancarios",
    # Asian
    "bkash", "nagad", "rocket", "upay",
    "jazzcash", "easypaisa",
    "gcash", "paymaya",
    "promptpay", "truemoney",
    "dana",
    # European / other
    "swish", "sepa", "faster-payments", "bankgiro",
    "imps-transfer", "neft-national-electronic-funds-transfer",
    "upi", "upi123pay",
    # SEPA variants
    "sct-inst",
}

REVERSIBLE_METHODS = {
    "paypal", "paypal-business-payments",
    "credit-card", "visa-debit-credit-card",
    "american-express-card", "discover-credit-cards",
    "cashapp", "cash-app", "cashapp-payment",
    "venmo",
    "chime-instant-transfers",
    "apple-cash",
}

# ── Comprehensive EM currency list to scan ─────────────────────────────────
EM_CURRENCIES = [
    # Sub-Saharan Africa (highest BTC premiums globally)
    "NGN",  # Nigeria
    "KES",  # Kenya
    "GHS",  # Ghana
    "TZS",  # Tanzania
    "UGX",  # Uganda
    "ZAR",  # South Africa
    "ETB",  # Ethiopia
    "RWF",  # Rwanda
    "XOF",  # West Africa (CFA)
    "MAD",  # Morocco
    "EGP",  # Egypt
    "DZD",  # Algeria
    "ZMW",  # Zambia
    "MWK",  # Malawi
    "MZN",  # Mozambique
    # Latin America
    "BRL",  # Brazil
    "COP",  # Colombia
    "VES",  # Venezuela (parallel rate)
    "PEN",  # Peru
    "ARS",  # Argentina (parallel rate)
    "CLP",  # Chile
    "BOB",  # Bolivia
    "UYU",  # Uruguay
    "DOP",  # Dominican Republic
    "GTQ",  # Guatemala
    "HNL",  # Honduras
    "CRC",  # Costa Rica
    # South/Southeast Asia
    "PKR",  # Pakistan
    "BDT",  # Bangladesh
    "LKR",  # Sri Lanka
    "NPR",  # Nepal
    "MMK",  # Myanmar
    "VND",  # Vietnam
    "IDR",  # Indonesia
    "PHP",  # Philippines
    "INR",  # India
    "THB",  # Thailand
    "MYR",  # Malaysia
    "KHR",  # Cambodia
    # Middle East / Central Asia
    "TRY",  # Turkey
    "UAH",  # Ukraine
    "KZT",  # Kazakhstan
    "UZS",  # Uzbekistan
    "GEL",  # Georgia
    "AMD",  # Armenia
    "AZN",  # Azerbaijan
    # Eastern Europe
    "HUF",  # Hungary
    "RON",  # Romania
    "BGN",  # Bulgaria
    "RSD",  # Serbia
    # Nordic/local (your base market)
    "SEK",  # Sweden
    "NOK",  # Norway
    # Reserve currencies (baseline comparison)
    "USD",
    "EUR",
]

# Country names for display
CURRENCY_TO_COUNTRY = {
    "NGN": ("Nigeria",     "🇳🇬"),
    "KES": ("Kenya",       "🇰🇪"),
    "GHS": ("Ghana",       "🇬🇭"),
    "TZS": ("Tanzania",    "🇹🇿"),
    "UGX": ("Uganda",      "🇺🇬"),
    "ZAR": ("South Africa","🇿🇦"),
    "ETB": ("Ethiopia",    "🇪🇹"),
    "RWF": ("Rwanda",      "🇷🇼"),
    "XOF": ("W.Africa CFA","🌍"),
    "MAD": ("Morocco",     "🇲🇦"),
    "EGP": ("Egypt",       "🇪🇬"),
    "DZD": ("Algeria",     "🇩🇿"),
    "ZMW": ("Zambia",      "🇿🇲"),
    "MWK": ("Malawi",      "🇲🇼"),
    "MZN": ("Mozambique",  "🇲🇿"),
    "BRL": ("Brazil",      "🇧🇷"),
    "COP": ("Colombia",    "🇨🇴"),
    "VES": ("Venezuela",   "🇻🇪"),
    "PEN": ("Peru",        "🇵🇪"),
    "ARS": ("Argentina",   "🇦🇷"),
    "CLP": ("Chile",       "🇨🇱"),
    "BOB": ("Bolivia",     "🇧🇴"),
    "UYU": ("Uruguay",     "🇺🇾"),
    "DOP": ("Dom. Rep.",   "🇩🇴"),
    "GTQ": ("Guatemala",   "🇬🇹"),
    "HNL": ("Honduras",    "🇭🇳"),
    "CRC": ("Costa Rica",  "🇨🇷"),
    "PKR": ("Pakistan",    "🇵🇰"),
    "BDT": ("Bangladesh",  "🇧🇩"),
    "LKR": ("Sri Lanka",   "🇱🇰"),
    "NPR": ("Nepal",       "🇳🇵"),
    "MMK": ("Myanmar",     "🇲🇲"),
    "VND": ("Vietnam",     "🇻🇳"),
    "IDR": ("Indonesia",   "🇮🇩"),
    "PHP": ("Philippines", "🇵🇭"),
    "INR": ("India",       "🇮🇳"),
    "THB": ("Thailand",    "🇹🇭"),
    "MYR": ("Malaysia",    "🇲🇾"),
    "KHR": ("Cambodia",    "🇰🇭"),
    "TRY": ("Turkey",      "🇹🇷"),
    "UAH": ("Ukraine",     "🇺🇦"),
    "KZT": ("Kazakhstan",  "🇰🇿"),
    "UZS": ("Uzbekistan",  "🇺🇿"),
    "GEL": ("Georgia",     "🇬🇪"),
    "AMD": ("Armenia",     "🇦🇲"),
    "AZN": ("Azerbaijan",  "🇦🇿"),
    "HUF": ("Hungary",     "🇭🇺"),
    "RON": ("Romania",     "🇷🇴"),
    "BGN": ("Bulgaria",    "🇧🇬"),
    "RSD": ("Serbia",      "🇷🇸"),
    "SEK": ("Sweden",      "🇸🇪"),
    "NOK": ("Norway",      "🇳🇴"),
    "USD": ("USA/Global",  "🌐"),
    "EUR": ("Eurozone",    "🇪🇺"),
}


@dataclass
class PaymentMethodRank:
    slug: str
    label: str
    offer_count: int
    median_premium_pct: float
    avg_seller_score: float
    avg_trades: float            # avg trade count of sellers using this method
    risk: str                    # "low" / "medium" / "high"
    score: float = 0.0           # composite score

    def __post_init__(self):
        risk_mult = {"low": 1.0, "medium": 0.7, "high": 0.3}.get(self.risk, 0.5)
        self.score = (
            self.offer_count * 0.4
            + self.median_premium_pct * 0.3
            + (self.avg_seller_score / 100) * 0.2
            + math.log1p(self.avg_trades) * 0.1
        ) * risk_mult


@dataclass
class DiscoveredMarket:
    currency: str
    country: str
    flag: str
    spot_usd: Decimal
    premium_pct: float           # vs Binance spot
    offer_count: int
    parallel_rate: bool          # official FX unreliable
    payment_methods: list[PaymentMethodRank]
    opportunity_score: float = 0.0
    scanned_at: float = field(default_factory=time.time)
    scan_count: int = 1          # how many scans confirmed this premium
    consistent_days: int = 0     # days premium has been in range

    def __post_init__(self):
        if not self.parallel_rate:
            liquidity = math.sqrt(max(self.offer_count, 1))
            self.opportunity_score = self.premium_pct * liquidity

    @property
    def top_method(self) -> PaymentMethodRank | None:
        if not self.payment_methods:
            return None
        return max(self.payment_methods, key=lambda m: m.score)

    @property
    def tier1_methods(self) -> list[PaymentMethodRank]:
        return [m for m in self.payment_methods if m.risk == "low"]

    def format_summary(self) -> str:
        pm = self.top_method
        method_str = f"via {pm.label}" if pm else "no methods ranked"
        flag = "⚠️ parallel rate" if self.parallel_rate else ""
        return (
            f"{self.flag} {self.country:<14} "
            f"{self.premium_pct:>+6.1f}%  "
            f"score={self.opportunity_score:>5.1f}  "
            f"{method_str}  {flag}"
        )


class MarketDiscoveryEngine:
    """
    Dynamically discovers and ranks EM markets by scanning Noones
    across all configured currencies.

    Two scan modes:
      deep_scan()  — scans all EM_CURRENCIES, slow, run every few hours
      quick_scan() — re-scans only current top markets, fast, run frequently
    """

    def __init__(
        self,
        binance: BinanceConnector,
        noones: NoonesConnector,
        fx: FxRatesConnector,
    ):
        self.binance = binance
        self.noones = noones
        self.fx = fx
        cfg = get_config()
        db_path = cfg["database"]["path"]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self._create_tables()
        self._top_currencies: list[str] = []

    def _create_tables(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS market_discoveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency TEXT NOT NULL,
                country TEXT NOT NULL,
                premium_pct REAL NOT NULL,
                offer_count INTEGER NOT NULL,
                opportunity_score REAL NOT NULL,
                parallel_rate INTEGER NOT NULL DEFAULT 0,
                top_method TEXT,
                scanned_at REAL NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_disc_currency
                ON market_discoveries(currency, scanned_at);
        """)
        self.db.commit()

    # ── Core scanning ───────────────────────────────────────────────────────

    def _scan_currency(
        self, currency: str, spot_usd: Decimal, fx_rates: dict
    ) -> DiscoveredMarket | None:
        """Scan one currency: fetch offers, calculate premium, rank methods."""
        country, flag = CURRENCY_TO_COUNTRY.get(currency, (currency, "🌐"))
        parallel = currency in PARALLEL_RATE_CURRENCIES

        # Get FX rate
        fx_rate = fx_rates.get(currency)
        if fx_rate is None:
            return None

        # Fetch offers
        offers = self.noones.get_offers(
            offer_type="sell",
            currency_code=currency,
            crypto_currency_code="BTC",
            limit=20,
        )

        if len(offers) < 2:
            return None

        # Calculate premium from median price
        prices = sorted([float(o["price"]) for o in offers if o["price"] > 0])
        if not prices:
            return None
        median_local = prices[len(prices) // 2]
        price_in_usd = median_local / fx_rate
        premium_pct = (price_in_usd - float(spot_usd)) / float(spot_usd) * 100

        # Rank payment methods
        pm_ranks = self._rank_payment_methods(offers)

        market = DiscoveredMarket(
            currency=currency,
            country=country,
            flag=flag,
            spot_usd=spot_usd,
            premium_pct=premium_pct,
            offer_count=len(offers),
            parallel_rate=parallel,
            payment_methods=pm_ranks,
        )

        # Persist to DB
        top_method = market.top_method.label if market.top_method else None
        self.db.execute(
            """INSERT INTO market_discoveries
               (currency, country, premium_pct, offer_count,
                opportunity_score, parallel_rate, top_method, scanned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (currency, country, premium_pct, len(offers),
             market.opportunity_score, int(parallel), top_method, time.time()),
        )
        self.db.commit()

        return market

    def _rank_payment_methods(self, offers: list[dict]) -> list[PaymentMethodRank]:
        """Group offers by payment method and rank each."""
        from collections import defaultdict
        groups: dict[str, list[dict]] = defaultdict(list)
        for offer in offers:
            slug = (offer.get("payment_method_slug") or "").lower().strip()
            if slug:
                groups[slug].append(offer)

        ranks = []
        for slug, group_offers in groups.items():
            if not group_offers:
                continue
            prices = sorted([float(o["price"]) for o in group_offers if o["price"] > 0])
            if not prices:
                continue
            median_price = prices[len(prices) // 2]
            avg_score = sum(o.get("seller_score", 0) for o in group_offers) / len(group_offers)
            avg_trades = sum(o.get("seller_trades", 0) for o in group_offers) / len(group_offers)
            label = group_offers[0].get("payment_method", slug)

            risk = self._classify_risk(slug)

            ranks.append(PaymentMethodRank(
                slug=slug,
                label=label,
                offer_count=len(group_offers),
                median_premium_pct=0.0,  # filled below if needed
                avg_seller_score=avg_score,
                avg_trades=avg_trades,
                risk=risk,
            ))

        ranks.sort(key=lambda r: r.score, reverse=True)
        return ranks[:10]  # top 10 methods per market

    def _classify_risk(self, slug: str) -> str:
        """Classify payment method risk based on reversibility."""
        slug_lower = slug.lower()
        for irrev in IRREVERSIBLE_METHODS:
            if irrev in slug_lower or slug_lower in irrev:
                return "low"
        for rev in REVERSIBLE_METHODS:
            if rev in slug_lower or slug_lower in rev:
                return "high"
        return "medium"

    # ── Public scan methods ─────────────────────────────────────────────────

    def deep_scan(self, currencies: list[str] | None = None) -> list[DiscoveredMarket]:
        """
        Scan all EM currencies. Takes 2-5 minutes depending on API rate limits.
        Run every 4-6 hours.
        """
        currencies = currencies or EM_CURRENCIES
        logger.info(f"Deep scan starting — {len(currencies)} currencies")

        try:
            spot_usd = self.binance.get_spot_price("BTCUSDT")
            fx_rates = self.fx.get_rates()
        except Exception as e:
            logger.error(f"Deep scan aborted: {e}")
            return []

        results = []
        for i, currency in enumerate(currencies):
            try:
                market = self._scan_currency(currency, spot_usd, fx_rates)
                if market:
                    results.append(market)
                    logger.debug(f"[{i+1}/{len(currencies)}] {market.format_summary()}")
            except Exception as e:
                logger.warning(f"Skipping {currency}: {e}")
            # Brief delay to respect API rate limits
            time.sleep(0.2)

        ranked = self._apply_ranking(results)
        self._top_currencies = [m.currency for m in ranked[:15]]
        logger.info(f"Deep scan complete. Top markets: {self._top_currencies[:5]}")
        return ranked

    def quick_scan(self) -> list[DiscoveredMarket]:
        """
        Re-scan only the current top markets. Fast — runs every 5-10 min.
        Falls back to deep_scan if no top markets yet.
        """
        if not self._top_currencies:
            logger.info("No top markets cached, running deep scan first")
            return self.deep_scan()

        logger.debug(f"Quick scan: {self._top_currencies}")
        try:
            spot_usd = self.binance.get_spot_price("BTCUSDT")
            fx_rates = self.fx.get_rates()
        except Exception as e:
            logger.error(f"Quick scan aborted: {e}")
            return []

        results = []
        for currency in self._top_currencies:
            try:
                market = self._scan_currency(currency, spot_usd, fx_rates)
                if market:
                    results.append(market)
            except Exception as e:
                logger.warning(f"Quick scan skip {currency}: {e}")
            time.sleep(0.1)

        return self._apply_ranking(results)

    def _apply_ranking(self, markets: list[DiscoveredMarket]) -> list[DiscoveredMarket]:
        """
        Final ranking: sort by opportunity score, parallel-rate markets last.
        """
        real = [m for m in markets if not m.parallel_rate and m.premium_pct > 0]
        parallel = [m for m in markets if m.parallel_rate]
        low = [m for m in markets if not m.parallel_rate and m.premium_pct <= 0]

        real.sort(key=lambda m: m.opportunity_score, reverse=True)
        parallel.sort(key=lambda m: m.country)
        low.sort(key=lambda m: m.premium_pct, reverse=True)

        return real + parallel + low

    # ── History & consistency ────────────────────────────────────────────────

    def get_consistent_markets(self, min_days: int = 3, min_premium: float = 3.0) -> list[dict]:
        """
        Markets that have shown premium consistently over time.
        More reliable than a single scan spike.
        """
        cutoff = time.time() - (min_days * 86400)
        rows = self.db.execute(
            """
            SELECT currency, country,
                   COUNT(*) as scan_count,
                   AVG(premium_pct) as avg_premium,
                   MIN(premium_pct) as min_premium,
                   MAX(premium_pct) as max_premium,
                   AVG(opportunity_score) as avg_score,
                   top_method
            FROM market_discoveries
            WHERE scanned_at > ? AND premium_pct > ? AND parallel_rate = 0
            GROUP BY currency
            HAVING COUNT(*) >= 3
            ORDER BY avg_premium DESC
            """,
            (cutoff, min_premium),
        ).fetchall()
        return [dict(r) for r in rows]

    def close(self):
        self.db.close()
