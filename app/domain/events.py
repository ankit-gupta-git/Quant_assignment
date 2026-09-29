"""
app/domain/events.py
────────────────────
Domain events that flow through the internal event bus.
Using dataclasses with ``frozen=True`` ensures events are immutable
once emitted, preventing accidental mutation downstream.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.domain.enums import AlertLevel, Exchange, OrderStatus, RiskEvent, Side


@dataclass(frozen=True)
class BaseEvent:
    """Common fields for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class OrderPlacedEvent(BaseEvent):
    """Fired when an order is successfully submitted to the broker."""
    client_order_id: str = ""
    broker_order_id: str = ""
    symbol: str = ""
    exchange: Exchange = Exchange.NSE
    side: Side = Side.BUY
    quantity: int = 0
    price: Decimal = Decimal("0")
    strategy_id: str = ""


@dataclass(frozen=True)
class OrderFilledEvent(BaseEvent):
    """Fired when an order is fully or partially filled."""
    client_order_id: str = ""
    broker_order_id: str = ""
    symbol: str = ""
    exchange: Exchange = Exchange.NSE
    side: Side = Side.BUY
    filled_quantity: int = 0
    average_price: Decimal = Decimal("0")
    status: OrderStatus = OrderStatus.FILLED
    strategy_id: str = ""


@dataclass(frozen=True)
class OrderCancelledEvent(BaseEvent):
    """Fired when an order is cancelled (by user, broker or risk engine)."""
    client_order_id: str = ""
    broker_order_id: str = ""
    symbol: str = ""
    reason: str = ""
    strategy_id: str = ""


@dataclass(frozen=True)
class OrderRejectedEvent(BaseEvent):
    """Fired when a broker rejects an order."""
    client_order_id: str = ""
    symbol: str = ""
    reason: str = ""
    strategy_id: str = ""


@dataclass(frozen=True)
class FillEvent(BaseEvent):
    """Fired for every execution / partial fill."""
    fill_id: str = ""
    order_id: str = ""
    symbol: str = ""
    exchange: Exchange = Exchange.NSE
    side: Side = Side.BUY
    quantity: int = 0
    price: Decimal = Decimal("0")
    gross_pnl: Decimal = Decimal("0")
    net_pnl: Decimal = Decimal("0")
    strategy_id: str = ""


@dataclass(frozen=True)
class PnlUpdateEvent(BaseEvent):
    """Periodic P&L update broadcast to subscribers."""
    symbol: str = ""
    strategy_id: str = ""
    realised_pnl: Decimal = Decimal("0")
    unrealised_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")
    drawdown_pct: float = 0.0


@dataclass(frozen=True)
class RiskEventEmitted(BaseEvent):
    """Fired when the risk engine triggers a rule violation."""
    risk_event: RiskEvent = RiskEvent.KILL_SWITCH
    level: AlertLevel = AlertLevel.CRITICAL
    message: str = ""
    action_taken: str = ""


@dataclass(frozen=True)
class KillSwitchEvent(BaseEvent):
    """Fired when the emergency kill switch is activated."""
    reason: str = ""
    positions_closed: int = 0
    orders_cancelled: int = 0


@dataclass(frozen=True)
class ReconnectEvent(BaseEvent):
    """Fired when the WebSocket reconnects after a drop."""
    broker: str = ""
    attempt: int = 0
    success: bool = False


@dataclass(frozen=True)
class RegimeChangeEvent(BaseEvent):
    """Fired when the macro regime engine detects a regime change."""
    previous_regime: str = ""
    new_regime: str = ""
    score: float = 0.0
