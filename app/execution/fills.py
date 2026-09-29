"""
app/execution/fills.py
──────────────────────
Fill processor: converts raw Fill events into portfolio P&L updates.

Responsibilities:
  * Accept Fill objects from the broker / order manager.
  * Update Position average price.
  * Compute realised P&L for closing fills.
  * Record completed Trade objects.
  * Emit structured log events for every fill.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.core.logger import get_logger
from app.domain.enums import Side
from app.domain.models import Fill, Portfolio, Position, Trade

log = get_logger(__name__)


class FillProcessor:
    """
    Applies fill events to portfolio positions and records trades.

    Args:
        portfolio: Shared portfolio state (mutated in-place on each fill).
    """

    def __init__(self, portfolio: Portfolio) -> None:
        self._portfolio = portfolio
        self._open_trades: dict[str, Position] = {}  # symbol → entry position

    def process(self, fill: Fill) -> Decimal:
        """
        Apply a fill to the portfolio and return the realised P&L
        (zero for opening fills).

        Args:
            fill: The execution fill event.

        Returns:
            Realised P&L for this fill (Decimal).
        """
        key = f"{fill.symbol}:{fill.exchange.value}"
        existing = self._portfolio.positions.get(key)

        if existing is None:
            # Opening fill → create new position
            self._open_new_position(key, fill)
            realised = Decimal("0")
        elif existing.side == fill.side:
            # Adding to existing position (pyramiding)
            self._add_to_position(existing, fill)
            realised = Decimal("0")
        else:
            # Closing fill → compute P&L
            realised = self._close_position(key, existing, fill)

        log.info(
            "fill.processed",
            fill_id=fill.fill_id,
            symbol=fill.symbol,
            side=fill.side.value,
            qty=fill.quantity,
            price=str(fill.price),
            realised_pnl=str(realised),
        )
        return realised

    # ── Private helpers ───────────────────────────────────────────────────────

    def _open_new_position(self, key: str, fill: Fill) -> None:
        pos = Position(
            symbol=fill.symbol,
            exchange=fill.exchange,
            side=fill.side,
            quantity=fill.quantity,
            average_price=fill.price,
            strategy_id="",
            opened_at=fill.timestamp,
        )
        self._portfolio.positions[key] = pos

    def _add_to_position(self, pos: Position, fill: Fill) -> None:
        """VWAP-style average price update."""
        old_qty = Decimal(str(pos.quantity))
        add_qty = Decimal(str(fill.quantity))
        total_qty = old_qty + add_qty
        pos.average_price = (pos.average_price * old_qty + fill.price * add_qty) / total_qty
        pos.quantity += fill.quantity
        pos.last_updated = fill.timestamp

    def _close_position(
        self, key: str, pos: Position, fill: Fill
    ) -> Decimal:
        """
        Compute realised P&L, update portfolio, record the trade.
        """
        close_qty = Decimal(str(min(fill.quantity, pos.quantity)))
        if pos.side == Side.BUY:
            gross_pnl = (fill.price - pos.average_price) * close_qty
        else:
            gross_pnl = (pos.average_price - fill.price) * close_qty

        net_pnl = gross_pnl - fill.net_cost + (fill.price * close_qty)

        trade = Trade(
            symbol=fill.symbol,
            exchange=fill.exchange,
            side=pos.side,
            quantity=int(close_qty),
            entry_price=pos.average_price,
            exit_price=fill.price,
            entry_time=pos.opened_at,
            exit_time=fill.timestamp,
            strategy_id=pos.strategy_id,
            gross_pnl=gross_pnl,
            charges=fill.brokerage + fill.stt + fill.transaction_charges + fill.gst,
            net_pnl=gross_pnl - (fill.brokerage + fill.stt + fill.transaction_charges + fill.gst),
        )
        self._portfolio.trades.append(trade)
        self._portfolio.daily_realised_pnl += trade.net_pnl

        if trade.net_pnl < Decimal("0"):
            self._portfolio.consecutive_losses += 1
        else:
            self._portfolio.consecutive_losses = 0

        # Update or remove position
        remaining = pos.quantity - int(close_qty)
        if remaining <= 0:
            del self._portfolio.positions[key]
        else:
            pos.quantity = remaining
            pos.realised_pnl += trade.net_pnl
            pos.last_updated = fill.timestamp

        self._portfolio.update_peak()
        return trade.net_pnl
