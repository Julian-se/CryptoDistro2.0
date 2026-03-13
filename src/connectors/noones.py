"""
Noones connector — P2P offer browsing, price checking, trade management.

Noones API inherits the Paxful v1 architecture:
- Auth: OAuth2 client_credentials flow (token from auth.noones.com)
- Endpoints: POST to /noones/v1/<resource>/<action>
- All requests require auth, even public offer browsing

Lager 1 automation: scanning offers is pure data work, automate fully.
Lager 3: trade initiation stays human-in-the-loop (motpartsbedömning).

Docs: https://dev.noones.com/documentation/noones-api
"""

import logging
import time
from decimal import Decimal

import httpx

from src.core.config import get_config

logger = logging.getLogger(__name__)


class NoonesConnector:
    """Wrapper around Noones (ex-Paxful) API."""

    def __init__(self):
        cfg = get_config()["noones"]
        self.api_key = cfg["api_key"]
        self.api_secret = cfg["api_secret"]
        self.auth_url = cfg.get("auth_url", "https://auth.noones.com/oauth2/token")
        self.api_url = cfg.get("api_url", "https://api.noones.com").rstrip("/")
        self._token: str | None = None
        self._token_expires: float = 0
        self._client = httpx.Client(timeout=30)
        logger.info("Noones connector initialized")

    # --- Authentication (OAuth2 client_credentials) ---

    def _get_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        if self._token and time.time() < self._token_expires:
            return self._token

        resp = self._client.post(
            self.auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expires = time.time() + data.get("expires_in", 3600) - 60
        logger.debug("Noones OAuth2 token refreshed")
        return self._token

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json; version=1",
        }

    def _post(self, endpoint: str, payload: dict | None = None) -> dict:
        """
        All Noones API calls are POST requests.
        Endpoint format: /noones/v1/<resource>/<action>
        """
        url = f"{self.api_url}/noones/v1/{endpoint}"
        resp = self._client.post(
            url,
            data=payload or {},
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        result = resp.json()

        if result.get("status") == "error":
            error = result.get("error", {})
            logger.error(f"Noones API error on {endpoint}: {error}")
            raise RuntimeError(f"Noones API error: {error.get('message', 'Unknown')}")

        return result

    # --- Offer Browsing (Lager 1 — fully automated scanning) ---

    def get_offers(
        self,
        offer_type: str = "sell",
        currency_code: str = "USD",
        crypto_currency_code: str = "BTC",
        payment_method: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        Search all marketplace offers.
        offer_type: "sell" (we buy from sellers) or "buy" (we sell to buyers)
        """
        payload = {
            "offer_type": offer_type,
            "currency_code": currency_code,
            "crypto_currency_code": crypto_currency_code,
            "limit": limit,
            "offset": offset,
        }
        if payment_method:
            payload["payment_method"] = payment_method

        try:
            result = self._post("offer/all", payload)
            offers = result.get("data", {}).get("offers", [])
            return self._parse_offers(offers)
        except Exception as e:
            logger.error(f"Failed to fetch Noones offers: {e}")
            return []

    def get_offer_prices(self, payment_method: str | None = None) -> dict:
        """Get offer prices, optionally filtered by payment method."""
        payload = {}
        if payment_method:
            payload["payment_method"] = payment_method
        try:
            result = self._post("offer/prices", payload)
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch offer prices: {e}")
            return {}

    def get_offer(self, offer_hash: str) -> dict:
        """Get details of a specific offer."""
        try:
            result = self._post("offer/get", {"offer_hash": offer_hash})
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch offer {offer_hash}: {e}")
            return {}

    def _parse_offers(self, raw_offers: list) -> list[dict]:
        """Parse raw API offers into clean dicts."""
        parsed = []
        for offer in raw_offers:
            try:
                parsed.append({
                    "offer_hash": offer.get("offer_hash", ""),
                    "offer_id": offer.get("offer_hash", ""),  # Alias for compatibility
                    "seller": offer.get("username", ""),
                    "price": Decimal(str(offer.get("fiat_price_per_btc", "0"))),
                    "min_amount": Decimal(str(offer.get("fiat_amount_range_min", "0"))),
                    "max_amount": Decimal(str(offer.get("fiat_amount_range_max", "0"))),
                    "currency": offer.get("currency_code", ""),
                    "crypto": offer.get("crypto_currency_code", "BTC"),
                    "payment_method": offer.get("payment_method_name", ""),
                    "payment_method_slug": offer.get("payment_method_slug", ""),
                    "seller_score": offer.get("score", 0),
                    "seller_trades": offer.get("trade_count", 0),
                    "last_seen": offer.get("last_seen_at", ""),
                    "margin": offer.get("margin", 0),
                })
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping malformed offer: {e}")
        return parsed

    # --- Currency & Rates ---

    def get_currency_rates(self) -> dict:
        """Get current currency/BTC exchange rates."""
        try:
            result = self._post("currency/rates")
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch currency rates: {e}")
            return {}

    def get_btc_price(self) -> Decimal:
        """Get current BTC price in USD from Noones."""
        try:
            result = self._post("currency/btc")
            price = result.get("data", {}).get("price", "0")
            return Decimal(str(price))
        except Exception as e:
            logger.error(f"Failed to fetch BTC price: {e}")
            return Decimal("0")

    # --- Price Helpers ---

    def get_best_buy_price(self, currency: str = "USD", crypto: str = "BTC") -> Decimal | None:
        """Get cheapest available price to buy crypto on Noones."""
        offers = self.get_offers(
            offer_type="sell",  # We look at sellers to buy from them
            currency_code=currency,
            crypto_currency_code=crypto,
            limit=5,
        )
        if not offers:
            return None
        return min(o["price"] for o in offers if o["price"] > 0)

    def get_best_sell_price(self, currency: str = "USD", crypto: str = "BTC") -> Decimal | None:
        """Get best price to sell crypto on Noones (highest buyer offer)."""
        offers = self.get_offers(
            offer_type="buy",  # We look at buyers to sell to them
            currency_code=currency,
            crypto_currency_code=crypto,
            limit=5,
        )
        if not offers:
            return None
        return max(o["price"] for o in offers if o["price"] > 0)

    # --- Account ---

    def get_profile(self) -> dict:
        """Get your Noones profile info."""
        try:
            result = self._post("user/me")
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch profile: {e}")
            return {}

    # --- Trade Management ---

    def get_active_trades(self) -> list[dict]:
        """Get all currently active trades."""
        try:
            result = self._post("trade/list")
            return result.get("data", {}).get("trades", [])
        except Exception as e:
            logger.error(f"Failed to fetch active trades: {e}")
            return []

    def get_trade(self, trade_hash: str) -> dict:
        """Get info on a specific trade."""
        try:
            result = self._post("trade/get", {"trade_hash": trade_hash})
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch trade {trade_hash}: {e}")
            return {}

    def get_completed_trades(self, page: int = 1) -> list[dict]:
        """Get completed trade history."""
        try:
            result = self._post("trade/completed", {"page": page})
            return result.get("data", {}).get("trades", [])
        except Exception as e:
            logger.error(f"Failed to fetch completed trades: {e}")
            return []

    # --- Offer Management (for selling on Noones — reverse arb) ---

    def create_offer(
        self,
        offer_type: str,
        currency: str,
        margin: float,
        range_min: float,
        range_max: float,
        payment_method: str,
        crypto: str = "BTC",
        payment_window: int = 30,
        offer_terms: str = "",
    ) -> dict:
        """Create a buy or sell offer on Noones."""
        try:
            result = self._post("offer/create", {
                "offer_type_field": offer_type,
                "currency": currency,
                "crypto_currency_code": crypto,
                "payment_method": payment_method,
                "margin": margin,
                "range_min": range_min,
                "range_max": range_max,
                "payment_window": payment_window,
                "offer_terms": offer_terms,
            })
            offer_hash = result.get("data", {}).get("offer_hash", "")
            logger.info(f"Created {offer_type} offer {offer_hash} at {margin}% margin")
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to create offer: {e}")
            return {}

    def deactivate_offer(self, offer_hash: str) -> bool:
        """Deactivate an offer."""
        try:
            self._post("offer/deactivate", {"offer_hash": offer_hash})
            return True
        except Exception:
            return False

    # --- Payment Methods ---

    def get_payment_methods(self) -> list[dict]:
        """List available payment methods."""
        try:
            result = self._post("payment-method/list")
            return result.get("data", [])
        except Exception as e:
            logger.error(f"Failed to fetch payment methods: {e}")
            return []

    # --- Wallet Balance ---

    def get_balance(self) -> dict:
        """
        Get wallet balances from user/me profile.
        The Noones API does not expose a dedicated wallet/balance endpoint.
        Wallet balances are embedded in the user profile under total_btc, total_usdt, etc.
        Note: user/me requires JSON body (not form-encoded) — use direct httpx call.
        Returns: {"btc": Decimal, "usdt": Decimal}
        """
        try:
            url = f"{self.api_url}/noones/v1/user/me"
            resp = self._client.post(
                url,
                json={},
                headers={**self._auth_headers(), "Content-Type": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            btc = Decimal(str(data.get("total_btc") or "0"))
            usdt = Decimal(str(data.get("total_usdt") or "0"))
            return {"btc": btc, "usdt": usdt}
        except Exception as e:
            logger.error(f"Failed to fetch Noones balance: {e}")
            return {"btc": Decimal("0"), "usdt": Decimal("0")}

    # --- Swap API (crypto-to-crypto conversion) ---

    def get_swap_rates(self, convert_from: str = "BTC", convert_to: str = "USDT") -> dict:
        """Get conversion quotes between crypto pairs."""
        try:
            result = self._post("wallet/conversion-quotes", {
                "convert_from": convert_from,
                "convert_to": convert_to,
            })
            return result.get("data", {})
        except Exception as e:
            logger.error(f"Failed to fetch swap rates: {e}")
            return {}

    def close(self):
        """Close the HTTP client."""
        self._client.close()
