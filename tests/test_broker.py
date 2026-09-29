"""
tests/test_broker.py
─────────────────────
Unit tests for the mock Zerodha broker.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.broker.zerodha_mock import ZerodhaMockBroker
from app.domain.enums import Exchange, OrderStatus, OrderType, ProductType, Side
from app.domain.models import Order


@pytest.fixture
def broker() -> ZerodhaMockBroker:
    return ZerodhaMockBroker(slippage_bps=5.0, tick_interval=0.01)


@pytest.fixture
def sample_order() -> Order:
    return Order(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.MIS,
        quantity=1,
        price=Decimal("18000"),
        strategy_id="test",
    )


class TestBrokerConnect:
    @pytest.mark.asyncio
    async def test_connect_succeeds(self, broker: ZerodhaMockBroker) -> None:
        await broker.connect()
        assert broker._is_connected

    @pytest.mark.asyncio
    async def test_double_connect_idempotent(self, broker: ZerodhaMockBroker) -> None:
        await broker.connect()
        await broker.connect()
        assert broker._is_connected


class TestOrderPlacement:
    @pytest.mark.asyncio
    async def test_place_order_returns_order_with_broker_id(
        self, broker: ZerodhaMockBroker, sample_order: Order
    ) -> None:
        await broker.connect()
        returned = await broker.place_order(sample_order)
        assert returned.broker_order_id is not None

    @pytest.mark.asyncio
    async def test_place_order_updates_status(
        self, broker: ZerodhaMockBroker, sample_order: Order
    ) -> None:
        await broker.connect()
        returned = await broker.place_order(sample_order)
        assert returned.status in {
            OrderStatus.OPEN,
            OrderStatus.FILLED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.REJECTED,
        }

    @pytest.mark.asyncio
    async def test_duplicate_order_returns_same_object(
        self, broker: ZerodhaMockBroker, sample_order: Order
    ) -> None:
        """Placing the same client_order_id twice must be idempotent."""
        await broker.connect()
        returned1 = await broker.place_order(sample_order)
        returned2 = await broker.place_order(sample_order)
        assert returned1.client_order_id == returned2.client_order_id
        assert returned1.broker_order_id == returned2.broker_order_id


class TestOrderCancellation:
    @pytest.mark.asyncio
    async def test_cancel_open_order(
        self, broker: ZerodhaMockBroker, sample_order: Order
    ) -> None:
        await broker.connect()
        await broker.place_order(sample_order)
        # Force to OPEN so cancel works
        sample_order.status = OrderStatus.OPEN
        cancelled = await broker.cancel_order(sample_order)
        assert cancelled.status == OrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_unknown_order_returns_order(
        self, broker: ZerodhaMockBroker, sample_order: Order
    ) -> None:
        await broker.connect()
        # Order was never placed → cancel returns the original order unchanged
        result = await broker.cancel_order(sample_order)
        assert result is not None


class TestPositionsAndOrders:
    @pytest.mark.asyncio
    async def test_positions_returns_list(self, broker: ZerodhaMockBroker) -> None:
        await broker.connect()
        positions = await broker.positions()
        assert isinstance(positions, list)

    @pytest.mark.asyncio
    async def test_orders_contains_placed_order(
        self, broker: ZerodhaMockBroker, sample_order: Order
    ) -> None:
        await broker.connect()
        await broker.place_order(sample_order)
        orders = await broker.orders()
        assert any(o.client_order_id == sample_order.client_order_id for o in orders)

    @pytest.mark.asyncio
    async def test_reconnect_restores_connection(self, broker: ZerodhaMockBroker) -> None:
        await broker.connect()
        await broker.disconnect()
        assert not broker._is_connected
        await broker.reconnect()
        assert broker._is_connected
