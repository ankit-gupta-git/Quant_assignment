"""
app/strategy/base.py
────────────────────
Abstract base class for all trading strategies.

Design contract:
  * Strategies are stateful objects that receive candles one at a time.
  * They emit zero or more ``Signal`` objects per bar.
  * They must NOT know about order placement — that is the execution engine's
    concern (Separation of Concerns / Clean Architecture).
  * All concrete strategies must implement ``on_candle`` and ``reset``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.domain.enums import StrategyState
from app.domain.models import Candle, Signal, StrategyConfig

if TYPE_CHECKING:
    pass


class BaseStrategy(ABC):
    """
    Abstract strategy.

    Subclasses override ``on_candle`` to compute signals based on the incoming
    bar plus any internal state they maintain (indicator buffers, open grids, etc.)

    Attributes:
        config: Injected ``StrategyConfig`` controlling strategy behaviour.
        state:  Lifecycle state; strategies should check this before emitting
                signals (do not emit when STOPPED or PAUSED).
    """

    def __init__(self, config: StrategyConfig) -> None:
        self.config = config
        self.state: StrategyState = config.state

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def pause(self) -> None:
        """Temporarily pause signal generation (e.g. during market halt)."""
        self.state = StrategyState.PAUSED

    def resume(self) -> None:
        """Resume signal generation."""
        self.state = StrategyState.ACTIVE

    def stop(self) -> None:
        """Permanently stop the strategy (kill switch)."""
        self.state = StrategyState.STOPPED

    @property
    def is_active(self) -> bool:
        return self.state == StrategyState.ACTIVE

    # ── Abstract interface ────────────────────────────────────────────────────

    @abstractmethod
    def on_candle(self, candle: Candle) -> list[Signal]:
        """
        Process a new OHLCV bar and return zero or more trading signals.

        **IMPORTANT**: This method must NEVER look at future bars.
        All state must be updated *after* signal generation.

        Args:
            candle: The current closed bar (past data only).

        Returns:
            A list of ``Signal`` objects.  Return an empty list for HOLD.
        """

    @abstractmethod
    def reset(self) -> None:
        """
        Reset all internal state (buffers, grids, counters, etc.).
        Called before a new backtest run or when the strategy is re-initialised.
        """

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _guard_active(self) -> bool:
        """
        Return True when signals should be emitted.
        Subclasses should call this at the top of ``on_candle``.
        """
        return self.is_active
