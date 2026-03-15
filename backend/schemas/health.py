from pydantic import BaseModel
from typing import Optional


class HealthComponent(BaseModel):
    status: str  # ok | slow | error
    latency_ms: float
    last_check_at: float
    error: Optional[str] = None


class ScanMetrics(BaseModel):
    last_scan_at: float
    scan_interval_sec: int
    scans_last_hour: int
    scan_errors_last_hour: int


class HealthResponse(BaseModel):
    status: str  # healthy | degraded | down
    components: dict[str, HealthComponent]
    scan_metrics: ScanMetrics
    api_latency_ms: dict[str, float]
    uptime_sec: float
