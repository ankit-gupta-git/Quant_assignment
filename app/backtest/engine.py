"""
app/backtest/engine.py
───────────────────────
Bar-accurate backtesting engine.

Design
──────
The engine iterates over OHLCV candles **one bar at a time** and feeds
each bar to the strategy.  Signals are converted to orders and filled
on the *next* bar's open to avoid look-ahead bias.

Fill pipeline
─────────────
1. strategy.on_candle(candle) → signals
2. For each signal → create Order
3. On next bar: fill at open ± slippage
4. Apply brokerage model (NSE: brokerage + STT + CTT + transaction charges + GST)
5. Update Portfolio
6. Record Trade in blotter and DuckDB

Metrics returned
────────────────
* Equity curve (list of (timestamp, equity) tuples)
* Win rate, Sharpe ratio, Max drawdown, Profit factor
* Blotter CSV path
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

from app.backtest.brokerage import BrokerageModel, NSEEquityBrokerage
from app.backtest.slippage import FixedSlippage, SlippageModel
from app.core.logger import get_logger
from app.domain.enums import Exchange, OrderStatus, OrderType, ProductType, Side, SignalAction
from app.domain.models import (
    Candle,
    Fill,
    Order,
    Portfolio,
    Position,
    Signal,
    StrategyConfig,
    Trade,
)
from app.monitoring.trade_blotter import TradeBlotter
from app.storage.duckdb_store import DuckDBStore
from app.strategy.base import BaseStrategy

log = get_logger(__name__)


@dataclass
class BacktestResult:
    """Aggregated results from a single backtest run."""

    equity_curve: list[tuple[datetime, Decimal]] = field(default_factory=list)
    trades: list[Trade] = field(default_factory=list)
    total_net_pnl: Decimal = Decimal("0")
    total_gross_pnl: Decimal = Decimal("0")
    total_charges: Decimal = Decimal("0")
    win_rate: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    blotter_path: Optional[Path] = None

    def to_dict(self) -> dict:
        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "win_rate_pct": round(self.win_rate, 2),
            "total_net_pnl": str(self.total_net_pnl),
            "total_gross_pnl": str(self.total_gross_pnl),
            "total_charges": str(self.total_charges),
            "sharpe_ratio": round(self.sharpe_ratio, 4),
            "max_drawdown_pct": round(self.max_drawdown_pct, 2),
            "profit_factor": round(self.profit_factor, 3),
            "blotter_path": str(self.blotter_path) if self.blotter_path else None,
        }


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Args:
        strategy:       Configured strategy instance.
        initial_cash:   Starting capital in INR.
        slippage_model: Slippage implementation (default: FixedSlippage 0.05%).
        brokerage_model:Brokerage + charges model.
        db_store:       DuckDB store (use ``:memory:`` for isolation).
        blotter_path:   Where to export the blotter CSV.
        lot_size:       Units per signal quantity (1 for equity, N for F&O).
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        initial_cash: Decimal = Decimal("1_000_000"),
        slippage_model: Optional[SlippageModel] = None,
        brokerage_model: Optional[BrokerageModel] = None,
        db_store: Optional[DuckDBStore] = None,
        blotter_path: Path = Path("data/blotter.csv"),
        lot_size: int = 1,
    ) -> None:
        self._strategy = strategy
        self._portfolio = Portfolio(cash=initial_cash, peak_equity=initial_cash)
        self._slippage = slippage_model or FixedSlippage(slippage_pct=0.05)
        self._brokerage = brokerage_model or NSEEquityBrokerage()
        self._store = db_store or DuckDBStore(":memory:")
        self._blotter = TradeBlotter(export_path=blotter_path)
        self._lot_size = lot_size

        # Pending orders waiting for the next bar's open to fill
        self._pending_orders: list[Order] = []
        # Track open positions keyed by symbol+side for simple round-trip matching
        self._open_entries: dict[str, list[tuple[Decimal, datetime, str]]] = {}
        # Equity curve
        self._equity_curve: list[tuple[datetime, Decimal]] = []

    # ── Main entry point ──────────────────────────────────────────────────────

    def run(self, candles: list[Candle]) -> BacktestResult:
        """
        Run the strategy over a list of candles and return results.

        Lookahead bias prevention: signals from bar N are filled at bar N+1 open.
        """
        self._strategy.reset()
        log.info(
            "backtest.start",
            strategy=self._strategy.config.strategy_id,
            bars=len(candles),
        )

        for i, candle in enumerate(candles):
            # Step 1: Fill any pending orders at this bar's open
            if self._pending_orders:
                self._fill_pending_orders(candle)

            # Step 2: Let the strategy observe this bar
            signals: list[Signal] = self._strategy.on_candle(candle)

            # Step 3: Convert signals to pending orders (filled next bar)
            for signal in signals:
                order = self._signal_to_order(signal, candle)
                self._pending_orders.append(order)
                self._store.upsert_order(order)

            # Step 4: Mark portfolio to market
            for pos in self._portfolio.positions.values():
                pos.mark_to_market(candle.close)
            self._portfolio.update_peak()

            # Record equity curve point
            self._equity_curve.append((candle.timestamp, self._portfolio.equity))

        log.info(
            "backtest.complete",
            strategy=self._strategy.config.strategy_id,
            trades=len(self._portfolio.trades),
        )
        return self._compile_results()

    # ── Order / fill processing ───────────────────────────────────────────────

    def _signal_to_order(self, signal: Signal, candle: Candle) -> Order:
        """Convert a Strategy Signal into an Order domain object."""
        side = (
            Side.BUY
            if signal.action in {
                SignalAction.ENTER_LONG,
                SignalAction.PYRAMID_LONG,
                SignalAction.REVERSE_TO_LONG,
            }
            else Side.SELL
        )
        return Order(
            symbol=signal.symbol,
            exchange=signal.exchange,
            side=side,
            order_type=OrderType.LIMIT,
            product_type=ProductType.MIS,
            quantity=signal.quantity * self._lot_size,
            price=signal.price,
            strategy_id=signal.strategy_id,
            tag=signal.action.value,
        )

    def _fill_pending_orders(self, candle: Candle) -> None:
        """Fill all pending orders at the opening price of the current candle."""
        still_pending: list[Order] = []
        for order in self._pending_orders:
            fill_price = self._slippage.apply(order, candle)
            charges = self._brokerage.calculate(order, fill_price)
            self._execute_fill(order, fill_price, charges, candle.timestamp)
        self._pending_orders = still_pending  # cleared — all filled

    def _execute_fill(
        self,
        order: Order,
        fill_price: Decimal,
        charges: "BrokerageResult",  # type: ignore[name-defined]
        ts: datetime,
    ) -> None:
        """Apply a fill to the portfolio and potentially close a position."""
        order.status = OrderStatus.FILLED
        order.filled_quantity = order.quantity
        order.average_price = fill_price
        order.updated_at = ts
        self._store.upsert_order(order)

        fill = Fill(
            order_id=order.client_order_id,
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=ts,
            brokerage=charges.brokerage,
            stt=charges.stt,
            transaction_charges=charges.transaction_charges,
            gst=charges.gst,
        )
        self._store.insert_fill(fill)

        key = f"{order.symbol}:{order.exchange.value}"

        if order.side == Side.BUY:
            # Open or add to long position
            self._open_entries.setdefault(key, []).append(
                (fill_price, ts, order.client_order_id)
            )
            if key in self._portfolio.positions:
                pos = self._portfolio.positions[key]
                new_qty = pos.quantity + order.quantity
                new_avg = (
                    pos.average_price * Decimal(str(pos.quantity))
                    + fill_price * Decimal(str(order.quantity))
                ) / Decimal(str(new_qty))
                pos.quantity = new_qty
                pos.average_price = new_avg
            else:
                self._portfolio.positions[key] = Position(
                    symbol=order.symbol,
                    exchange=order.exchange,
                    side=Side.BUY,
                    quantity=order.quantity,
                    average_price=fill_price,
                    strategy_id=order.strategy_id,
                )
        else:
            # Close long position (SELL)
            entries = self._open_entries.pop(key, [])
            if entries:
                entry_price, entry_time, _ = entries[-1]
                qty = Decimal(str(order.quantity))
                gross_pnl = (fill_price - entry_price) * qty
                total_charges = fill.net_cost - fill_price * qty
                net_pnl = gross_pnl - abs(total_charges)

                trade = Trade(
                    symbol=order.symbol,
                    exchange=order.exchange,
                    side=Side.BUY,
                    quantity=order.quantity,
                    entry_price=entry_price,
                    exit_price=fill_price,
                    entry_time=entry_time,
                    exit_time=ts,
                    strategy_id=order.strategy_id,
                    gross_pnl=gross_pnl,
                    charges=abs(total_charges),
                    net_pnl=net_pnl,
                    reason=order.tag,
                )
                self._portfolio.trades.append(trade)
                self._portfolio.daily_realised_pnl += net_pnl
                self._portfolio.cash += net_pnl
                if net_pnl < Decimal("0"):
                    self._portfolio.consecutive_losses += 1
                else:
                    self._portfolio.consecutive_losses = 0
                self._blotter.record(trade)
                self._store.insert_trade(trade)

            # Remove or reduce position
            if key in self._portfolio.positions:
                pos = self._portfolio.positions[key]
                if pos.quantity <= order.quantity:
                    del self._portfolio.positions[key]
                else:
                    pos.quantity -= order.quantity

    # ── Results compilation ───────────────────────────────────────────────────

    def _compile_results(self) -> BacktestResult:
        trades = self._portfolio.trades
        blotter_path = self._blotter.export_csv()

        wins = [t for t in trades if t.net_pnl > Decimal("0")]
        total_net = sum(t.net_pnl for t in trades) if trades else Decimal("0")
        total_gross = sum(t.gross_pnl for t in trades) if trades else Decimal("0")
        total_charges = sum(t.charges for t in trades) if trades else Decimal("0")
        win_rate = len(wins) / len(trades) * 100 if trades else 0.0

        # Sharpe ratio from daily equity returns
        sharpe = self._compute_sharpe()

        # Max drawdown
        max_dd = self._compute_max_drawdown()

        # Profit factor
        gross_wins = sum(t.net_pnl for t in wins) if wins else Decimal("0")
        losses = [t for t in trades if t.net_pnl < Decimal("0")]
        gross_losses = abs(sum(t.net_pnl for t in losses)) if losses else Decimal("0")
        pf = float(gross_wins / gross_losses) if gross_losses > Decimal("0") else float("inf")

        return BacktestResult(
            equity_curve=self._equity_curve,
            trades=trades,
            total_net_pnl=Decimal(str(total_net)),
            total_gross_pnl=Decimal(str(total_gross)),
            total_charges=Decimal(str(total_charges)),
            win_rate=win_rate,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_dd,
            profit_factor=pf,
            total_trades=len(trades),
            winning_trades=len(wins),
            blotter_path=blotter_path,
        )

    def _compute_sharpe(self, risk_free_rate: float = 0.065) -> float:
        """Annualised Sharpe ratio from the equity curve."""
        if len(self._equity_curve) < 2:
            return 0.0
        equities = [float(e) for _, e in self._equity_curve]
        returns = [(equities[i] - equities[i - 1]) / equities[i - 1] for i in range(1, len(equities))]
        if not returns:
            return 0.0
        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        std_r = math.sqrt(variance)
        if std_r == 0:
            return 0.0
        daily_rf = risk_free_rate / 252
        return (mean_r - daily_rf) / std_r * math.sqrt(252)

    def _compute_max_drawdown(self) -> float:
        """Maximum peak-to-trough drawdown percentage."""
        if not self._equity_curve:
            return 0.0
        peak = float(self._equity_curve[0][1])
        max_dd = 0.0
        for _, equity in self._equity_curve:
            e = float(equity)
            if e > peak:
                peak = e
            if peak > 0:
                dd = (peak - e) / peak * 100
                max_dd = max(max_dd, dd)
        return max_dd

    @staticmethod
    def load_candles_from_csv(
        csv_path: Path,
        symbol: str = "NIFTY",
        exchange: Exchange = Exchange.NSE,
    ) -> list[Candle]:
        """
        Load OHLCV data from a CSV file.

        Expected columns: timestamp, open, high, low, close, volume
        (column names are case-insensitive).
        """
        df = pd.read_csv(csv_path)
        df.columns = [c.lower().strip() for c in df.columns]
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        candles: list[Candle] = []
        for _, row in df.iterrows():
            candles.append(
                Candle(
                    symbol=symbol,
                    exchange=exchange,
                    timestamp=row["timestamp"].to_pydatetime(),
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=int(row.get("volume", 0)),
                )
            )
        return candles
