from pydantic import BaseModel
from typing import Optional


class InventorySignal(BaseModel):
    predicted_hours_to_empty: float = 99.0
    refill_needed: bool = False
    confidence: float = 0.0
    recommended_refill_usd: float = 0.0
    consumption_rate_btc_per_hour: float = 0.0


class SpreadSignal(BaseModel):
    recommended_margins: dict[str, float] = {}
    market_premiums: dict[str, float] = {}
    calibration_notes: dict[str, str] = {}


class VelocitySignal(BaseModel):
    recommended_hours: dict[str, int] = {}
    market_priority: list[str] = []
    revenue_per_hour: dict[str, float] = {}
    capital_constraint_note: str = ""


class ControllerSignals(BaseModel):
    inventory: InventorySignal = InventorySignal()
    spread: SpreadSignal = SpreadSignal()
    velocity: VelocitySignal = VelocitySignal()
    last_run_at: float = 0.0


class PaymentMethod(BaseModel):
    slug: str
    label: str
    risk: str = "low"


class MarketSummary(BaseModel):
    name: str
    flag: str
    currency: str
    premium_pct: float
    action: str  # ACT_NOW | WATCH | AVOID | DATA_ISSUE
    suggested_margin: float
    offer_count: int
    payment_methods: list[PaymentMethod]
    fx_rate: float
    refill_status: str  # verified | partial | unverified
    scanned_at: float = 0.0


class PlatformBalance(BaseModel):
    platform: str
    btc: float
    usdt: float
    total_usd: float
    updated_at: float = 0.0


class ActiveTrade(BaseModel):
    cycle_id: str
    started_at: float
    status: str
    buy_platform: str
    sell_platform: str
    asset: str
    notes: Optional[str] = None


class DashboardSnapshot(BaseModel):
    btc_spot_usd: float
    markets: list[MarketSummary]
    balances: dict[str, PlatformBalance]
    active_trades: list[ActiveTrade]
    open_cycles: int
    controller_signals: ControllerSignals
    scanned_at: float
