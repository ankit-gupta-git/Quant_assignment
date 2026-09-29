"""
tests/test_storage.py
──────────────────────
Unit tests for the DuckDB storage layer and Parquet export.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums import Exchange, OrderStatus, OrderType, ProductType, Side
from app.domain.models import Fill, Order, Portfolio, Position, Trade
from app.storage.duckdb_store import DuckDBStore
from app.storage.parquet import export_trades, read_parquet


@pytest.fixture
def store() -> DuckDBStore:
    """In-memory DuckDB store for isolated tests."""
    return DuckDBStore(":memory:")


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


@pytest.fixture
def sample_trade() -> Trade:
    return Trade(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        side=Side.BUY,
        quantity=1,
        entry_price=Decimal("18000"),
        exit_price=Decimal("18200"),
        entry_time=datetime(2023, 6, 1, 9, 15),
        exit_time=datetime(2023, 6, 1, 10, 30),
        strategy_id="test",
        gross_pnl=Decimal("200"),
        charges=Decimal("15"),
        net_pnl=Decimal("185"),
        reason="take_profit",
    )


class TestDuckDBOrders:
    def test_upsert_and_load(self, store: DuckDBStore, sample_order: Order) -> None:
        store.upsert_order(sample_order)
        orders = store.load_open_orders()
        assert any(o.client_order_id == sample_order.client_order_id for o in orders)

    def test_upsert_idempotent(self, store: DuckDBStore, sample_order: Order) -> None:
        store.upsert_order(sample_order)
        store.upsert_order(sample_order)
        orders = store.load_all_orders()
        matching = [o for o in orders if o.client_order_id == sample_order.client_order_id]
        assert len(matching) == 1

    def test_status_update(self, store: DuckDBStore, sample_order: Order) -> None:
        store.upsert_order(sample_order)
        sample_order.status = OrderStatus.FILLED
        sample_order.filled_quantity = 1
        store.upsert_order(sample_order)
        orders = store.load_all_orders()
        updated = next(o for o in orders if o.client_order_id == sample_order.client_order_id)
        assert updated.status == OrderStatus.FILLED

    def test_terminal_orders_not_in_open(self, store: DuckDBStore, sample_order: Order) -> None:
        sample_order.status = OrderStatus.FILLED
        store.upsert_order(sample_order)
        open_orders = store.load_open_orders()
        assert all(o.client_order_id != sample_order.client_order_id for o in open_orders)


class TestDuckDBTrades:
    def test_insert_and_load(self, store: DuckDBStore, sample_trade: Trade) -> None:
        store.insert_trade(sample_trade)
        trades = store.load_trades()
        assert any(t.trade_id == sample_trade.trade_id for t in trades)

    def test_insert_idempotent(self, store: DuckDBStore, sample_trade: Trade) -> None:
        store.insert_trade(sample_trade)
        store.insert_trade(sample_trade)  # second insert should be no-op
        trades = store.load_trades()
        matching = [t for t in trades if t.trade_id == sample_trade.trade_id]
        assert len(matching) == 1

    def test_filter_by_strategy(self, store: DuckDBStore, sample_trade: Trade) -> None:
        store.insert_trade(sample_trade)
        trades = store.load_trades(strategy_id="nonexistent")
        assert len(trades) == 0
        trades = store.load_trades(strategy_id="test")
        assert len(trades) == 1

    def test_daily_pnl_summary(self, store: DuckDBStore, sample_trade: Trade) -> None:
        store.insert_trade(sample_trade)
        summary = store.daily_pnl_summary()
        assert len(summary) >= 1
        assert "net_pnl" in summary[0]


class TestDuckDBPortfolio:
    def test_snapshot_and_reload(self, store: DuckDBStore) -> None:
        portfolio = Portfolio(
            cash=Decimal("800000"),
            peak_equity=Decimal("1000000"),
        )
        portfolio.positions["NIFTY:NSE"] = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=2,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        store.save_portfolio_snapshot(portfolio)
        snap = store.load_latest_portfolio_snapshot()
        assert snap is not None
        assert snap["cash"] == Decimal("800000")


class TestParquetExport:
    def test_export_trades(self, sample_trade: Trade, tmp_path) -> None:
        path = export_trades([sample_trade], tmp_path)
        assert path.exists()
        df = read_parquet(path)
        assert len(df) == 1
        assert "trade_id" in df.columns

    def test_export_empty_trades(self, tmp_path) -> None:
        path = export_trades([], tmp_path)
        assert path.suffix == ".parquet"
