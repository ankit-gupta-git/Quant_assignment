"""
app/domain/models.py
────────────────────
Core domain model dataclasses.
All monetary values use Decimal to prevent floating-point rounding errors
that are unacceptable in a production P&L system.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domain.enums import (
    AlertLevel,
    Exchange,
    MarketRegime,
    OrderStatus,
    OrderType,
    ProductType,
    RiskEvent,
    Side,
    SignalAction,
    StrategyState,
)


# ── Market Data ───────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Candle:
    """
    OHLCV bar.  ``frozen=True`` so candles can be used as dict keys and in sets.
    """
    symbol: str
    exchange: Exchange
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    interval: str = "1m"  # e.g. "1m", "5m", "1h", "1d"

    @property
    def mid_price(self) -> Decimal:
        """Midpoint of high and low."""
        return (self.high + self.low) / Decimal("2")

    @property
    def body_size(self) -> Decimal:
        """Absolute candle body size."""
        return abs(self.close - self.open)

    @property
    def is_bullish(self) -> bool:
        return self.close >= self.open


@dataclass(frozen=True)
class Tick:
    """Real-time level-1 market data tick."""
    symbol: str
    exchange: Exchange
    timestamp: datetime
    last_price: Decimal
    bid: Decimal
    ask: Decimal
    volume: int
    oi: int = 0  # open interest (futures/options)

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid


# ── Orders ────────────────────────────────────────────────────────────────────


@dataclass
class Order:
    """
    Represents a single order in the system lifecycle.
    ``client_order_id`` is our internal idempotency key.
    ``broker_order_id`` is set after the broker acknowledges placement.
    """
    symbol: str
    exchange: Exchange
    side: Side
    order_type: OrderType
    product_type: ProductType
    quantity: int
    price: Decimal  # limit price; ignored for MARKET orders
    strategy_id: str
    client_order_id: str = field(default_factory=lambda: f"ORD-{uuid.uuid4().hex[:12].upper()}")
    broker_order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_price: Decimal = Decimal("0")
    trigger_price: Decimal = Decimal("0")  # for SL orders
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tag: str = ""  # free-form label (e.g. "grid-level-3")
    reject_reason: str = ""

    @property
    def is_terminal(self) -> bool:
        """True if the order cannot change state further."""
        return self.status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}

    @property
    def open_quantity(self) -> int:
        return self.quantity - self.filled_quantity

    @property
    def notional_value(self) -> Decimal:
        return Decimal(str(self.quantity)) * self.price


@dataclass
class Fill:
    """A single execution / fill event for an order."""
    order_id: str
    symbol: str
    exchange: Exchange
    side: Side
    quantity: int
    price: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    fill_id: str = field(default_factory=lambda: f"FILL-{uuid.uuid4().hex[:12].upper()}")
    brokerage: Decimal = Decimal("0")
    stt: Decimal = Decimal("0")
    transaction_charges: Decimal = Decimal("0")
    gst: Decimal = Decimal("0")

    @property
    def net_cost(self) -> Decimal:
        """Total cost of this fill including all charges."""
        return (
            Decimal(str(self.quantity)) * self.price
            + self.brokerage
            + self.stt
            + self.transaction_charges
            + self.gst
        )


# ── Portfolio ─────────────────────────────────────────────────────────────────


@dataclass
class Position:
    """
    Open position for a single symbol.
    Tracks average entry price and realised/unrealised P&L.
    """
    symbol: str
    exchange: Exchange
    side: Side
    quantity: int
    average_price: Decimal
    strategy_id: str
    opened_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    realised_pnl: Decimal = Decimal("0")
    unrealised_pnl: Decimal = Decimal("0")

    def mark_to_market(self, ltp: Decimal) -> None:
        """Update unrealised P&L based on last traded price."""
        qty = Decimal(str(self.quantity))
        if self.side == Side.BUY:
            self.unrealised_pnl = (ltp - self.average_price) * qty
        else:
            self.unrealised_pnl = (self.average_price - ltp) * qty
        self.last_updated = datetime.utcnow()

    @property
    def total_pnl(self) -> Decimal:
        return self.realised_pnl + self.unrealised_pnl

    @property
    def notional_value(self) -> Decimal:
        return Decimal(str(self.quantity)) * self.average_price


@dataclass
class Trade:
    """A completed round-trip (or partial) trade record."""
    symbol: str
    exchange: Exchange
    side: Side
    quantity: int
    entry_price: Decimal
    exit_price: Decimal
    entry_time: datetime
    exit_time: datetime
    strategy_id: str
    gross_pnl: Decimal
    charges: Decimal
    net_pnl: Decimal
    trade_id: str = field(default_factory=lambda: f"TRD-{uuid.uuid4().hex[:12].upper()}")
    reason: str = ""  # e.g. "take_profit", "stop_loss", "kill_switch"


@dataclass
class Portfolio:
    """Aggregate portfolio state."""
    cash: Decimal
    positions: dict[str, Position] = field(default_factory=dict)
    trades: list[Trade] = field(default_factory=list)
    peak_equity: Decimal = Decimal("0")
    daily_realised_pnl: Decimal = Decimal("0")
    consecutive_losses: int = 0

    @property
    def total_unrealised_pnl(self) -> Decimal:
        return sum(p.unrealised_pnl for p in self.positions.values())  # type: ignore[return-value]

    @property
    def equity(self) -> Decimal:
        return self.cash + self.total_unrealised_pnl

    @property
    def drawdown_pct(self) -> float:
        if self.peak_equity == Decimal("0"):
            return 0.0
        dd = (self.peak_equity - self.equity) / self.peak_equity
        return float(dd) * 100

    @property
    def total_exposure(self) -> Decimal:
        return sum(p.notional_value for p in self.positions.values())  # type: ignore[return-value]

    def update_peak(self) -> None:
        """Call after each bar to maintain high-water mark."""
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity


# ── Signals ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Signal:
    """
    Trading signal produced by a strategy.
    Consumed by the execution engine.
    """
    strategy_id: str
    symbol: str
    exchange: Exchange
    action: SignalAction
    price: Decimal
    quantity: int
    timestamp: datetime
    atr: Decimal = Decimal("0")
    confidence: float = 1.0  # [0, 1]
    metadata: dict = field(default_factory=dict)  # type: ignore[assignment]
    signal_id: str = field(default_factory=lambda: f"SIG-{uuid.uuid4().hex[:12].upper()}")


# ── Monitoring ────────────────────────────────────────────────────────────────


@dataclass
class RiskAlert:
    """An alert emitted by the risk engine."""
    event: RiskEvent
    message: str
    level: AlertLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)  # type: ignore[assignment]


@dataclass
class MacroSnapshot:
    """Point-in-time macro reading."""
    date: datetime
    vix: float
    usdinr: float
    crude: float
    bond_yield: float
    regime: MarketRegime = MarketRegime.SIDEWAYS
    score: float = 0.0


@dataclass
class StrategyConfig:
    """Runtime-configurable parameters for a strategy instance."""
    strategy_id: str
    symbol: str
    exchange: Exchange
    atr_multiplier: float = 1.5
    max_positions: int = 10
    take_profit_multiplier: float = 2.0
    stop_loss_multiplier: float = 3.0
    pyramid_enabled: bool = True
    stop_and_reverse: bool = False
    state: StrategyState = StrategyState.ACTIVE
    regime_overrides: dict = field(default_factory=dict)  # type: ignore[assignment]
