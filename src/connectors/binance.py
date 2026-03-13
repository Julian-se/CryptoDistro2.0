"""
Binance connector — spot prices, order placement, balance checks.
Uses the official binance-connector-python SDK.

Lager 2 automation: exchange-side execution is fully automatable.
When BTC arrives, auto-sell at market or limit price.

SDK: https://github.com/binance/binance-connector-python
"""

import logging
from decimal import Decimal

import httpx
from binance.spot import Spot
from binance.error import ClientError, ServerError

from src.core.config import get_config

# Binance P2P is a separate product — different base URL, no SDK, no auth required
BINANCE_P2P_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

logger = logging.getLogger(__name__)

# Binance testnet base URL
TESTNET_URL = "https://testnet.binance.vision"


class BinanceConnector:
    """Wrapper around Binance spot API using official SDK."""

    def __init__(self):
        cfg = get_config()["binance"]
        self.testnet = cfg.get("testnet", True)
        base_url = TESTNET_URL if self.testnet else "https://api.binance.com"

        self.client = Spot(
            api_key=cfg["api_key"],
            api_secret=cfg["api_secret"],
            base_url=base_url,
        )

        mode = "TESTNET" if self.testnet else "LIVE"
        logger.info(f"Binance connector initialized ({mode})")

        # Separate client for P2P — always hits live endpoint regardless of testnet flag
        self._p2p_client = httpx.Client(
            timeout=15,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
        )

    # --- Price Data ---

    def get_spot_price(self, symbol: str = "BTCUSDT") -> Decimal:
        """Get current spot price for a trading pair."""
        ticker = self.client.ticker_price(symbol=symbol)
        return Decimal(ticker["price"])

    def get_orderbook_top(self, symbol: str = "BTCUSDT") -> dict:
        """Get best bid/ask from orderbook."""
        book = self.client.depth(symbol=symbol, limit=5)
        best_bid = Decimal(book["bids"][0][0])
        best_ask = Decimal(book["asks"][0][0])
        return {
            "best_bid": best_bid,
            "best_bid_qty": Decimal(book["bids"][0][1]),
            "best_ask": best_ask,
            "best_ask_qty": Decimal(book["asks"][0][1]),
            "spread_pct": (best_ask - best_bid) / best_bid * 100,
        }

    # --- Account & Balances ---

    def get_balance(self, asset: str = "BTC") -> dict:
        """Get balance for a specific asset."""
        account = self.client.account()
        for b in account["balances"]:
            if b["asset"] == asset:
                free = Decimal(b["free"])
                locked = Decimal(b["locked"])
                return {
                    "asset": asset,
                    "free": free,
                    "locked": locked,
                    "total": free + locked,
                }
        return {"asset": asset, "free": Decimal("0"), "locked": Decimal("0"), "total": Decimal("0")}

    def get_all_balances(self) -> list[dict]:
        """Get all non-zero balances."""
        account = self.client.account()
        balances = []
        for b in account["balances"]:
            free = Decimal(b["free"])
            locked = Decimal(b["locked"])
            total = free + locked
            if total > 0:
                balances.append({
                    "asset": b["asset"],
                    "free": free,
                    "locked": locked,
                    "total": total,
                })
        return balances

    # --- Order Placement ---

    def market_sell(self, symbol: str, quantity: str) -> dict:
        """Place a market sell order. Used when BTC arrives from P2P transfer."""
        try:
            order = self.client.new_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity,
            )
            logger.info(f"Market sell executed: {quantity} {symbol} — order ID {order['orderId']}")
            return {
                "order_id": order["orderId"],
                "status": order["status"],
                "filled_qty": order["executedQty"],
                "price": order.get("fills", [{}])[0].get("price", "0") if order.get("fills") else "0",
                "raw": order,
            }
        except (ClientError, ServerError) as e:
            logger.error(f"Market sell failed: {e}")
            raise

    def limit_sell(self, symbol: str, quantity: str, price: str) -> dict:
        """Place a limit sell order slightly below best ask for fast fill."""
        try:
            order = self.client.new_order(
                symbol=symbol,
                side="SELL",
                type="LIMIT",
                quantity=quantity,
                price=price,
                timeInForce="GTC",
            )
            logger.info(f"Limit sell placed: {quantity} {symbol} @ {price} — order ID {order['orderId']}")
            return {
                "order_id": order["orderId"],
                "status": order["status"],
                "price": price,
                "raw": order,
            }
        except (ClientError, ServerError) as e:
            logger.error(f"Limit sell failed: {e}")
            raise

    def market_buy(self, symbol: str, quantity: str) -> dict:
        """Place a market buy order."""
        try:
            order = self.client.new_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity,
            )
            logger.info(f"Market buy executed: {quantity} {symbol} — order ID {order['orderId']}")
            return {
                "order_id": order["orderId"],
                "status": order["status"],
                "filled_qty": order["executedQty"],
                "price": order.get("fills", [{}])[0].get("price", "0") if order.get("fills") else "0",
                "raw": order,
            }
        except (ClientError, ServerError) as e:
            logger.error(f"Market buy failed: {e}")
            raise

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """Check status of an existing order."""
        order = self.client.get_order(symbol=symbol, orderId=order_id)
        return {
            "order_id": order["orderId"],
            "status": order["status"],
            "filled_qty": order["executedQty"],
            "price": order["price"],
        }

    # --- Deposit/Withdrawal Info ---

    def get_deposit_address(self, coin: str = "BTC", network: str = "BTC") -> str:
        """Get deposit address for receiving crypto."""
        result = self.client.deposit_address(coin=coin, network=network)
        return result["address"]

    def withdraw(self, coin: str, address: str, amount: str, network: str = "BTC") -> dict:
        """Withdraw crypto to external address. USE WITH CAUTION."""
        try:
            result = self.client.withdraw(
                coin=coin,
                address=address,
                amount=amount,
                network=network,
            )
            logger.info(f"Withdrawal initiated: {amount} {coin} to {address[:12]}... — ID {result['id']}")
            return result
        except (ClientError, ServerError) as e:
            logger.error(f"Withdrawal failed: {e}")
            raise

    # --- Binance P2P (C2C marketplace — separate from spot, no auth needed) ---

    def get_p2p_offers(
        self,
        fiat: str = "NGN",
        asset: str = "BTC",
        trade_type: str = "SELL",  # SELL = we can buy from these people
        rows: int = 20,
        page: int = 1,
    ) -> list[dict]:
        """
        Fetch live P2P offers from Binance C2C marketplace.

        trade_type="SELL" means sellers listing BTC — the people we'd buy from,
        or competitors if we're also selling in this market.
        trade_type="BUY" means buyers posting want-to-buy ads.

        Returns normalized offer dicts matching Noones format for easy comparison.
        """
        payload = {
            "page": page,
            "rows": rows,
            "payTypes": [],
            "asset": asset.upper(),
            "tradeType": trade_type.upper(),
            "fiat": fiat.upper(),
            "publisherType": None,
            "merchantCheck": False,
        }
        try:
            resp = self._p2p_client.post(BINANCE_P2P_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") != "000000":
                logger.warning(f"Binance P2P API non-zero code: {data.get('code')}")
                return []
            return self._parse_p2p_offers(data.get("data", []), fiat)
        except Exception as e:
            logger.error(f"Binance P2P fetch failed ({fiat}): {e}")
            return []

    def _parse_p2p_offers(self, raw: list, fiat: str) -> list[dict]:
        """Normalize Binance P2P response into the same shape as Noones offers."""
        parsed = []
        for item in raw:
            adv = item.get("adv", {})
            advertiser = item.get("advertiser", {})
            try:
                total_trades = advertiser.get("totalTradeCount", 0)
                month_trades = advertiser.get("monthOrderCount", 0)
                positive_rate = advertiser.get("positiveRate", 0)
                finish_rate = advertiser.get("monthFinishRate", 0)
                # Convert 0.97 → 97 to match Noones score scale (0–100)
                score = round(positive_rate * 100)

                parsed.append({
                    "platform": "Binance P2P",
                    "seller": advertiser.get("nickName", "?"),
                    "price": Decimal(str(adv.get("price", "0"))),
                    "min_amount": Decimal(str(adv.get("minSingleTransAmount", "0"))),
                    "max_amount": Decimal(str(adv.get("maxSingleTransAmount", "0"))),
                    "currency": fiat,
                    "crypto": adv.get("asset", "BTC"),
                    "payment_method": ", ".join(
                        pm.get("tradeMethodName", "") for pm in adv.get("tradeMethods", [])
                    ),
                    "seller_score": score,
                    "seller_trades": total_trades,
                    "month_trades": month_trades,
                    "finish_rate": round(finish_rate * 100),
                    "is_merchant": advertiser.get("userType") == "merchant",
                    "is_online": advertiser.get("isOnline", False),
                    "margin": None,  # Binance P2P doesn't expose margin directly
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed Binance P2P offer: {e}")
        return parsed

    def close(self):
        self._p2p_client.close()
