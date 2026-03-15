from pydantic import BaseModel
from typing import Optional


class SimParams(BaseModel):
    scenario: str  # conservative | realistic | optimistic | custom
    spread_pct: float
    fiat_minutes: float
    active_hours: float
    days: int = 30
    runs: int = 10
    market: Optional[str] = None


class SimResult(BaseModel):
    capital: list[int]
    profit: list[int]
    volume: list[int]
    p10: list[int]
    p90: list[int]
    smoothed_capital: list[int]


class MilestonePoint(BaseModel):
    day: int
    capital: int
    profit: int
    volume_day: int
    capital_pct_change: float


class SimStats(BaseModel):
    cycles_per_day_ln: int
    cycles_per_day_oc: int
    velocity_multiplier: float
    profit_per_cycle: float
    monthly_volume_ln: int
    monthly_volume_oc: int
    monthly_net_profit_mean: int
    monthly_net_profit_p10: int
    monthly_net_profit_p90: int


class SimulationResult(BaseModel):
    params: SimParams
    lightning: SimResult
    onchain: SimResult
    milestones: dict[str, MilestonePoint]  # "day1", "day3", "day7", "day30"
    stats: SimStats
    computed_at: float
