"""
Python port of noones_lightning_simulator_260315.html JS simulation engine.
Adds joblib parallelism for Monte Carlo confidence bands.
"""
import time
import numpy as np
from scipy.signal import savgol_filter
from joblib import Parallel, delayed

START = 500
BASE_TRADE = 60
MAX_TRADE = 200
REP_DAYS = 10
CB_LN = 0.012 / 7    # 1.2% weekly chargeback → daily
CB_OC = 0.025 / 7    # 2.5% weekly chargeback → daily


def cycles_per_day(fiat_minutes: float, active_hours: float) -> int:
    return int((60.0 / fiat_minutes) * active_hours)


def _sim_ln_single(
    spread: float,
    fiat_minutes: float,
    active_hours: float,
    days: int,
    rng: np.random.Generator,
) -> dict:
    """Single Monte Carlo run for Lightning scenario."""
    cyc = cycles_per_day(fiat_minutes, active_hours)
    capital, profit, volume = [START], [0], [0]
    cap, cum = float(START), 0.0

    for d in range(1, days + 1):
        rep = (0.35 + 0.65 * (d / REP_DAYS)) if d <= REP_DAYS else 1.0
        trades = int(cyc * rep)
        t_size = min(MAX_TRADE, BASE_TRADE + (cap - START) * 0.05)
        t_size = max(BASE_TRADE, t_size)
        max_sim = int(cap / t_size) if t_size > 0 else 0
        actual = min(trades, max_sim * 3)
        vol = actual * t_size
        gross = vol * (spread / 100.0)
        cb_hit = rng.random() < CB_LN
        cb_loss = cb_hit * t_size * (0.6 + rng.random() * 0.6)
        net = gross - cb_loss
        cap = max(0.0, cap + net)
        cum += net
        capital.append(int(round(cap)))
        profit.append(int(round(cum)))
        volume.append(int(round(vol)))

    return {"capital": capital, "profit": profit, "volume": volume}


def _sim_oc_single(
    spread: float,
    active_hours: float,
    days: int,
    rng: np.random.Generator,
) -> dict:
    """Single Monte Carlo run for on-chain scenario."""
    cyc = int(1.3 * active_hours)
    capital, profit, volume = [START], [0], [0]
    cap, cum = float(START), 0.0

    for d in range(1, days + 1):
        rep = (0.4 + 0.6 * (d / 14)) if d <= 14 else 1.0
        trades = int(cyc * rep)
        t_size = min(MAX_TRADE, BASE_TRADE + (cap - START) * 0.05)
        t_size = max(BASE_TRADE, t_size)
        vol = trades * t_size
        gross = vol * (spread / 100.0)
        cb_hit = rng.random() < CB_OC
        cb_loss = cb_hit * t_size * (0.8 + rng.random() * 0.8)
        net = gross - cb_loss
        cap = max(0.0, cap + net)
        cum += net
        capital.append(int(round(cap)))
        profit.append(int(round(cum)))
        volume.append(int(round(vol)))

    return {"capital": capital, "profit": profit, "volume": volume}


def _smooth(arr: list[int]) -> list[int]:
    if len(arr) < 6:
        return arr
    win = min(7, len(arr) if len(arr) % 2 == 1 else len(arr) - 1)
    if win < 3:
        return arr
    smoothed = savgol_filter(arr, window_length=win, polyorder=2)
    return [int(round(v)) for v in smoothed]


def run_simulation(
    spread: float,
    fiat_minutes: float,
    active_hours: float,
    days: int = 30,
    runs: int = 10,
) -> dict:
    """
    Run N Monte Carlo simulations in parallel.
    Returns mean + p10/p90 bands for Lightning and on-chain.
    """
    runs = max(1, min(runs, 50))

    # Run in parallel via joblib
    ln_results = Parallel(n_jobs=-1)(
        delayed(_sim_ln_single)(spread, fiat_minutes, active_hours, days, np.random.default_rng(s))
        for s in range(runs)
    )
    oc_results = Parallel(n_jobs=-1)(
        delayed(_sim_oc_single)(spread, active_hours, days, np.random.default_rng(s + 1000))
        for s in range(runs)
    )

    def aggregate(results: list[dict]) -> dict:
        out = {}
        for key in ("capital", "profit", "volume"):
            matrix = np.array([r[key] for r in results])
            mean_line = np.mean(matrix, axis=0).astype(int).tolist()
            p10_line = np.percentile(matrix, 10, axis=0).astype(int).tolist()
            p90_line = np.percentile(matrix, 90, axis=0).astype(int).tolist()
            out[key] = mean_line
            out[f"{key}_p10"] = p10_line
            out[f"{key}_p90"] = p90_line
        out["smoothed_capital"] = _smooth(out["capital"])
        return out

    ln = aggregate(ln_results)
    oc = aggregate(oc_results)

    return {
        "lightning": {
            "capital": ln["capital"],
            "profit": ln["profit"],
            "volume": ln["volume"],
            "p10": ln["capital_p10"],
            "p90": ln["capital_p90"],
            "smoothed_capital": ln["smoothed_capital"],
        },
        "onchain": {
            "capital": oc["capital"],
            "profit": oc["profit"],
            "volume": oc["volume"],
            "p10": oc["capital_p10"],
            "p90": oc["capital_p90"],
            "smoothed_capital": oc["smoothed_capital"],
        },
    }
