"""
app/strategy/grid.py
────────────────────
ATR-based Grid Trading Strategy with pyramiding and stop-and-reverse.

Design
──────
The grid is constructed around a reference price (the mid-price of the first
bar after initialisation).  Levels are spaced ``ATR × atr_multiplier`` apart.

On each new candle:
  1. Update the ATR buffer.
  2. Check if the current price has crossed any grid level.
  3. If a long grid level is hit → ENTER_LONG or PYRAMID_LONG.
  4. If stop-and-reverse is enabled and the opposite level is hit → REVERSE.
  5. Check take-profit / stop-loss distances to emit EXIT signals.

Positions are tracked as a simple list of entry prices.
The average entry price is recomputed after every fill.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.core.logger import get_logger
from app.domain.enums import Exchange, SignalAction
from app.domain.models import Candle, Signal, StrategyConfig
from app.indicators.atr import atr as compute_atr
from app.strategy.base import BaseStrategy

import pandas as pd

log = get_logger(__name__)


@dataclass
class GridLevel:
    """A single price level in the grid."""
    price: Decimal
    side: str  # 'long' | 'short'
    filled: bool = False
    filled_at: Optional[datetime] = None


@dataclass
class GridState:
    """Internal mutable state of the running grid."""
    reference_price: Decimal = Decimal("0")
    grid_spacing: Decimal = Decimal("0")
    levels: list[GridLevel] = field(default_factory=list)
    open_long_entries: list[Decimal] = field(default_factory=list)  # entry prices
    open_short_entries: list[Decimal] = field(default_factory=list)
    average_long_price: Decimal = Decimal("0")
    average_short_price: Decimal = Decimal("0")
    is_initialised: bool = False


class GridStrategy(BaseStrategy):
    """
    ATR-spaced Grid Trading Strategy.

    Parameters (from StrategyConfig):
        atr_multiplier:          Multiplier applied to ATR to get grid spacing.
        max_positions:           Maximum number of open grid positions (position cap).
        take_profit_multiplier:  Take profit = entry_avg ± ATR × this value.
        stop_loss_multiplier:    Stop loss   = entry_avg ∓ ATR × this value.
        pyramid_enabled:         Allow adding to winning positions.
        stop_and_reverse:        Flip position direction when opposite side hit.

    The strategy only emits ``Signal`` objects; actual order placement is
    handled by the execution engine.
    """

    ATR_PERIOD: int = 14
    CANDLE_BUFFER: int = 50  # keep last N candles in memory

    def __init__(self, config: StrategyConfig) -> None:
        super().__init__(config)
        self._candle_buffer: deque[Candle] = deque(maxlen=self.CANDLE_BUFFER)
        self._grid = GridState()
        self._last_atr: Decimal = Decimal("0")

    # ── BaseStrategy interface ────────────────────────────────────────────────

    def on_candle(self, candle: Candle) -> list[Signal]:
        """Process a new bar and return signals."""
        if not self._guard_active():
            return []

        self._candle_buffer.append(candle)

        if len(self._candle_buffer) < self.ATR_PERIOD + 1:
            return []  # not enough data yet

        self._last_atr = self._compute_atr()

        if not self._grid.is_initialised:
            self._initialise_grid(candle)
            return []

        signals: list[Signal] = []
        signals.extend(self._check_entry_signals(candle))
        signals.extend(self._check_exit_signals(candle))
        return signals

    def reset(self) -> None:
        """Reset all state for a new backtest run."""
        self._candle_buffer.clear()
        self._grid = GridState()
        self._last_atr = Decimal("0")
        log.info("grid.reset", strategy_id=self.config.strategy_id)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _compute_atr(self) -> Decimal:
        """Recompute ATR from the current candle buffer."""
        candles = list(self._candle_buffer)
        high = pd.Series([float(c.high) for c in candles])
        low = pd.Series([float(c.low) for c in candles])
        close = pd.Series([float(c.close) for c in candles])
        atr_series = compute_atr(high, low, close, period=self.ATR_PERIOD)
        return Decimal(str(round(atr_series.iloc[-1], 4)))

    def _initialise_grid(self, candle: Candle) -> None:
        """Build the initial grid levels around the current price."""
        ref = candle.mid_price
        spacing = self._last_atr * Decimal(str(self.config.atr_multiplier))

        levels: list[GridLevel] = []
        max_p = self.config.max_positions
        for i in range(1, max_p + 1):
            levels.append(GridLevel(price=ref - spacing * Decimal(str(i)), side="long"))
            levels.append(GridLevel(price=ref + spacing * Decimal(str(i)), side="short"))

        self._grid = GridState(
            reference_price=ref,
            grid_spacing=spacing,
            levels=levels,
            is_initialised=True,
        )
        log.info(
            "grid.initialised",
            strategy_id=self.config.strategy_id,
            ref_price=str(ref),
            spacing=str(spacing),
            levels=len(levels),
        )

    def _check_entry_signals(self, candle: Candle) -> list[Signal]:
        """Check if the candle low/high has crossed any unfilled grid level."""
        signals: list[Signal] = []

        for level in self._grid.levels:
            if level.filled:
                continue

            if level.side == "long":
                long_count = len(self._grid.open_long_entries)
                if long_count >= self.config.max_positions:
                    continue
                # Price dipped to or below this buy level
                if candle.low <= level.price:
                    action = (
                        SignalAction.PYRAMID_LONG
                        if long_count > 0 and self.config.pyramid_enabled
                        else SignalAction.ENTER_LONG
                    )
                    signals.append(self._make_signal(candle, action, level.price))
                    level.filled = True
                    level.filled_at = candle.timestamp
                    self._grid.open_long_entries.append(level.price)
                    self._recalculate_averages()

            else:  # short
                short_count = len(self._grid.open_short_entries)
                if short_count >= self.config.max_positions:
                    continue
                if candle.high >= level.price:
                    if (
                        self.config.stop_and_reverse
                        and len(self._grid.open_long_entries) > 0
                    ):
                        action = SignalAction.REVERSE_TO_SHORT
                        # Close all longs
                        self._grid.open_long_entries.clear()
                    else:
                        action = (
                            SignalAction.PYRAMID_SHORT
                            if short_count > 0 and self.config.pyramid_enabled
                            else SignalAction.ENTER_SHORT
                        )
                    signals.append(self._make_signal(candle, action, level.price))
                    level.filled = True
                    level.filled_at = candle.timestamp
                    self._grid.open_short_entries.append(level.price)
                    self._recalculate_averages()

        return signals

    def _check_exit_signals(self, candle: Candle) -> list[Signal]:
        """Emit take-profit or stop-loss signals when thresholds are breached."""
        signals: list[Signal] = []
        atr = self._last_atr
        tp_mult = Decimal(str(self.config.take_profit_multiplier))
        sl_mult = Decimal(str(self.config.stop_loss_multiplier))

        if self._grid.open_long_entries:
            avg = self._grid.average_long_price
            tp = avg + atr * tp_mult
            sl = avg - atr * sl_mult
            if candle.high >= tp:
                signals.append(self._make_signal(candle, SignalAction.EXIT_LONG, tp))
                self._clear_long_positions()
                self._reset_grid_levels("long")
            elif candle.low <= sl:
                signals.append(self._make_signal(candle, SignalAction.EXIT_LONG, sl))
                self._clear_long_positions()
                self._reset_grid_levels("long")

        if self._grid.open_short_entries:
            avg = self._grid.average_short_price
            tp = avg - atr * tp_mult
            sl = avg + atr * sl_mult
            if candle.low <= tp:
                signals.append(self._make_signal(candle, SignalAction.EXIT_SHORT, tp))
                self._clear_short_positions()
                self._reset_grid_levels("short")
            elif candle.high >= sl:
                signals.append(self._make_signal(candle, SignalAction.EXIT_SHORT, sl))
                self._clear_short_positions()
                self._reset_grid_levels("short")

        return signals

    def _recalculate_averages(self) -> None:
        """Recompute VWAP-style average entry prices."""
        if self._grid.open_long_entries:
            total = sum(self._grid.open_long_entries)
            self._grid.average_long_price = total / Decimal(
                str(len(self._grid.open_long_entries))
            )
        if self._grid.open_short_entries:
            total = sum(self._grid.open_short_entries)
            self._grid.average_short_price = total / Decimal(
                str(len(self._grid.open_short_entries))
            )

    def _clear_long_positions(self) -> None:
        self._grid.open_long_entries.clear()
        self._grid.average_long_price = Decimal("0")

    def _clear_short_positions(self) -> None:
        self._grid.open_short_entries.clear()
        self._grid.average_short_price = Decimal("0")

    def _reset_grid_levels(self, side: str) -> None:
        """Mark all levels of the given side as unfilled so the grid can re-trigger."""
        for level in self._grid.levels:
            if level.side == side:
                level.filled = False
                level.filled_at = None

    def _make_signal(
        self, candle: Candle, action: SignalAction, price: Decimal
    ) -> Signal:
        return Signal(
            strategy_id=self.config.strategy_id,
            symbol=candle.symbol,
            exchange=candle.exchange,
            action=action,
            price=price,
            quantity=1,  # execution engine scales by lot size
            timestamp=candle.timestamp,
            atr=self._last_atr,
            metadata={
                "grid_spacing": str(self._grid.grid_spacing),
                "ref_price": str(self._grid.reference_price),
            },
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def last_atr(self) -> Decimal:
        return self._last_atr

    @property
    def open_long_count(self) -> int:
        return len(self._grid.open_long_entries)

    @property
    def open_short_count(self) -> int:
        return len(self._grid.open_short_entries)
