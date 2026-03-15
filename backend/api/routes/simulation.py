from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from backend.simulation.runner import run_simulation_full
from backend.schemas.simulation import SimulationResult

router = APIRouter()


class SimRequest(BaseModel):
    scenario: str = "realistic"
    spread_pct: Optional[float] = None
    fiat_minutes: Optional[float] = None
    active_hours: Optional[float] = None
    days: int = 30
    runs: int = 10


@router.post("/simulation/run", response_model=SimulationResult)
async def run_simulation(req: SimRequest):
    result = run_simulation_full(
        scenario=req.scenario,
        spread_pct=req.spread_pct,
        fiat_minutes=req.fiat_minutes,
        active_hours=req.active_hours,
        days=min(req.days, 90),
        runs=min(req.runs, 50),
    )
    return result
