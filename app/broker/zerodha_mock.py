"""
app/broker/zerodha_mock.py
──────────────────────────
Mock Zerodha broker implementation.

Simulates the full Zerodha Kite Connect API behaviour without hitting any
real endpoints.  Designed for:
  * Local development and testing.
  * Backtest order execution simulation.
  * Integration tests that need realistic broker behaviour.

Simulated features:
  * Idempotent order placement using client_order_id.
  * Realistic fill simulation (MARKET → immediate fill, LIMIT → fill on price).
  * Partial fill simulation (configurable probability).
  * Rejection simulation (configurable probability).
  * WebSocket tick streaming with synthetic OHLCV data.
  * Heartbeat and reconnect simulation.
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime
from decimal import Decimal
from typing import AsyncIterator

from app.broker.base import BrokerBase
from app.core.logger import get_logger
from app.domain.enums import Exchange, OrderStatus, OrderType, Side
from app.domain.models import Fill, Order, Position, Tick

log = get_logger(__name__)

# Probability of a LIMIT order being rejected by the mock (0.0–1.0)
_REJECTION_PROBABILITY = 0.02
# Probability of a MARKET order getting a partial fill first
_PARTIAL_FILL_PROBABILITY = 0.05


class ZerodhaMockBroker(BrokerBase):
    """
    In-memory mock of the Zerodha Kite Connect REST + WebSocket API.

    Args:
        slippage_bps:   Slippage in basis points applied to MARKET orders.
        tick_interval:  Seconds between synthetic tick events (for streaming).
        base_price:     Starting price for the mock tick generator.
    """

    def __init__(
        self,
        slippage_bps: float = 5.0,
        tick_interval: float = 0.5,
        base_price: float = 19800.0,
        # Zerodha-style credential kwargs — accepted but ignored in mock
        api_key: str | None = None,
        api_secret: str | None = None,
        access_token: str | None = None,
    ) -> None:
        self.slippage_bps = slippage_bps
        self.tick_interval = tick_interval
        self._base_price = base_price
        self._is_connected: bool = False
        self._orders: dict[str, Order] = {}          # client_order_id -> Order
        self._broker_to_client: dict[str, str] = {}  # broker_id -> client_order_id
        self._fills: dict[str, list[Fill]] = {}      # client_order_id -> fills
        self._positions: dict[str, Position] = {}
        self._current_price: float = base_price
        self._reconnect_count: int = 0

    # ── Connection lifecycle ──────────────────────────────────────────────────

    async def connect(self) -> None:
        await asyncio.sleep(0.05)  # simulate network handshake
        self._is_connected = True
        log.info("mock_broker.connected", broker="zerodha_mock")

    async def disconnect(self) -> None:
        self._is_connected = False
        log.info("mock_broker.disconnected", broker="zerodha_mock")

    async def reconnect(self) -> None:
        """Simulate a WebSocket reconnect with exponential backoff."""
        self._reconnect_count += 1
        backoff = min(30.0, 2.0 ** self._reconnect_count)
        log.warning(
            "mock_broker.reconnecting",
            attempt=self._reconnect_count,
            backoff=backoff,
        )
        await asyncio.sleep(min(backoff, 0.1))  # fast in tests
        await self.connect()

    # ── Order management ──────────────────────────────────────────────────────

    async def place_order(self, order: Order) -> Order:
        """Place an order, simulating realistic broker behaviour."""
        self._assert_connected()

        # Idempotency: return existing order if already placed
        if order.client_order_id in self._orders:
            existing = self._orders[order.client_order_id]
            log.warning(
                "mock_broker.duplicate_order",
                client_order_id=order.client_order_id,
                status=existing.status.value,
            )
            return existing

        # Simulate broker-side rejection
        if random.random() < _REJECTION_PROBABILITY:
            order.status = OrderStatus.REJECTED
            order.reject_reason = "Mock: simulated broker rejection"
            order.broker_order_id = f"MOCK-REJ-{uuid.uuid4().hex[:8].upper()}"
            self._orders[order.client_order_id] = order
            log.warning("mock_broker.order_rejected", client_order_id=order.client_order_id)
            return order

        # Assign broker order ID
        order.broker_order_id = f"MOCK-{uuid.uuid4().hex[:10].upper()}"
        order.status = OrderStatus.OPEN
        order.updated_at = datetime.utcnow()
        self._orders[order.client_order_id] = order
        self._broker_to_client[order.broker_order_id] = order.client_order_id
        self._fills[order.client_order_id] = []

        log.info(
            "mock_broker.order_placed",
            client_order_id=order.client_order_id,
            broker_order_id=order.broker_order_id,
            symbol=order.symbol,
            side=order.side.value,
            qty=order.quantity,
        )

        # Schedule asynchronous fill simulation
        asyncio.create_task(self._simulate_fill(order))
        return order

    async def cancel_order(self, order: Order) -> Order:
        self._assert_connected()
        stored = self._orders.get(order.client_order_id)
        if stored is None:
            log.warning("mock_broker.cancel_unknown", client_order_id=order.client_order_id)
            return order
        if stored.is_terminal:
            return stored  # idempotent: already done
        stored.status = OrderStatus.CANCELLED
        stored.updated_at = datetime.utcnow()
        log.info("mock_broker.order_cancelled", client_order_id=order.client_order_id)
        return stored

    async def modify_order(
        self,
        order: Order,
        new_price: float | None = None,
        new_quantity: int | None = None,
    ) -> Order:
        self._assert_connected()
        stored = self._orders.get(order.client_order_id)
        if stored is None or stored.is_terminal:
            return order
        if new_price is not None:
            stored.price = Decimal(str(new_price))
        if new_quantity is not None:
            stored.quantity = new_quantity
        stored.updated_at = datetime.utcnow()
        log.info(
            "mock_broker.order_modified",
            client_order_id=order.client_order_id,
            new_price=new_price,
            new_quantity=new_quantity,
        )
        return stored

    # ── Account state ─────────────────────────────────────────────────────────

    async def positions(self) -> list[Position]:
        self._assert_connected()
        return list(self._positions.values())

    async def orders(self) -> list[Order]:
        self._assert_connected()
        return list(self._orders.values())

    async def get_fills(self, order_id: str) -> list[Fill]:
        # order_id here is client_order_id for internal consistency
        return self._fills.get(order_id, [])

    # ── Market data / WebSocket simulation ────────────────────────────────────

    async def stream_ticks(self, symbols: list[str]) -> AsyncIterator[Tick]:  # type: ignore[override]
        """
        Yield simulated tick events using a random-walk price model.

        The tick generator runs indefinitely until the caller cancels it via
        ``asyncio.CancelledError``.
        """
        self._assert_connected()
        log.info("mock_broker.tick_stream_started", symbols=symbols)
        try:
            while True:
                await asyncio.sleep(self.tick_interval)
                # Random walk
                change_pct = random.gauss(0, 0.001)
                self._current_price = max(
                    1.0, self._current_price * (1 + change_pct)
                )
                spread = self._current_price * 0.0001
                for symbol in symbols:
                    tick = Tick(
                        symbol=symbol,
                        exchange=Exchange.NSE,
                        timestamp=datetime.utcnow(),
                        last_price=Decimal(str(round(self._current_price, 2))),
                        bid=Decimal(str(round(self._current_price - spread, 2))),
                        ask=Decimal(str(round(self._current_price + spread, 2))),
                        volume=random.randint(100, 10000),
                        oi=0,
                    )
                    yield tick
        except asyncio.CancelledError:
            log.info("mock_broker.tick_stream_stopped")

    # ── Internal fill simulation ──────────────────────────────────────────────

    async def _simulate_fill(self, order: Order) -> None:
        """Async task that fills the order after a simulated exchange latency."""
        await asyncio.sleep(random.uniform(0.01, 0.1))

        if order.is_terminal:
            return

        fill_price = self._compute_fill_price(order)
        is_partial = (
            order.order_type != OrderType.MARKET
            and random.random() < _PARTIAL_FILL_PROBABILITY
        )
        fill_qty = max(1, order.quantity // 2) if is_partial else order.quantity

        fill = Fill(
            order_id=order.client_order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side,
            quantity=fill_qty,
            price=fill_price,
        )
        self._fills[order.client_order_id].append(fill)

        order.filled_quantity += fill_qty
        order.average_price = fill_price
        order.status = (
            OrderStatus.PARTIALLY_FILLED if is_partial else OrderStatus.FILLED
        )
        order.updated_at = datetime.utcnow()

        self._update_position(order, fill)

        log.info(
            "mock_broker.fill",
            client_order_id=order.client_order_id,
            fill_qty=fill_qty,
            fill_price=str(fill_price),
            status=order.status.value,
        )

        # If partially filled, fill the remainder after a short delay
        if is_partial and not order.is_terminal:
            await asyncio.sleep(random.uniform(0.05, 0.2))
            await self._simulate_fill(order)

    def _compute_fill_price(self, order: Order) -> Decimal:
        """Compute the simulated fill price including slippage for MARKET orders."""
        base = Decimal(str(self._current_price))
        if order.order_type == OrderType.MARKET:
            slip = base * Decimal(str(self.slippage_bps / 10000.0))
            if order.side == Side.BUY:
                return base + slip
            else:
                return base - slip
        return order.price  # LIMIT: fill at the limit price

    def _update_position(self, order: Order, fill: Fill) -> None:
        """Update internal position tracking after a fill."""
        key = f"{order.symbol}:{order.exchange.value}"
        pos = self._positions.get(key)

        if pos is None:
            if order.side == Side.BUY:
                self._positions[key] = Position(
                    symbol=order.symbol,
                    exchange=order.exchange,
                    side=Side.BUY,
                    quantity=fill.quantity,
                    average_price=fill.price,
                    strategy_id=order.strategy_id,
                )
        else:
            if order.side == pos.side:
                # Adding to position: recompute average
                total_qty = pos.quantity + fill.quantity
                pos.average_price = (
                    pos.average_price * Decimal(str(pos.quantity))
                    + fill.price * Decimal(str(fill.quantity))
                ) / Decimal(str(total_qty))
                pos.quantity = total_qty
            else:
                # Reducing / closing position
                pos.quantity -= fill.quantity
                if pos.quantity <= 0:
                    del self._positions[key]

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _assert_connected(self) -> None:
        if not self._is_connected:
            raise RuntimeError("Broker not connected. Call connect() first.")

    @property
    def order_count(self) -> int:
        return len(self._orders)

    @property
    def current_price(self) -> float:
        return self._current_price
