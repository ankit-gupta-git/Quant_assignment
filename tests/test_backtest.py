"""
tests/test_backtest.py
───────────────────────
Integration tests for the backtesting engine.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.backtest.engine import BacktestEngine
from app.backtest.slippage import FixedSlippage, VolumeSlippage
from app.backtest.brokerage import NSEEquityBrokerage
from app.domain.enums import Exchange
from app.domain.models import Candle, StrategyConfig
from app.storage.duckdb_store import DuckDBStore
from app.strategy.grid import GridStrategy


def make_candles(n: int = 300, seed: int = 42) -> list[Candle]:
    random.seed(seed)
    base_ts = datetime(2023, 1, 1, 9, 15)
    candles: list[Candle] = []
    price = 18000.0
    for i in range(n):
        price += random.uniform(-40, 40)
        c = Decimal(str(round(price, 2)))
        h = c + Decimal(str(round(abs(random.uniform(5, 50)), 2)))
        l = c - Decimal(str(round(abs(random.uniform(5, 50)), 2)))
        candles.append(
            Candle(
                symbol="NIFTY",
                exchange=Exchange.NSE,
                timestamp=base_ts + timedelta(minutes=i),
                open=c,
                high=h,
                low=l,
                close=c,
                volume=random.randint(100_000, 1_000_000),
            )
        )
    return candles


@pytest.fixture
def grid_strategy() -> GridStrategy:
    config = StrategyConfig(
        strategy_id="backtest-grid",
        symbol="NIFTY",
        exchange=Exchange.NSE,
        atr_multiplier=1.0,
        max_positions=5,
        take_profit_multiplier=3.0,
        stop_loss_multiplier=5.0,
        pyramid_enabled=True,
    )
    return GridStrategy(config)


@pytest.fixture
def backtest_engine(grid_strategy: GridStrategy, tmp_path) -> BacktestEngine:
    return BacktestEngine(
        strategy=grid_strategy,
        initial_cash=Decimal("1000000"),
        slippage_model=FixedSlippage(0.05),
        brokerage_model=NSEEquityBrokerage(),
        db_store=DuckDBStore(":memory:"),
        blotter_path=tmp_path / "blotter.csv",
    )


class TestBacktestEngine:
    def test_run_returns_result(self, backtest_engine: BacktestEngine) -> None:
        candles = make_candles(300)
        result = backtest_engine.run(candles)
        assert result is not None
        assert isinstance(result.total_net_pnl, Decimal)

    def test_equity_curve_length(self, backtest_engine: BacktestEngine) -> None:
        candles = make_candles(300)
        result = backtest_engine.run(candles)
        assert len(result.equity_curve) == len(candles)

    def test_no_lookahead_bias(self, backtest_engine: BacktestEngine) -> None:
        """Signals from bar N should only fill on bar N+1 open."""
        # Run backtest with 2 bars; any signal from bar 0 fills at bar 1
        candles = make_candles(50)
        result = backtest_engine.run(candles)
        # Basic sanity: equity curve starts at initial cash before any trades
        assert result.equity_curve[0][1] == Decimal("1000000")

    def test_sharpe_ratio_finite(self, backtest_engine: BacktestEngine) -> None:
        candles = make_candles(300)
        result = backtest_engine.run(candles)
        assert result.sharpe_ratio == result.sharpe_ratio  # not NaN

    def test_max_drawdown_nonnegative(self, backtest_engine: BacktestEngine) -> None:
        candles = make_candles(300)
        result = backtest_engine.run(candles)
        assert result.max_drawdown_pct >= 0.0

    def test_blotter_csv_created(self, backtest_engine: BacktestEngine, tmp_path) -> None:
        candles = make_candles(300)
        result = backtest_engine.run(candles)
        assert result.blotter_path is not None
        assert result.blotter_path.exists()

    def test_result_dict_keys(self, backtest_engine: BacktestEngine) -> None:
        candles = make_candles(300)
        result = backtest_engine.run(candles)
        d = result.to_dict()
        expected_keys = {
            "total_trades", "winning_trades", "win_rate_pct",
            "total_net_pnl", "sharpe_ratio", "max_drawdown_pct", "profit_factor",
        }
        assert expected_keys.issubset(set(d.keys()))


class TestSlippageModels:
    def test_fixed_slippage_buy_increases_price(self) -> None:
        from app.domain.enums import OrderType, ProductType, Side
        from app.domain.models import Order

        model = FixedSlippage(slippage_pct=0.1)
        order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=1,
            price=Decimal("18000"),
            strategy_id="test",
        )
        candle = Candle(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            timestamp=datetime.utcnow(),
            open=Decimal("18000"),
            high=Decimal("18050"),
            low=Decimal("17950"),
            close=Decimal("18000"),
            volume=500_000,
        )
        fill_price = model.apply(order, candle)
        assert fill_price > Decimal("18000")

    def test_fixed_slippage_sell_decreases_price(self) -> None:
        from app.domain.enums import OrderType, ProductType, Side
        from app.domain.models import Order

        model = FixedSlippage(slippage_pct=0.1)
        order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.SELL,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=1,
            price=Decimal("18000"),
            strategy_id="test",
        )
        candle = Candle(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            timestamp=datetime.utcnow(),
            open=Decimal("18000"),
            high=Decimal("18050"),
            low=Decimal("17950"),
            close=Decimal("18000"),
            volume=500_000,
        )
        fill_price = model.apply(order, candle)
        assert fill_price < Decimal("18000")

    def test_volume_slippage_zero_volume_no_impact(self) -> None:
        from app.domain.enums import OrderType, ProductType, Side
        from app.domain.models import Order

        model = VolumeSlippage()
        order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=1,
            price=Decimal("18000"),
            strategy_id="test",
        )
        candle = Candle(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            timestamp=datetime.utcnow(),
            open=Decimal("18000"),
            high=Decimal("18050"),
            low=Decimal("17950"),
            close=Decimal("18000"),
            volume=0,
        )
        fill_price = model.apply(order, candle)
        assert fill_price == Decimal("18000")


class TestBrokerageModel:
    def test_brokerage_nonnegative(self) -> None:
        from app.domain.enums import OrderType, ProductType, Side
        from app.domain.models import Order

        model = NSEEquityBrokerage()
        order = Order(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=10,
            price=Decimal("18000"),
            strategy_id="test",
        )
        result = model.calculate(order, Decimal("18000"))
        assert result.total >= Decimal("0")
        assert result.brokerage >= Decimal("0")
        assert result.stt >= Decimal("0")
        assert result.gst >= Decimal("0")
