"""
app/domain/enums.py
───────────────────
All enumerations used across the trading engine.
Keep enums here so they are importable without circular dependencies.
"""
from __future__ import annotations

from enum import Enum, auto


class Side(str, Enum):
    """Trade / order direction."""
    BUY = "BUY"
    SELL = "SELL"

    def opposite(self) -> "Side":
        return Side.SELL if self == Side.BUY else Side.BUY


class OrderType(str, Enum):
    """Supported order types on the exchange."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LOSS_MARKET = "STOP_LOSS_MARKET"


class OrderStatus(str, Enum):
    """Lifecycle states of an order."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class ProductType(str, Enum):
    """Zerodha product codes."""
    CNC = "CNC"       # Delivery
    MIS = "MIS"       # Intraday
    NRML = "NRML"     # Futures / Options carry-forward


class Exchange(str, Enum):
    """Supported exchanges."""
    NSE = "NSE"
    BSE = "BSE"
    MCX = "MCX"
    NFO = "NFO"       # NSE Futures & Options
    BFO = "BFO"       # BSE Futures & Options


class MarketRegime(str, Enum):
    """Macro market regime labels."""
    BULL = "BULL"
    BEAR = "BEAR"
    RISK_OFF = "RISK_OFF"
    SIDEWAYS = "SIDEWAYS"


class SignalAction(str, Enum):
    """Actions that a strategy signal can request."""
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    EXIT_LONG = "EXIT_LONG"
    EXIT_SHORT = "EXIT_SHORT"
    REVERSE_TO_LONG = "REVERSE_TO_LONG"
    REVERSE_TO_SHORT = "REVERSE_TO_SHORT"
    HOLD = "HOLD"
    PYRAMID_LONG = "PYRAMID_LONG"
    PYRAMID_SHORT = "PYRAMID_SHORT"


class RiskEvent(str, Enum):
    """Events emitted by the risk engine."""
    MAX_DAILY_LOSS = "MAX_DAILY_LOSS"
    MAX_EXPOSURE = "MAX_EXPOSURE"
    MAX_CONSECUTIVE_LOSSES = "MAX_CONSECUTIVE_LOSSES"
    MAX_DRAWDOWN = "MAX_DRAWDOWN"
    KILL_SWITCH = "KILL_SWITCH"
    POSITION_CAP = "POSITION_CAP"


class AlertLevel(str, Enum):
    """Severity levels for monitoring alerts."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class StrategyState(str, Enum):
    """Lifecycle state of a running strategy instance."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
