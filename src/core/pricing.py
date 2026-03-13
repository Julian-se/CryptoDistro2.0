"""
Pricing — spread calculation, fee estimation, net profit computation.
"""

from decimal import Decimal

from src.core.config import get_config


def calculate_spread(buy_price: Decimal, sell_price: Decimal) -> Decimal:
    """Calculate spread as percentage: (sell - buy) / buy * 100."""
    if buy_price <= 0:
        return Decimal("0")
    return ((sell_price - buy_price) / buy_price) * 100


def estimate_fees(trade_amount_usd: Decimal, transfer_method: str = "lightning") -> Decimal:
    """Estimate total fees for one arbitrage cycle in USD."""
    cfg = get_config()["fees"]

    # Trading fees (buy + sell sides)
    binance_fee = trade_amount_usd * Decimal(str(cfg["binance_trading_pct"])) / 100
    noones_fee = trade_amount_usd * Decimal(str(cfg["noones_fee_pct"])) / 100

    # Transfer fee
    if transfer_method == "lightning":
        # Lightning fees are negligible (a few sats)
        transfer_fee = Decimal("0.01")
    elif transfer_method == "onchain":
        transfer_fee = Decimal(str(cfg["onchain_fee_usd"]))
    elif transfer_method == "trc20":
        transfer_fee = Decimal(str(cfg["usdt_trc20_fee_usd"]))
    else:
        transfer_fee = Decimal("0")

    return binance_fee + noones_fee + transfer_fee


def net_profit(
    buy_price: Decimal,
    sell_price: Decimal,
    quantity: Decimal,
    transfer_method: str = "lightning",
) -> dict:
    """Calculate net profit for an arbitrage trade."""
    trade_amount = quantity * buy_price
    gross = (sell_price - buy_price) * quantity
    fees = estimate_fees(trade_amount, transfer_method)
    net = gross - fees

    return {
        "gross_profit_usd": gross,
        "fees_usd": fees,
        "net_profit_usd": net,
        "spread_pct": calculate_spread(buy_price, sell_price),
        "net_spread_pct": calculate_spread(buy_price, sell_price) - (fees / trade_amount * 100) if trade_amount > 0 else Decimal("0"),
        "roi_pct": (net / trade_amount * 100) if trade_amount > 0 else Decimal("0"),
    }
