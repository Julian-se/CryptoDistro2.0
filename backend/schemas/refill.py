from pydantic import BaseModel
from typing import Optional


class RefillMethod(BaseModel):
    slug: str
    label: str
    risk: str = "low"
    status: str  # verified | partial | unverified
    buy_service: str
    buy_service_url: str
    lightning_wallet: str
    pipeline_steps: list[str]
    total_time_min: int
    total_time_max: int
    fee_pct_approx: float
    fee_notes: str
    limits: str
    kyc_required: str
    gaps: Optional[str] = None
    workaround: Optional[str] = None
    evidence_urls: list[str] = []


class RefillMarket(BaseModel):
    name: str
    currency: str
    flag: str
    methods: list[RefillMethod]


class RefillPipeline(BaseModel):
    markets: list[RefillMarket]
    source_file: str
    parsed_at: float
