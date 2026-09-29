"""
app/risk/pyramiding.py
──────────────────────
Pyramiding risk controller.

Controls how many layers can be added to a winning position.
Each pyramid layer requires:
  1. The position is profitable by at least ``min_profit_atr`` ATR units.
  2. The total number of layers has not exceeded ``max_layers``.
  3. Each new layer is smaller than the previous (scale-in sizing).

Position sizing per layer:
    layer_1_qty = base_qty
    layer_2_qty = base_qty * size_factor
    layer_3_qty = base_qty * size_factor²
    ...

This implements a conservative pyramiding approach that limits risk as more
layers are added.
"""
from __future__ import annotations

from decimal import Decimal

from app.core.logger import get_logger
from app.domain.enums import AlertLevel, RiskEvent, Side
from app.domain.models import Position, RiskAlert

log = get_logger(__name__)


class PyramidingController:
    """
    Controls position pyramiding (scale-in) behaviour.

    Args:
        max_layers:       Maximum pyramid layers per position.
        min_profit_atr:   Minimum ATR-based profit before adding a layer.
        size_factor:      Scaling factor for each successive layer (< 1.0).
        base_quantity:    Base lot quantity for the first layer.
    """

    def __init__(
        self,
        max_layers: int = 3,
        min_profit_atr: float = 1.0,
        size_factor: float = 0.5,
        base_quantity: int = 1,
    ) -> None:
        if max_layers < 1:
            raise ValueError("max_layers must be >= 1")
        if not (0.0 < size_factor < 1.0):
            raise ValueError("size_factor must be in (0, 1)")
        self.max_layers = max_layers
        self.min_profit_atr = min_profit_atr
        self.size_factor = size_factor
        self.base_quantity = base_quantity
        self._layers: dict[str, int] = {}  # symbol → current layer count

    # ── Public interface ──────────────────────────────────────────────────────

    def can_pyramid(
        self,
        position: Position,
        current_price: Decimal,
        atr: Decimal,
    ) -> tuple[bool, str]:
        """
        Determine whether a new pyramid layer can be added.

        Args:
            position:      The existing open position.
            current_price: Latest market price.
            atr:           Current ATR value.

        Returns:
            Tuple of (allowed: bool, reason: str).
        """
        layers = self._layers.get(position.symbol, 0)

        if layers >= self.max_layers:
            return False, f"Max layers ({self.max_layers}) reached"

        profit = self._profit_in_atr(position, current_price, atr)
        if profit < self.min_profit_atr:
            return False, (
                f"Insufficient profit ({profit:.2f} ATR) < required ({self.min_profit_atr} ATR)"
            )

        return True, "ok"

    def add_layer(self, symbol: str) -> int:
        """
        Record that a new pyramid layer has been added.

        Returns:
            Quantity to trade for this layer.
        """
        current = self._layers.get(symbol, 0)
        self._layers[symbol] = current + 1
        qty = self._layer_quantity(current + 1)
        log.info(
            "pyramid.layer_added",
            symbol=symbol,
            layer=current + 1,
            quantity=qty,
        )
        return qty

    def close_position(self, symbol: str) -> None:
        """Reset layer counter when position is closed."""
        self._layers.pop(symbol, None)

    def layer_count(self, symbol: str) -> int:
        """Return the number of active pyramid layers for a symbol."""
        return self._layers.get(symbol, 0)

    def layer_quantity(self, symbol: str) -> int:
        """Return the quantity for the next pyramid layer."""
        layer = self._layers.get(symbol, 0) + 1
        return self._layer_quantity(layer)

    def validate(
        self,
        position: Position,
        current_price: Decimal,
        atr: Decimal,
    ) -> list[RiskAlert]:
        """
        Validate a prospective pyramid trade and return any alerts.

        Returns an empty list if the pyramid trade is permitted.
        """
        allowed, reason = self.can_pyramid(position, current_price, atr)
        if not allowed:
            return [
                RiskAlert(
                    event=RiskEvent.POSITION_CAP,
                    message=f"Pyramid blocked: {reason}",
                    level=AlertLevel.WARNING,
                    metadata={
                        "symbol": position.symbol,
                        "reason": reason,
                        "layers": self.layer_count(position.symbol),
                    },
                )
            ]
        return []

    # ── Private helpers ───────────────────────────────────────────────────────

    def _profit_in_atr(
        self, position: Position, current_price: Decimal, atr: Decimal
    ) -> float:
        """Calculate how many ATR units the position is in profit."""
        if atr == Decimal("0"):
            return 0.0
        if position.side == Side.BUY:
            raw_profit = current_price - position.average_price
        else:
            raw_profit = position.average_price - current_price
        return float(raw_profit / atr)

    def _layer_quantity(self, layer_number: int) -> int:
        """
        Compute quantity for a given layer using geometric decay.

        Layer 1: base_quantity
        Layer 2: base_quantity × size_factor
        Layer 3: base_quantity × size_factor²
        """
        qty = self.base_quantity * (self.size_factor ** (layer_number - 1))
        return max(1, round(qty))
