"""
app/monitoring/trade_blotter.py
────────────────────────────────
Trade blotter: maintains an in-memory ledger of all completed trades
and can export it to CSV for post-trade analysis.

The blotter is the single source of truth for the P&L dashboard.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.core.logger import get_logger
from app.domain.models import Trade

log = get_logger(__name__)


@dataclass
class BlotterRow:
    """A single row in the trade blotter."""

    timestamp: datetime
    trade_id: str
    symbol: str
    exchange: str
    side: str
    quantity: int
    entry_price: Decimal
    exit_price: Decimal
    gross_pnl: Decimal
    charges: Decimal
    net_pnl: Decimal
    strategy_id: str
    reason: str
    running_pnl: Decimal = Decimal("0")


class TradeBlotter:
    """
    Append-only, in-memory trade ledger.

    Args:
        export_path: Where to write the blotter CSV.
    """

    def __init__(self, export_path: Path = Path("data/blotter.csv")) -> None:
        self._export_path = export_path
        self._rows: list[BlotterRow] = []
        self._running_pnl: Decimal = Decimal("0")

    # ── Public interface ──────────────────────────────────────────────────────

    def record(self, trade: Trade) -> None:
        """Add a completed trade to the blotter."""
        self._running_pnl += trade.net_pnl
        row = BlotterRow(
            timestamp=trade.exit_time,
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            exchange=trade.exchange.value,
            side=trade.side.value,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            gross_pnl=trade.gross_pnl,
            charges=trade.charges,
            net_pnl=trade.net_pnl,
            strategy_id=trade.strategy_id,
            reason=trade.reason,
            running_pnl=self._running_pnl,
        )
        self._rows.append(row)
        log.info(
            "blotter.trade_recorded",
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            net_pnl=str(trade.net_pnl),
            running_pnl=str(self._running_pnl),
        )

    def export_csv(self) -> Path:
        """Write all blotter rows to a CSV file and return the path."""
        self._export_path.parent.mkdir(parents=True, exist_ok=True)
        with self._export_path.open("w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "trade_id",
                    "symbol",
                    "exchange",
                    "side",
                    "quantity",
                    "entry_price",
                    "exit_price",
                    "gross_pnl",
                    "charges",
                    "net_pnl",
                    "strategy_id",
                    "reason",
                    "running_pnl",
                ],
            )
            writer.writeheader()
            for row in self._rows:
                writer.writerow(
                    {
                        "timestamp": row.timestamp.isoformat(),
                        "trade_id": row.trade_id,
                        "symbol": row.symbol,
                        "exchange": row.exchange,
                        "side": row.side,
                        "quantity": row.quantity,
                        "entry_price": str(row.entry_price),
                        "exit_price": str(row.exit_price),
                        "gross_pnl": str(row.gross_pnl),
                        "charges": str(row.charges),
                        "net_pnl": str(row.net_pnl),
                        "strategy_id": row.strategy_id,
                        "reason": row.reason,
                        "running_pnl": str(row.running_pnl),
                    }
                )
        log.info("blotter.csv.exported", path=str(self._export_path), rows=len(self._rows))
        return self._export_path

    # ── Statistics ────────────────────────────────────────────────────────────

    @property
    def total_trades(self) -> int:
        return len(self._rows)

    @property
    def winning_trades(self) -> int:
        return sum(1 for r in self._rows if r.net_pnl > Decimal("0"))

    @property
    def losing_trades(self) -> int:
        return sum(1 for r in self._rows if r.net_pnl < Decimal("0"))

    @property
    def win_rate(self) -> float:
        if not self._rows:
            return 0.0
        return self.winning_trades / self.total_trades * 100

    @property
    def total_net_pnl(self) -> Decimal:
        return self._running_pnl

    @property
    def total_gross_pnl(self) -> Decimal:
        return sum(r.gross_pnl for r in self._rows)  # type: ignore[return-value]

    @property
    def total_charges(self) -> Decimal:
        return sum(r.charges for r in self._rows)  # type: ignore[return-value]

    @property
    def average_win(self) -> Decimal:
        wins = [r.net_pnl for r in self._rows if r.net_pnl > Decimal("0")]
        if not wins:
            return Decimal("0")
        return sum(wins) / Decimal(str(len(wins)))  # type: ignore[arg-type]

    @property
    def average_loss(self) -> Decimal:
        losses = [r.net_pnl for r in self._rows if r.net_pnl < Decimal("0")]
        if not losses:
            return Decimal("0")
        return sum(losses) / Decimal(str(len(losses)))  # type: ignore[arg-type]

    @property
    def profit_factor(self) -> float:
        gross_wins = sum(r.net_pnl for r in self._rows if r.net_pnl > Decimal("0"))
        gross_losses = abs(sum(r.net_pnl for r in self._rows if r.net_pnl < Decimal("0")))
        if gross_losses == Decimal("0"):
            return float("inf")
        return float(gross_wins / gross_losses)

    def summary(self) -> dict:
        """Return a dict of key blotter statistics."""
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate_pct": round(self.win_rate, 2),
            "total_net_pnl": str(self.total_net_pnl),
            "total_gross_pnl": str(self.total_gross_pnl),
            "total_charges": str(self.total_charges),
            "average_win": str(self.average_win),
            "average_loss": str(self.average_loss),
            "profit_factor": round(self.profit_factor, 3),
        }
