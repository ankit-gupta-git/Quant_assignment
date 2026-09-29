"""
tests/conftest.py
──────────────────
Shared pytest fixtures used across the test suite.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.enums import Exchange, OrderType, ProductType, Side
from app.domain.models import Candle, Order, StrategyConfig


# ── Candle factory ────────────────────────────────────────────────────────────


def make_candle(
    close: float,
    high: float | None = None,
    low: float | None = None,
    open_: float | None = None,
    volume: int = 100_000,
    ts: datetime | None = None,
    symbol: str = "NIFTY",
) -> Candle:
    """Build a Candle with sensible defaults."""
    c = Decimal(str(close))
    h = Decimal(str(high)) if high is not None else c + Decimal("10")
    l = Decimal(str(low)) if low is not None else c - Decimal("10")
    o = Decimal(str(open_)) if open_ is not None else c
    return Candle(
        symbol=symbol,
        exchange=Exchange.NSE,
        timestamp=ts or datetime.utcnow(),
        open=o,
        high=h,
        low=l,
        close=c,
        volume=volume,
    )


def make_candle_series(prices: list[float], start: datetime | None = None) -> list[Candle]:
    """Build a series of candles from a list of closing prices."""
    base = start or datetime(2023, 1, 1, 9, 15)
    return [
        make_candle(p, ts=base + timedelta(minutes=i))
        for i, p in enumerate(prices)
    ]


@pytest.fixture
def sample_candles() -> list[Candle]:
    """500 candles with a realistic random walk around 18000."""
    import random

    random.seed(99)
    prices: list[float] = []
    price = 18000.0
    for _ in range(500):
        price += random.uniform(-40, 40)
        prices.append(round(price, 2))
    return make_candle_series(prices)


@pytest.fixture
def default_strategy_config() -> StrategyConfig:
    return StrategyConfig(
        strategy_id="test-strategy",
        symbol="NIFTY",
        exchange=Exchange.NSE,
        atr_multiplier=1.5,
        max_positions=5,
        take_profit_multiplier=2.0,
        stop_loss_multiplier=3.0,
        pyramid_enabled=True,
        stop_and_reverse=False,
    )


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
        strategy_id="test-strategy",
    )
