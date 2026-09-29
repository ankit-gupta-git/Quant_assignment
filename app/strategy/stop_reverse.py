"""
app/strategy/stop_reverse.py
─────────────────────────────
Stop-and-Reverse (SAR) Strategy.

Always-in-market strategy that flips from long to short (or vice versa)
when the ATR-based trailing stop is breached.

Logic:
  1. On the first bar after initialisation, enter LONG.
  2. Maintain a trailing stop at ``entry - ATR × multiplier``.
  3. When price crosses the trailing stop:
     a. Exit current position.
     b. Immediately enter the opposite direction.
  4. Repeat.

This creates a continuous, self-reversing position.
"""
from __future__ import annotations

from collections import deque
from decimal import Decimal
from typing import Optional

import pandas as pd

from app.core.logger import get_logger
from app.domain.enums import SignalAction
from app.domain.models import Candle, Signal, StrategyConfig
from app.indicators.atr import atr as compute_atr
from app.strategy.base import BaseStrategy

log = get_logger(__name__)


class StopAndReverseStrategy(BaseStrategy):
    """
    ATR trailing stop-and-reverse strategy.

    Attributes:
        config:          Injected StrategyConfig.
        _position_side:  Current position direction ('long' | 'short' | None).
        _entry_price:    Entry price of the current position.
        _trailing_stop:  Current trailing stop level.
        _candle_buffer:  Rolling window of recent candles for ATR calculation.
        _last_atr:       Most recent ATR value.
    """

    ATR_PERIOD: int = 14
    BUFFER_SIZE: int = 60

    def __init__(self, config: StrategyConfig) -> None:
        super().__init__(config)
        self._candle_buffer: deque[Candle] = deque(maxlen=self.BUFFER_SIZE)
        self._position_side: Optional[str] = None  # 'long' | 'short'
        self._entry_price: Decimal = Decimal("0")
        self._trailing_stop: Decimal = Decimal("0")
        self._last_atr: Decimal = Decimal("0")
        self._highest_since_entry: Decimal = Decimal("0")
        self._lowest_since_entry: Decimal = Decimal("0")

    # ── BaseStrategy interface ────────────────────────────────────────────────

    def on_candle(self, candle: Candle) -> list[Signal]:
        if not self._guard_active():
            return []

        self._candle_buffer.append(candle)

        if len(self._candle_buffer) < self.ATR_PERIOD + 1:
            return []

        self._last_atr = self._compute_atr()
        signals: list[Signal] = []

        if self._position_side is None:
            # Initialise: enter long on first valid bar
            signals.append(self._enter_long(candle))
        elif self._position_side == "long":
            signals.extend(self._manage_long(candle))
        else:
            signals.extend(self._manage_short(candle))

        return signals

    def reset(self) -> None:
        self._candle_buffer.clear()
        self._position_side = None
        self._entry_price = Decimal("0")
        self._trailing_stop = Decimal("0")
        self._last_atr = Decimal("0")
        log.info("sar.reset", strategy_id=self.config.strategy_id)

    # ── Long management ───────────────────────────────────────────────────────

    def _manage_long(self, candle: Candle) -> list[Signal]:
        signals: list[Signal] = []

        # Update trailing high-water mark
        if candle.high > self._highest_since_entry:
            self._highest_since_entry = candle.high
            # Ratchet trailing stop up
            new_stop = self._highest_since_entry - self._last_atr * Decimal(
                str(self.config.atr_multiplier)
            )
            if new_stop > self._trailing_stop:
                self._trailing_stop = new_stop

        if candle.low <= self._trailing_stop:
            log.info(
                "sar.reverse_to_short",
                strategy_id=self.config.strategy_id,
                stop=str(self._trailing_stop),
                price=str(candle.close),
            )
            signals.append(
                self._make_signal(candle, SignalAction.REVERSE_TO_SHORT, self._trailing_stop)
            )
            signals.append(self._enter_short(candle))

        return signals

    # ── Short management ──────────────────────────────────────────────────────

    def _manage_short(self, candle: Candle) -> list[Signal]:
        signals: list[Signal] = []

        if candle.low < self._lowest_since_entry:
            self._lowest_since_entry = candle.low
            new_stop = self._lowest_since_entry + self._last_atr * Decimal(
                str(self.config.atr_multiplier)
            )
            if new_stop < self._trailing_stop:
                self._trailing_stop = new_stop

        if candle.high >= self._trailing_stop:
            log.info(
                "sar.reverse_to_long",
                strategy_id=self.config.strategy_id,
                stop=str(self._trailing_stop),
                price=str(candle.close),
            )
            signals.append(
                self._make_signal(candle, SignalAction.REVERSE_TO_LONG, self._trailing_stop)
            )
            signals.append(self._enter_long(candle))

        return signals

    # ── Entry helpers ─────────────────────────────────────────────────────────

    def _enter_long(self, candle: Candle) -> Signal:
        self._position_side = "long"
        self._entry_price = candle.close
        self._highest_since_entry = candle.high
        self._trailing_stop = candle.close - self._last_atr * Decimal(
            str(self.config.atr_multiplier)
        )
        return self._make_signal(candle, SignalAction.ENTER_LONG, candle.close)

    def _enter_short(self, candle: Candle) -> Signal:
        self._position_side = "short"
        self._entry_price = candle.close
        self._lowest_since_entry = candle.low
        self._trailing_stop = candle.close + self._last_atr * Decimal(
            str(self.config.atr_multiplier)
        )
        return self._make_signal(candle, SignalAction.ENTER_SHORT, candle.close)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _compute_atr(self) -> Decimal:
        candles = list(self._candle_buffer)
        h = pd.Series([float(c.high) for c in candles])
        lo = pd.Series([float(c.low) for c in candles])
        cl = pd.Series([float(c.close) for c in candles])
        series = compute_atr(h, lo, cl, period=self.ATR_PERIOD)
        return Decimal(str(round(series.iloc[-1], 4)))

    def _make_signal(
        self, candle: Candle, action: SignalAction, price: Decimal
    ) -> Signal:
        return Signal(
            strategy_id=self.config.strategy_id,
            symbol=candle.symbol,
            exchange=candle.exchange,
            action=action,
            price=price,
            quantity=1,
            timestamp=candle.timestamp,
            atr=self._last_atr,
            metadata={
                "trailing_stop": str(self._trailing_stop),
                "position_side": str(self._position_side),
            },
        )

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def position_side(self) -> Optional[str]:
        return self._position_side

    @property
    def trailing_stop(self) -> Decimal:
        return self._trailing_stop
