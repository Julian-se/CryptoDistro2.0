"""Simulation runner — builds full SimulationResult from params."""
import time
from backend.simulation.engine import run_simulation, cycles_per_day, BASE_TRADE
from backend.simulation.scenarios import SCENARIOS
from backend.schemas.simulation import (
    SimParams, SimResult, SimulationResult, MilestonePoint, SimStats,
)


def run_simulation_full(
    scenario: str = "realistic",
    spread_pct: float | None = None,
    fiat_minutes: float | None = None,
    active_hours: float | None = None,
    days: int = 30,
    runs: int = 10,
) -> SimulationResult:
    # Resolve params
    if scenario in SCENARIOS:
        preset = SCENARIOS[scenario]
        sp = spread_pct if spread_pct is not None else preset["spread_pct"]
        fm = fiat_minutes if fiat_minutes is not None else preset["fiat_minutes"]
        ah = active_hours if active_hours is not None else preset["active_hours"]
        market = preset.get("market")
    else:
        sp = spread_pct or 9.0
        fm = fiat_minutes or 20.0
        ah = active_hours or 10.0
        market = "Custom"

    params = SimParams(
        scenario=scenario,
        spread_pct=sp,
        fiat_minutes=fm,
        active_hours=ah,
        days=days,
        runs=runs,
        market=market,
    )

    results = run_simulation(sp, fm, ah, days, runs)
    ln = results["lightning"]
    oc = results["onchain"]

    def make_sim_result(r: dict) -> SimResult:
        return SimResult(
            capital=r["capital"],
            profit=r["profit"],
            volume=r["volume"],
            p10=r["p10"],
            p90=r["p90"],
            smoothed_capital=r["smoothed_capital"],
        )

    def milestone(r: dict, day: int) -> MilestonePoint:
        idx = min(day, len(r["capital"]) - 1)
        cap = r["capital"][idx]
        pft = r["profit"][idx]
        vol_day = r["volume"][idx] if idx < len(r["volume"]) else 0
        pct_change = ((cap - 500) / 500.0) * 100.0
        return MilestonePoint(
            day=day, capital=cap, profit=pft,
            volume_day=vol_day, capital_pct_change=round(pct_change, 1)
        )

    milestones = {
        "day1": milestone(ln, 1),
        "day3": milestone(ln, 3),
        "day7": milestone(ln, 7),
        "day30": milestone(ln, min(30, days)),
    }

    cpd_ln = cycles_per_day(fm, ah)
    cpd_oc = int(1.3 * ah)
    vel_mult = round(cpd_ln / cpd_oc, 1) if cpd_oc > 0 else 1.0
    profit_per_cycle = round(BASE_TRADE * (sp / 100.0), 2)
    monthly_vol_ln = sum(ln["volume"])
    monthly_vol_oc = sum(oc["volume"])
    month_idx = min(30, days) if days >= 30 else days
    monthly_profit = ln["profit"][month_idx] if month_idx < len(ln["profit"]) else 0
    monthly_p10 = ln["p10"][month_idx] if month_idx < len(ln["p10"]) else 0
    monthly_p90 = ln["p90"][month_idx] if month_idx < len(ln["p90"]) else 0

    stats = SimStats(
        cycles_per_day_ln=cpd_ln,
        cycles_per_day_oc=cpd_oc,
        velocity_multiplier=vel_mult,
        profit_per_cycle=profit_per_cycle,
        monthly_volume_ln=monthly_vol_ln,
        monthly_volume_oc=monthly_vol_oc,
        monthly_net_profit_mean=monthly_profit,
        monthly_net_profit_p10=monthly_p10,
        monthly_net_profit_p90=monthly_p90,
    )

    return SimulationResult(
        params=params,
        lightning=make_sim_result(ln),
        onchain=make_sim_result(oc),
        milestones=milestones,
        stats=stats,
        computed_at=time.time(),
    )
