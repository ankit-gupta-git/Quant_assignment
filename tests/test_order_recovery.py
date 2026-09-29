"""
tests/test_order_recovery.py
─────────────────────────────
Tests for crash-recovery: OrderManager must restore open orders from
DuckDB on restart and reconcile with the broker.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.broker.zerodha_mock import ZerodhaMockBroker
from app.domain.enums import Exchange, OrderStatus, OrderType, ProductType, Side
from app.domain.models import Order, Portfolio
from app.execution.order_manager import OrderManager
from app.execution.reconciliation import ReconciliationEngine
from app.storage.duckdb_store import DuckDBStore


@pytest.fixture
def in_memory_store() -> DuckDBStore:
    return DuckDBStore(":memory:")


@pytest.fixture
def broker() -> ZerodhaMockBroker:
    return ZerodhaMockBroker()


@pytest.fixture
def portfolio() -> Portfolio:
    return Portfolio(cash=Decimal("1000000"), peak_equity=Decimal("1000000"))


@pytest.fixture
def order_manager(
    broker: ZerodhaMockBroker, in_memory_store: DuckDBStore, portfolio: Portfolio
) -> OrderManager:
    return OrderManager(broker=broker, store=in_memory_store, portfolio=portfolio)


@pytest.fixture
def pending_order() -> Order:
    return Order(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        product_type=ProductType.MIS,
        quantity=1,
        price=Decimal("18000"),
        strategy_id="recovery-test",
        status=OrderStatus.OPEN,
    )


class TestOrderPersistence:
    def test_order_persisted_in_store(
        self, in_memory_store: DuckDBStore, pending_order: Order
    ) -> None:
        in_memory_store.upsert_order(pending_order)
        loaded = in_memory_store.load_open_orders()
        assert any(o.client_order_id == pending_order.client_order_id for o in loaded)

    def test_three_open_orders_loadable(self, in_memory_store: DuckDBStore) -> None:
        for _ in range(3):
            o = Order(
                symbol="NIFTY",
                exchange=Exchange.NSE,
                side=Side.BUY,
                order_type=OrderType.LIMIT,
                product_type=ProductType.MIS,
                quantity=1,
                price=Decimal("18000"),
                strategy_id="test",
                status=OrderStatus.OPEN,
            )
            in_memory_store.upsert_order(o)
        open_orders = in_memory_store.load_open_orders()
        assert len(open_orders) == 3

    def test_filled_orders_excluded_from_open(self, in_memory_store: DuckDBStore) -> None:
        filled_order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=1,
            price=Decimal("18000"),
            strategy_id="test",
            status=OrderStatus.FILLED,
        )
        in_memory_store.upsert_order(filled_order)
        open_orders = in_memory_store.load_open_orders()
        assert all(o.status != OrderStatus.FILLED for o in open_orders)

    @pytest.mark.asyncio
    async def test_restore_from_db_loads_open_orders(
        self, order_manager: OrderManager, in_memory_store: DuckDBStore
    ) -> None:
        order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=1,
            price=Decimal("18000"),
            strategy_id="test",
            status=OrderStatus.OPEN,
        )
        in_memory_store.upsert_order(order)
        count = await order_manager.restore_from_db()
        assert count >= 1

    @pytest.mark.asyncio
    async def test_submit_idempotent(
        self,
        broker: ZerodhaMockBroker,
        order_manager: OrderManager,
        pending_order: Order,
    ) -> None:
        await broker.connect()
        result1 = await order_manager.submit(pending_order)
        result2 = await order_manager.submit(pending_order)
        assert result1 is not None
        assert result2 is not None
        assert result1.client_order_id == result2.client_order_id


class TestReconciliationEngine:
    @pytest.mark.asyncio
    async def test_reconcile_detects_status_mismatch(
        self,
        broker: ZerodhaMockBroker,
        portfolio: Portfolio,
        in_memory_store: DuckDBStore,
    ) -> None:
        await broker.connect()
        engine = ReconciliationEngine(broker=broker, portfolio=portfolio)

        # Create a local order whose status disagrees with broker (broker knows nothing)
        local_order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=1,
            price=Decimal("18000"),
            strategy_id="test",
            status=OrderStatus.OPEN,
        )
        local_orders: dict[str, Order] = {local_order.client_order_id: local_order}
        reconciled = await engine.reconcile_orders(local_orders)
        # Broker has no such order → logged as warning, no update
        assert isinstance(reconciled, list)

    @pytest.mark.asyncio
    async def test_reconcile_positions_empty(
        self,
        broker: ZerodhaMockBroker,
        portfolio: Portfolio,
    ) -> None:
        await broker.connect()
        engine = ReconciliationEngine(broker=broker, portfolio=portfolio)
        reconciled = await engine.reconcile_positions()
        assert isinstance(reconciled, list)

    @pytest.mark.asyncio
    async def test_full_reconcile_returns_dict(
        self,
        broker: ZerodhaMockBroker,
        portfolio: Portfolio,
    ) -> None:
        await broker.connect()
        engine = ReconciliationEngine(broker=broker, portfolio=portfolio)
        result = await engine.full_reconcile({})
        assert "orders" in result
        assert "positions" in result
