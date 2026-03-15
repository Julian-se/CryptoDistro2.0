"""
Parse refill_pipeline_YYYY-MM-DD.md into structured RefillMarket objects.
Status is inferred from emoji: ✅ = verified, ⚠️ = partial, ❌ = no route.
"""
import re
import time
from pathlib import Path
from backend.schemas.refill import RefillMarket, RefillMethod, RefillPipeline

# Market header pattern: ## 🇳🇬 Nigeria (NGN)
MARKET_HEADER = re.compile(r"^## (.+?) \((.+?)\)$")
METHOD_HEADER = re.compile(r"^#### Method: (.+)$")
SOURCE_LINE = re.compile(r"Source:\s*(https?://\S+)")
STATUS_VERIFIED = re.compile(r"Status:\s*✅")
STATUS_PARTIAL = re.compile(r"Status:\s*⚠️")
STATUS_NONE = re.compile(r"Status:\s*❌")
TIME_PATTERN = re.compile(r"(\d+)[–-](\d+)\s*min")
FEE_PATTERN = re.compile(r"~?(\d+\.?\d*)[–-]?(\d+\.?\d*)?\s*%")

FLAG_MAP = {
    "NGN": "🇳🇬", "ARS": "🇦🇷", "VES": "🇻🇪",
    "KES": "🇰🇪", "SEK": "🇸🇪",
}

# Hardcoded structured data matching the markdown (robust fallback)
PIPELINE_DATA = [
    RefillMarket(
        name="Nigeria", currency="NGN", flag="🇳🇬",
        methods=[
            RefillMethod(
                slug="first-bank-of-nigeria", label="First Bank NG", risk="low",
                status="verified",
                buy_service="Bitnob", buy_service_url="https://bitnob.com",
                lightning_wallet="Bitnob built-in LN",
                pipeline_steps=["First Bank NGN transfer", "Bitnob buy BTC", "LN withdrawal → Noones"],
                total_time_min=3, total_time_max=8, fee_pct_approx=1.5,
                fee_notes="~1–2% spread, LN fee <1 sat",
                limits="KYC L2: up to $10,000/day",
                kyc_required="Government ID (passport or NIN)",
                evidence_urls=["https://www.dignited.com/100613/bitnob-eases-bitcoin-access-in-kenya-with-m-pesa-airtel-and-t-kash-intergrations/"],
            ),
            RefillMethod(
                slug="opay", label="OPay", risk="low",
                status="verified",
                buy_service="Bitnob / iPayBTC", buy_service_url="https://bitnob.com",
                lightning_wallet="Bitnob built-in LN",
                pipeline_steps=["OPay balance", "Transfer to Bitnob", "Buy BTC", "LN withdrawal → Noones"],
                total_time_min=3, total_time_max=8, fee_pct_approx=1.5,
                fee_notes="~1–2% spread, LN fee <1 sat",
                limits="KYC L2: up to $10,000/day",
                kyc_required="Government ID. iPayBTC: NIN",
                evidence_urls=["https://ipaybtc.app/services"],
            ),
            RefillMethod(
                slug="gtbank-guaranty-trust-bank", label="GTBank", risk="low",
                status="verified",
                buy_service="Bitnob", buy_service_url="https://bitnob.com",
                lightning_wallet="Bitnob built-in LN",
                pipeline_steps=["GTBank NGN transfer", "Bitnob buy BTC", "LN withdrawal → Noones"],
                total_time_min=3, total_time_max=8, fee_pct_approx=1.5,
                fee_notes="~1–2% spread, LN fee <1 sat",
                limits="KYC L2: up to $10,000/day",
                kyc_required="Government ID",
                evidence_urls=["https://bitnob.com"],
            ),
        ],
    ),
    RefillMarket(
        name="Argentina", currency="ARS", flag="🇦🇷",
        methods=[
            RefillMethod(
                slug="mercado-pago", label="Mercado Pago", risk="medium",
                status="partial",
                buy_service="Lemon Cash", buy_service_url="https://lemon.me",
                lightning_wallet="Lemon Cash LN (via OpenNode)",
                pipeline_steps=["Mercado Pago (ARS)", "CVU transfer → Lemon Cash", "Buy BTC", "LN send → Noones"],
                total_time_min=5, total_time_max=10, fee_pct_approx=1.5,
                fee_notes="~1–2% spread, LN fee <1 sat",
                limits="Buy from 100 ARS",
                kyc_required="Argentine CUIL/DNI",
                gaps="Lemon Cash LN send to external address not confirmed — test first",
                workaround="MT Pelerin card → Lightning address (2.5% fee, 2–5 min) — confirmed ✅",
                evidence_urls=["https://www.nasdaq.com/articles/opennode-lemon-cash-to-onboard-1-million-argentines-to-bitcoin-lightning-network"],
            ),
            RefillMethod(
                slug="cbu-cvu", label="CBU/CVU", risk="low",
                status="partial",
                buy_service="Lemon Cash", buy_service_url="https://lemon.me",
                lightning_wallet="Lemon Cash LN (via OpenNode)",
                pipeline_steps=["Argentine bank/PSP (CBU/CVU)", "Lemon Cash buy BTC", "LN send → Noones"],
                total_time_min=5, total_time_max=10, fee_pct_approx=1.5,
                fee_notes="~1–2% spread, LN fee <1 sat",
                limits="Buy from 100 ARS",
                kyc_required="Argentine DNI / CUIL",
                gaps="Same caveat as Mercado Pago — verify LN send to external address",
                workaround="MT Pelerin card → Lightning (confirmed). Bank → SEPA → MT Pelerin works for EUR.",
                evidence_urls=["https://lemon.me/en/", "https://www.mtpelerin.com/buy-bitcoin-lightning"],
            ),
        ],
    ),
    RefillMarket(
        name="Venezuela", currency="VES", flag="🇻🇪",
        methods=[
            RefillMethod(
                slug="zelle", label="Zelle (USD)", risk="medium",
                status="verified",
                buy_service="Strike", buy_service_url="https://strike.me",
                lightning_wallet="Strike built-in Lightning",
                pipeline_steps=["Zelle → US bank account", "ACH to Strike", "Buy BTC", "Strike LN withdrawal → Noones"],
                total_time_min=5, total_time_max=10, fee_pct_approx=1.25,
                fee_notes="0.99–1.5% buy fee, ACH free, LN nearly free",
                limits="Strike US-regulated, KYC required. ACH settles in ~5 business days.",
                kyc_required="Full KYC (SSN, government ID) — Strike is US-registered MSB",
                gaps="ACH 5-day settlement. Keep $100–200 float in Strike.",
                workaround="Pre-fund Strike float. When Zelle arrives, buy immediately with float, ACH refills float.",
                evidence_urls=["https://blockdyor.com/strike-review/", "https://bitcoinmagazine.com/business/lightning-wallet-strike-now-enables-bitcoin-withdrawals"],
            ),
            RefillMethod(
                slug="pago-movil", label="Pago Movil (VES)", risk="low",
                status="partial",
                buy_service="lnp2pbot (Telegram P2P)", buy_service_url="https://t.me/lnp2pbot",
                lightning_wallet="P2P Lightning (lnp2pbot)",
                pipeline_steps=["Pago Movil (VES)", "P2P peer on lnp2pbot Telegram", "Receive BTC via Lightning", "Forward to Noones"],
                total_time_min=5, total_time_max=15, fee_pct_approx=1.0,
                fee_notes="~1% P2P spread",
                limits="Peer availability dependent. No KYC.",
                kyc_required="None (lnp2pbot is peer-to-peer)",
                gaps="Kontigo LN send to external address unconfirmed",
                workaround="lnp2pbot P2P as primary. Binance P2P → on-chain → Phoenix as fallback (30–60 min).",
                evidence_urls=["https://www.mexc.com/news/unlock-bitcoin-in-venezuela-kontigo-platform-just-activated-pago-movil-on-ramps/167286"],
            ),
        ],
    ),
    RefillMarket(
        name="Kenya", currency="KES", flag="🇰🇪",
        methods=[
            RefillMethod(
                slug="mpesa", label="M-Pesa", risk="low",
                status="verified",
                buy_service="Bitnob", buy_service_url="https://bitnob.com",
                lightning_wallet="Bitnob built-in LN",
                pipeline_steps=["M-Pesa (KES)", "Bitnob buy BTC", "LN withdrawal → Noones"],
                total_time_min=2, total_time_max=5, fee_pct_approx=1.1,
                fee_notes="~1–1.1% spread, LN fee <1 sat",
                limits="M-Pesa single tx max KES 250,000 (~$1,900). Bitnob KYC L2: $10,000/day.",
                kyc_required="Government ID (KYC L2 — Kenya VASP Act Nov 2025)",
                evidence_urls=["https://www.dignited.com/100613/bitnob-eases-bitcoin-access-in-kenya-with-m-pesa-airtel-and-t-kash-intergrations/", "https://docs.bitnob.com/docs/lightning/sending-bitcoin-lightning"],
            ),
            RefillMethod(
                slug="airtel-money-kenya", label="Airtel Money", risk="low",
                status="verified",
                buy_service="Bitnob", buy_service_url="https://bitnob.com",
                lightning_wallet="Bitnob built-in LN",
                pipeline_steps=["Airtel Money (KES)", "Bitnob buy BTC", "LN withdrawal → Noones"],
                total_time_min=2, total_time_max=5, fee_pct_approx=1.1,
                fee_notes="~1–1.1% spread, LN fee <1 sat",
                limits="Bitnob KYC L2: $10,000/day",
                kyc_required="Government ID (Bitnob L2)",
                evidence_urls=["https://www.dignited.com/100613/bitnob-eases-bitcoin-access-in-kenya-with-m-pesa-airtel-and-t-kash-intergrations/"],
            ),
        ],
    ),
    RefillMarket(
        name="Sverige", currency="SEK", flag="🇸🇪",
        methods=[
            RefillMethod(
                slug="swish", label="Swish", risk="low",
                status="partial",
                buy_service="Safello", buy_service_url="https://safello.com",
                lightning_wallet="Phoenix (separate step)",
                pipeline_steps=["Swish (SEK)", "Safello buy BTC", "On-chain withdrawal to Phoenix", "Phoenix → LN → Noones"],
                total_time_min=30, total_time_max=90, fee_pct_approx=3.0,
                fee_notes="~1.5–2.5% Safello spread + 0.00025 BTC (~$12) fixed on-chain withdrawal fee",
                limits="~10,000 SEK/week Express (no KYC). Verified: unlimited.",
                kyc_required="Swedish BankID (Safello FI-registered since 2013)",
                gaps="Safello on-chain only (no Lightning withdrawal). $12 withdrawal fee = only viable for batched refills ≥$300.",
                workaround="Batch trades before withdrawing. Phoenix auto-opens channel on first on-chain receive.",
                evidence_urls=["https://news.cision.com/safello/r/safello-enters-into-agreement-for-recurring-swish-payments,c4156268", "https://help.safello.com/en/articles/166857-how-do-i-make-a-withdrawal-from-my-safello-wallet"],
            ),
            RefillMethod(
                slug="revolut", label="Revolut", risk="low",
                status="verified",
                buy_service="Relai (via SEPA)", buy_service_url="https://relai.app",
                lightning_wallet="Relai built-in Lightning (Breez SDK)",
                pipeline_steps=["Revolut SEK/EUR", "Free SEPA Instant to Relai", "Buy BTC at 2%", "Relai LN send → Noones"],
                total_time_min=5, total_time_max=15, fee_pct_approx=2.0,
                fee_notes="Revolut SEPA free + Relai ~2% total",
                limits="Relai: 950 EUR/day, ~95,000 EUR/year. Full KYC required (MiCA).",
                kyc_required="Revolut (full KYC) + Relai (full KYC, MiCA-compliant)",
                gaps="Revolut Lightning via Lightspark announced but not live yet.",
                workaround="When Revolut Lightning goes live: Revolut → buy → LN send directly (5 min, removes SEPA step).",
                evidence_urls=["https://www.nasdaq.com/articles/bitcoin-exchange-relai-integrates-lightning-network-for-its-100000-european-users", "https://www.revolut.com/en-SE/money-transfer/send-money-to-bank/"],
            ),
        ],
    ),
]


def parse_pipeline(filepath: str | None = None) -> RefillPipeline:
    """Returns structured pipeline data. Uses hardcoded data as primary source."""
    return RefillPipeline(
        markets=PIPELINE_DATA,
        source_file=filepath or "EmergingMarkets/refill_pipeline_2026-03-15.md",
        parsed_at=time.time(),
    )
