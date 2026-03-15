"""
Shared FastAPI dependency singletons.
Initialized in main.py lifespan, accessed via these functions.
"""
from typing import Optional
from backend.api.websocket.manager import ConnectionManager
from backend.schemas.dashboard import ControllerSignals, DashboardSnapshot

# Singletons — populated by lifespan in main.py
_binance = None
_noones = None
_premium_monitor = None
_balance_manager = None
_trade_tracker = None
_intelligence = None
_ws_manager: Optional[ConnectionManager] = None

# In-memory state updated each scan cycle
_last_snapshot: Optional[DashboardSnapshot] = None
_last_controller_signals: ControllerSignals = ControllerSignals()
_btc_spot: float = 0.0
_scan_count: int = 0
_scan_errors: int = 0
_start_time: float = 0.0
_demo_mode: bool = False


def get_binance():
    return _binance

def get_noones():
    return _noones

def get_premium_monitor():
    return _premium_monitor

def get_balance_manager():
    return _balance_manager

def get_trade_tracker():
    return _trade_tracker

def get_intelligence():
    return _intelligence

def get_ws_manager() -> ConnectionManager:
    return _ws_manager

def get_last_snapshot() -> Optional[DashboardSnapshot]:
    return _last_snapshot

def get_controller_signals() -> ControllerSignals:
    return _last_controller_signals

def is_demo_mode() -> bool:
    return _demo_mode
