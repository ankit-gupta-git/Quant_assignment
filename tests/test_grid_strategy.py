"""
tests/test_grid_strategy.py
────────────────────────────
Unit tests for the Grid strategy and stop-and-reverse.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.enums import Exchange, SignalAction
from app.domain.models import Candle, StrategyConfig
from app.strategy.grid import GridStrategy


def make_candle(
    close: float,
    high: float | None = None,
    low: float | None = None,
    ts: datetime | None = None,
) -> Candle:
    c = Decimal(str(close))
    h = Decimal(str(high)) if high is not None else c + Decimal("20")
    l = Decimal(str(low)) if low is not None else c - Decimal("20")
    return Candle(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        timestamp=ts or datetime.utcnow(),
        open=c,
        high=h,
        low=l,
        close=c,
        volume=500_000,
    )


def warmup_candles(n: int = 20, base: float = 18000.0) -> list[Candle]:
    """Generate n candles to satisfy ATR warm-up period."""
    base_ts = datetime(2023, 1, 1, 9, 15)
    candles = []
    import random
    random.seed(12)
    price = base
    for i in range(n):
        price += random.uniform(-30, 30)
        candles.append(
            make_candle(
                close=round(price, 2),
                ts=base_ts + timedelta(minutes=i),
            )
        )
    return candles


@pytest.fixture
def grid_strategy() -> GridStrategy:
    config = StrategyConfig(
        strategy_id="test-grid",
        symbol="NIFTY",
        exchange=Exchange.NSE,
        atr_multiplier=1.0,
        max_positions=5,
        take_profit_multiplier=3.0,
        stop_loss_multiplier=5.0,
        pyramid_enabled=True,
        stop_and_reverse=False,
    )
    return GridStrategy(config)


class TestGridStrategyInitialisation:
    def test_no_signals_before_warmup(self, grid_strategy: GridStrategy) -> None:
        """Strategy should not emit signals until ATR buffer is full."""
        candles = warmup_candles(10)  # fewer than ATR period
        signals = []
        for c in candles:
            signals.extend(grid_strategy.on_candle(c))
        assert signals == []

    def test_grid_initialises_after_warmup(self, grid_strategy: GridStrategy) -> None:
        """Grid should be initialised after enough candles."""
        candles = warmup_candles(20)
        for c in candles:
            grid_strategy.on_candle(c)
        assert grid_strategy._grid.is_initialised

    def test_reset_clears_state(self, grid_strategy: GridStrategy) -> None:
        """reset() should clear all internal state."""
        for c in warmup_candles(20):
            grid_strategy.on_candle(c)
        grid_strategy.reset()
        assert not grid_strategy._grid.is_initialised
        assert grid_strategy.open_long_count == 0


class TestGridEntrySignals:
    def test_long_entry_on_price_dip(self, grid_strategy: GridStrategy) -> None:
        """A candle whose low reaches a grid level should emit ENTER_LONG."""
        candles = warmup_candles(20)
        for c in candles:
            grid_strategy.on_candle(c)

        ref = grid_strategy._grid.reference_price
        spacing = grid_strategy._grid.grid_spacing
        # Force price to touch the first long level
        trigger_price = ref - spacing
        base_ts = datetime(2023, 1, 2, 9, 15)
        trigger_candle = make_candle(
            close=float(trigger_price),
            low=float(trigger_price) - 10,
            ts=base_ts,
        )
        signals = grid_strategy.on_candle(trigger_candle)
        enter_long = [s for s in signals if s.action == SignalAction.ENTER_LONG]
        assert len(enter_long) >= 1

    def test_pyramid_on_subsequent_level(self, grid_strategy: GridStrategy) -> None:
        """After first entry, hitting a lower level emits PYRAMID_LONG."""
        candles = warmup_candles(20)
        for c in candles:
            grid_strategy.on_candle(c)

        ref = grid_strategy._grid.reference_price
        spacing = grid_strategy._grid.grid_spacing
        base_ts = datetime(2023, 1, 2, 9, 15)

        # First level
        c1 = make_candle(float(ref - spacing), low=float(ref - spacing) - 1, ts=base_ts)
        grid_strategy.on_candle(c1)

        # Second level
        c2 = make_candle(
            float(ref - spacing * 2),
            low=float(ref - spacing * 2) - 1,
            ts=base_ts + timedelta(minutes=1),
        )
        signals = grid_strategy.on_candle(c2)
        pyramid = [s for s in signals if s.action == SignalAction.PYRAMID_LONG]
        assert len(pyramid) >= 1

    def test_max_positions_cap(self, grid_strategy: GridStrategy) -> None:
        """Strategy should not open more positions than max_positions."""
        candles = warmup_candles(20)
        for c in candles:
            grid_strategy.on_candle(c)

        ref = grid_strategy._grid.reference_price
        spacing = grid_strategy._grid.grid_spacing
        base_ts = datetime(2023, 1, 2, 9, 15)

        for i in range(1, 10):  # try to fill 9 levels
            p = float(ref - spacing * i)
            c = make_candle(p, low=p - 1, ts=base_ts + timedelta(minutes=i))
            grid_strategy.on_candle(c)

        assert grid_strategy.open_long_count <= grid_strategy.config.max_positions


class TestGridExitSignals:
    def test_take_profit_closes_longs(self) -> None:
        """Price rising beyond TP level should emit EXIT_LONG."""
        config = StrategyConfig(
            strategy_id="test-grid-tp",
            symbol="NIFTY",
            exchange=Exchange.NSE,
            atr_multiplier=2.0,
            max_positions=5,
            take_profit_multiplier=2.0,
            stop_loss_multiplier=2.0,
            pyramid_enabled=True,
            stop_and_reverse=False,
        )
        strategy = GridStrategy(config)
        base_ts = datetime(2023, 1, 1, 9, 15)
        # Warmup candles with tight range around 18000
        for i in range(16):
            strategy.on_candle(make_candle(18000.0, high=18002.0, low=17998.0, ts=base_ts + timedelta(minutes=i)))

        # Open long at lower level
        strategy.on_candle(make_candle(17980.0, high=17982.0, low=17978.0, ts=base_ts + timedelta(minutes=17)))
        assert strategy.open_long_count >= 1

        # Push price strongly above TP
        signals = strategy.on_candle(make_candle(18200.0, high=18250.0, low=18190.0, ts=base_ts + timedelta(minutes=18)))
        exits = [s for s in signals if s.action == SignalAction.EXIT_LONG]
        assert len(exits) >= 1
        assert strategy.open_long_count == 0

    def test_stop_loss_closes_longs(self) -> None:
        """Price falling beyond SL level should emit EXIT_LONG."""
        config = StrategyConfig(
            strategy_id="test-grid-sl",
            symbol="NIFTY",
            exchange=Exchange.NSE,
            atr_multiplier=2.0,
            max_positions=5,
            take_profit_multiplier=2.0,
            stop_loss_multiplier=2.0,
            pyramid_enabled=True,
            stop_and_reverse=False,
        )
        strategy = GridStrategy(config)
        base_ts = datetime(2023, 1, 1, 9, 15)
        # Warmup
        for i in range(16):
            strategy.on_candle(make_candle(18000.0, high=18002.0, low=17998.0, ts=base_ts + timedelta(minutes=i)))

        # Open long
        strategy.on_candle(make_candle(17980.0, high=17982.0, low=17978.0, ts=base_ts + timedelta(minutes=17)))
        assert strategy.open_long_count >= 1

        # Drop price strongly below SL
        signals = strategy.on_candle(make_candle(17500.0, high=17510.0, low=17400.0, ts=base_ts + timedelta(minutes=18)))
        exits = [s for s in signals if s.action == SignalAction.EXIT_LONG]
        assert len(exits) >= 1
        assert strategy.open_long_count == 0


class TestStopAndReverse:
    def test_reverse_to_short_on_opposite_level(self) -> None:
        """With stop_and_reverse=True, hitting a short level flips from long to short."""
        config = StrategyConfig(
            strategy_id="sar-test",
            symbol="NIFTY",
            exchange=Exchange.NSE,
            atr_multiplier=2.0,
            max_positions=5,
            take_profit_multiplier=5.0,
            stop_loss_multiplier=5.0,
            pyramid_enabled=True,
            stop_and_reverse=True,
        )
        strategy = GridStrategy(config)
        base_ts = datetime(2023, 1, 1, 9, 15)
        # Warmup with small range so no grid level triggers
        for i in range(16):
            strategy.on_candle(make_candle(18000.0, high=18002.0, low=17998.0, ts=base_ts + timedelta(minutes=i)))

        # Open a long at 17980 (below 18000 - 20)
        s1 = strategy.on_candle(make_candle(17980.0, high=17982.0, low=17978.0, ts=base_ts + timedelta(minutes=17)))
        assert strategy.open_long_count >= 1

        # Trigger short level at 18025 (above 18000 + 20) -> reverses to short
        signals = strategy.on_candle(make_candle(18025.0, high=18030.0, low=18020.0, ts=base_ts + timedelta(minutes=18)))
        reverses = [s for s in signals if s.action == SignalAction.REVERSE_TO_SHORT]
        assert len(reverses) >= 1
        assert strategy.open_long_count == 0
        assert strategy.open_short_count >= 1
