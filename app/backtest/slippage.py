"""
app/backtest/slippage.py
─────────────────────────
Slippage models for backtest execution simulation.

Two models are provided:
  1. ``FixedSlippage``   – fixed percentage of price per trade.
  2. ``VolumeSlippage``  – scales with order size relative to bar volume
                           (market-impact model).

Both models implement the ``SlippageModel`` protocol so they can be swapped
without changing the backtest engine.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Protocol

from app.domain.enums import Side
from app.domain.models import Candle, Order


class SlippageModel(Protocol):
    """Protocol interface for slippage models."""

    def apply(self, order: Order, candle: Candle) -> Decimal:
        """
        Return the adjusted fill price after slippage.

        Args:
            order:  The order being filled.
            candle: The current bar (used for volume / price data).

        Returns:
            Fill price including slippage.
        """
        ...


class FixedSlippage:
    """
    Fixed percentage slippage model.

    Slippage is added to buys and subtracted from sells.

    Args:
        slippage_pct: Slippage as a percentage (e.g. 0.05 = 0.05%).
    """

    def __init__(self, slippage_pct: float = 0.05) -> None:
        if slippage_pct < 0:
            raise ValueError("slippage_pct cannot be negative")
        self._factor = Decimal(str(slippage_pct / 100.0))

    def apply(self, order: Order, candle: Candle) -> Decimal:
        base = order.price if order.price > Decimal("0") else candle.close
        slip = base * self._factor
        if order.side == Side.BUY:
            return base + slip
        return base - slip


class VolumeSlippage:
    """
    Volume-impact slippage model (square-root market impact).

    Slippage increases with the square root of order size / bar volume ratio.
    This approximates the Almgren-Chriss market impact model.

    Args:
        impact_factor: Scaling coefficient (typical range 0.1 – 0.5).
        max_pct:       Maximum slippage cap as a percentage.
    """

    def __init__(self, impact_factor: float = 0.1, max_pct: float = 1.0) -> None:
        self.impact_factor = impact_factor
        self.max_pct = max_pct

    def apply(self, order: Order, candle: Candle) -> Decimal:
        import math

        base = order.price if order.price > Decimal("0") else candle.close
        if candle.volume == 0:
            return base  # no volume data → no impact

        participation = order.quantity / candle.volume
        impact_pct = self.impact_factor * math.sqrt(participation)
        impact_pct = min(impact_pct, self.max_pct / 100.0)

        slip = base * Decimal(str(impact_pct))
        if order.side == Side.BUY:
            return base + slip
        return base - slip
