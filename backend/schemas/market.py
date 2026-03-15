from pydantic import BaseModel
from typing import Optional
from .dashboard import MarketSummary


class PremiumPoint(BaseModel):
    timestamp: float
    premium_pct: float
    btc_spot: float
    action: str
    offer_count: int


class CompetitorOffer(BaseModel):
    seller: str
    price: float
    margin: Optional[float] = None
    trades: int
    score: float
    method: str
    min_amount: float
    max_amount: float
    platform: str


class MarketDetail(BaseModel):
    market: MarketSummary
    competitors: dict[str, list[CompetitorOffer]]
    premium_history: list[PremiumPoint]
