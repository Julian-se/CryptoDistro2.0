"""
Trade sync — pulls completed trades from Noones and upserts into TradeTracker.

Profit calculation:
  You sell crypto (USDT/BTC) for local fiat (SEK, NGN, etc.) at a premium.
  profit_usd = (fiat_received / fx_spot_rate) - crypto_cost_usd
  For USDT: crypto_cost_usd ≈ crypto_amount (1:1)
  For BTC:  crypto_cost_usd = crypto_amount × btc_spot_usd

Fees:
  Noones charges the seller a fee in crypto. This is already deducted from
  the crypto_amount the buyer receives, but we track it separately.
"""

import logging
import time
from datetime import datetime, timezone

from src.connectors.fxrates import FxRatesConnector
from src.connectors.noones import NoonesConnector
from src.core.trade_tracker import TradeTracker

logger = logging.getLogger(__name__)


def _parse_timestamp(ts_str: str | None) -> float | None:
    """Parse Noones timestamp string to epoch float."""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except (ValueError, AttributeError):
        try:
            return float(ts_str)
        except (ValueError, TypeError):
            return None


def sync_completed_trades(
    noones: NoonesConnector,
    tracker: TradeTracker,
    fx: FxRatesConnector | None = None,
    btc_spot_usd: float = 0.0,
    pages: int = 3,
    fetch_details: bool = True,
) -> dict:
    """
    Pull completed trades from Noones and upsert into the database.

    Step 1: Fetch trade list (has basic data but no paid_at / fee)
    Step 2: For new trades, fetch individual trade detail (has paid_at, fees, margin)
    Step 3: Calculate profit using FX rates
    """
    new_count = 0
    updated_count = 0
    errors = 0
    all_trades = []

    for page in range(1, pages + 1):
        try:
            raw_trades = noones.get_completed_trades(page=page)
            if not raw_trades:
                break
            all_trades.extend(raw_trades)
        except Exception as e:
            logger.error(f"Failed to fetch trades page {page}: {e}")
            errors += 1
            break

    for raw in all_trades:
        try:
            trade_hash = raw.get("trade_hash")
            if not trade_hash:
                continue

            # Check if we already have this trade with full detail
            existing = tracker.conn.execute(
                "SELECT id, paid_at FROM p2p_trades WHERE trade_hash = ?", (trade_hash,)
            ).fetchone()

            # If trade exists and already has paid_at AND fee, it has full detail — skip
            if existing and existing["paid_at"]:
                existing_fee = tracker.conn.execute(
                    "SELECT fee_usd FROM p2p_trades WHERE trade_hash = ?", (trade_hash,)
                ).fetchone()
                if existing_fee and (existing_fee["fee_usd"] or 0) > 0:
                    updated_count += 1
                    continue
                # Has paid_at but missing fee — fall through to detail fetch

            # For new trades or trades missing detail, fetch individual detail
            detail_data = raw
            if fetch_details:
                try:
                    detail = noones.get_trade(trade_hash)
                    trade_detail = detail.get("trade", detail)
                    if trade_detail and "crypto_amount_total" in trade_detail:
                        detail_data = trade_detail
                except Exception as e:
                    logger.debug(f"Could not fetch detail for {trade_hash}: {e}")

            trade = _map_noones_trade(detail_data, fx=fx, btc_spot_usd=btc_spot_usd)
            if trade:
                is_new = tracker.upsert_p2p_trade(trade)
                if is_new:
                    new_count += 1
                else:
                    updated_count += 1
        except Exception as e:
            logger.warning(f"Failed to map trade {raw.get('trade_hash', '?')}: {e}")
            errors += 1

    summary = {
        "synced_at": time.time(),
        "fetched": len(all_trades),
        "new": new_count,
        "updated": updated_count,
        "errors": errors,
    }
    logger.info(
        f"Trade sync: {new_count} new, {updated_count} updated, "
        f"{errors} errors out of {len(all_trades)} fetched"
    )
    return summary


# Noones stores crypto amounts as integers:
#   USDT: divide by 10^6 (6 decimal places)
#   BTC:  divide by 10^8 (satoshis)
_CRYPTO_DIVISORS = {"USDT": 1_000_000, "BTC": 100_000_000}


def _to_crypto_float(raw_amount, asset: str) -> float:
    """Convert Noones integer crypto amount to float."""
    amount = float(raw_amount or 0)
    if amount > 1000:  # Clearly in micro-units
        divisor = _CRYPTO_DIVISORS.get(asset, 1_000_000)
        return amount / divisor
    return amount  # Already a float


def _map_from_list(
    raw: dict,
    fx: FxRatesConnector | None = None,
    btc_spot_usd: float = 0.0,
) -> dict | None:
    """Light mapping from the trade list endpoint (no detail fields)."""
    trade_hash = raw.get("trade_hash")
    if not trade_hash:
        return None

    asset = raw.get("crypto_currency_code") or "USDT"
    fiat_amount = float(raw.get("fiat_amount_requested") or 0)
    fiat_currency = raw.get("fiat_currency_code") or ""
    crypto_amount = _to_crypto_float(raw.get("crypto_amount_requested"), asset)

    status = _normalize_status(raw.get("trade_status") or raw.get("status", ""))

    fiat_rate = fiat_amount / crypto_amount if crypto_amount > 0 else 0
    profit_usd, fee_usd = _calc_profit(
        fiat_amount, fiat_currency, crypto_amount, asset, 0, fx, btc_spot_usd
    )

    return {
        "trade_hash": trade_hash,
        "status": status,
        "trade_type": "sell",
        "asset": asset,
        "fiat_amount": fiat_amount,
        "fiat_currency": fiat_currency,
        "crypto_amount": round(crypto_amount, 6),
        "fiat_rate": round(fiat_rate, 4),
        "counterparty": raw.get("buyer") or raw.get("buyer_name"),
        "payment_method": raw.get("payment_method_name") or "",
        "opened_at": _parse_timestamp(raw.get("started_at")) or time.time(),
        "paid_at": None,  # Not available in list
        "released_at": None,
        "completed_at": _parse_timestamp(raw.get("completed_at") or raw.get("ended_at")),
        "profit_usd": profit_usd,
        "fee_usd": fee_usd,
        "offer_hash": raw.get("offer_hash"),
    }


def _map_noones_trade(
    raw: dict,
    fx: FxRatesConnector | None = None,
    btc_spot_usd: float = 0.0,
) -> dict | None:
    """
    Full mapping from trade detail endpoint.

    Noones trade detail fields:
      crypto_amount_requested  — net crypto buyer receives (integer, ÷10^6 for USDT)
      crypto_amount_total      — gross crypto including fee (integer)
      fee_crypto_amount        — platform fee in crypto (integer)
      seller_fee_percentage    — fee % (e.g. "1.00")
      margin                   — offer margin % (e.g. "15.00")
      fiat_price_per_crypto    — rate used (e.g. "10.769700")
      paid_at                  — buyer marked as paid
      escrow_funded_at         — escrow locked
      completed_at / ended_at  — trade finished
      buyer_name / seller_name — usernames
    """
    trade_hash = raw.get("trade_hash")
    if not trade_hash:
        return None

    asset = raw.get("crypto_currency_code") or "USDT"
    fiat_amount = float(raw.get("fiat_amount_requested") or 0)
    fiat_currency = raw.get("fiat_currency_code") or ""

    # Gross crypto (what you put in escrow, including fee)
    crypto_total = _to_crypto_float(raw.get("crypto_amount_total"), asset)
    # Net crypto (what buyer receives)
    crypto_net = _to_crypto_float(raw.get("crypto_amount_requested"), asset)
    # Fee in crypto
    fee_crypto = _to_crypto_float(
        raw.get("seller_fee_crypto_amount") or raw.get("fee_crypto_amount"), asset
    )

    # Use total as the amount you spent from your wallet
    crypto_amount = crypto_total if crypto_total > 0 else crypto_net

    status = _normalize_status(raw.get("trade_status") or raw.get("status", ""))

    # Counterparty — buyer in a sell trade
    counterparty = raw.get("buyer_name") or raw.get("buyer") or ""

    payment_method = raw.get("payment_method_name") or raw.get("payment_method_slug") or ""

    # Use the rate from the API if available
    fiat_rate = float(raw.get("fiat_price_per_crypto") or 0)
    if fiat_rate == 0 and crypto_net > 0:
        fiat_rate = fiat_amount / crypto_net

    # Timestamps
    opened_at = _parse_timestamp(
        raw.get("escrow_funded_at") or raw.get("started_at")
    ) or time.time()
    paid_at = _parse_timestamp(raw.get("paid_at"))
    completed_at = _parse_timestamp(
        raw.get("completed_at") or raw.get("ended_at")
    )

    # Calculate profit and fee in USD
    profit_usd, fee_usd = _calc_profit(
        fiat_amount, fiat_currency, crypto_total, asset, fee_crypto, fx, btc_spot_usd
    )

    return {
        "trade_hash": trade_hash,
        "status": status,
        "trade_type": "sell",
        "asset": asset,
        "fiat_amount": fiat_amount,
        "fiat_currency": fiat_currency,
        "crypto_amount": round(crypto_amount, 6),
        "fiat_rate": round(fiat_rate, 4),
        "counterparty": counterparty,
        "payment_method": payment_method,
        "opened_at": opened_at,
        "paid_at": paid_at,
        "released_at": completed_at,  # Released ≈ completed for successful trades
        "completed_at": completed_at,
        "profit_usd": profit_usd,
        "fee_usd": fee_usd,
        "offer_hash": raw.get("offer_hash"),
    }


def _normalize_status(status: str) -> str:
    s = status.lower()
    if "success" in s or "release" in s or "completed" in s:
        return "completed"
    if "cancel" in s or "expired" in s:
        return "cancelled"
    if "paid" in s:
        return "paid"
    return s or "unknown"


def _calc_profit(
    fiat_amount: float,
    fiat_currency: str,
    crypto_amount: float,
    asset: str,
    fee_crypto: float,
    fx: FxRatesConnector | None,
    btc_spot_usd: float,
) -> tuple[float, float]:
    """
    Calculate profit and fee in USD.

    profit = (fiat_received in USD) - (crypto_spent in USD)
    fee    = fee_crypto converted to USD
    """
    # Fee in USD
    fee_usd = 0.0
    if fee_crypto > 0:
        if asset == "USDT":
            fee_usd = fee_crypto
        elif asset == "BTC" and btc_spot_usd > 0:
            fee_usd = fee_crypto * btc_spot_usd

    # Fiat received in USD
    fiat_usd = 0.0
    if fx and fiat_currency:
        try:
            fiat_usd = fx.local_to_usd(fiat_amount, fiat_currency)
        except Exception:
            pass

    # Crypto cost in USD (what you spent from your wallet)
    crypto_usd = 0.0
    if asset == "USDT":
        crypto_usd = crypto_amount
    elif asset == "BTC" and btc_spot_usd > 0:
        crypto_usd = crypto_amount * btc_spot_usd

    if fiat_usd > 0 and crypto_usd > 0:
        profit_usd = fiat_usd - crypto_usd
    else:
        profit_usd = 0.0

    return round(profit_usd, 4), round(fee_usd, 4)
