"""
app/backtest/walkforward.py
────────────────────────────
Walk-forward testing framework.

Splits the full history into rolling (train, test) windows and runs
a fresh backtest on each test window.  Combines per-window metrics
into an aggregated summary.

Walk-forward prevents in-sample optimisation bias:
  * The strategy is **reset** before each window.
  * Only data from the train window (indices 0..train_end) should be
    used for parameter optimisation (not implemented here — this module
    handles the split and run mechanics).

Window example (monthly, 6-month train, 1-month test):
    Window 1 : train=Jan–Jun,  test=Jul
    Window 2 : train=Feb–Jul,  test=Aug
    …
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.backtest.engine import BacktestEngine, BacktestResult
from app.backtest.brokerage import NSEEquityBrokerage
from app.backtest.slippage import FixedSlippage
from app.core.logger import get_logger
from app.domain.models import Candle, StrategyConfig
from app.storage.duckdb_store import DuckDBStore
from app.strategy.base import BaseStrategy

log = get_logger(__name__)


@dataclass
class WindowResult:
    """Results from a single walk-forward window."""

    window_index: int
    train_size: int
    test_size: int
    result: BacktestResult


@dataclass
class WalkForwardSummary:
    """Aggregated metrics across all walk-forward windows."""

    windows: list[WindowResult] = field(default_factory=list)

    @property
    def total_trades(self) -> int:
        return sum(w.result.total_trades for w in self.windows)

    @property
    def total_net_pnl(self) -> Decimal:
        return sum(w.result.total_net_pnl for w in self.windows)  # type: ignore[return-value]

    @property
    def average_win_rate(self) -> float:
        rates = [w.result.win_rate for w in self.windows if w.result.total_trades > 0]
        return sum(rates) / len(rates) if rates else 0.0

    @property
    def average_sharpe(self) -> float:
        sharpes = [w.result.sharpe_ratio for w in self.windows]
        return sum(sharpes) / len(sharpes) if sharpes else 0.0

    @property
    def average_max_drawdown(self) -> float:
        dds = [w.result.max_drawdown_pct for w in self.windows]
        return sum(dds) / len(dds) if dds else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "num_windows": len(self.windows),
            "total_trades": self.total_trades,
            "total_net_pnl": str(self.total_net_pnl),
            "average_win_rate_pct": round(self.average_win_rate, 2),
            "average_sharpe_ratio": round(self.average_sharpe, 4),
            "average_max_drawdown_pct": round(self.average_max_drawdown, 2),
            "per_window": [
                {
                    "window": w.window_index,
                    "train_bars": w.train_size,
                    "test_bars": w.test_size,
                    **w.result.to_dict(),
                }
                for w in self.windows
            ],
        }


class WalkForwardEngine:
    """
    Rolling walk-forward tester.

    Args:
        strategy_factory: Callable that returns a fresh ``BaseStrategy``
                          instance (ensures no state leaks between windows).
        train_bars:       Number of bars in the training window.
        test_bars:        Number of bars in the out-of-sample test window.
        step_bars:        How many bars to advance between windows.
                          Defaults to ``test_bars`` (non-overlapping tests).
        initial_cash:     Starting cash per window.
        slippage_pct:     Slippage percentage for each window.
        blotter_dir:      Directory for per-window blotter CSV files.
    """

    def __init__(
        self,
        strategy_factory: Any,  # Callable[[], BaseStrategy]
        train_bars: int = 252,
        test_bars: int = 63,
        step_bars: int | None = None,
        initial_cash: Decimal = Decimal("1_000_000"),
        slippage_pct: float = 0.05,
        blotter_dir: Path = Path("data/walkforward"),
    ) -> None:
        self._factory = strategy_factory
        self._train_bars = train_bars
        self._test_bars = test_bars
        self._step_bars = step_bars if step_bars is not None else test_bars
        self._initial_cash = initial_cash
        self._slippage_pct = slippage_pct
        self._blotter_dir = blotter_dir

    def run(self, candles: list[Candle]) -> WalkForwardSummary:
        """
        Slice ``candles`` into rolling windows and backtest each window.

        The training window is used only to warm up the strategy's
        indicator buffers; P&L is measured over the test window only.

        Args:
            candles: Full chronological candle list.

        Returns:
            WalkForwardSummary with per-window and aggregated metrics.
        """
        summary = WalkForwardSummary()
        total_bars = len(candles)
        window_index = 0

        start = 0
        while start + self._train_bars + self._test_bars <= total_bars:
            train_end = start + self._train_bars
            test_end = train_end + self._test_bars

            train_candles = candles[start:train_end]
            test_candles = candles[train_end:test_end]

            log.info(
                "walkforward.window.start",
                window=window_index,
                train_bars=len(train_candles),
                test_bars=len(test_candles),
                train_start=train_candles[0].timestamp.isoformat(),
                test_end=test_candles[-1].timestamp.isoformat(),
            )

            strategy = self._factory()

            # Warm-up: feed train bars so indicators are primed
            # (signals are discarded — no fills during warm-up)
            for candle in train_candles:
                strategy.on_candle(candle)

            # Out-of-sample test
            blotter_path = self._blotter_dir / f"blotter_w{window_index:03d}.csv"
            engine = BacktestEngine(
                strategy=strategy,
                initial_cash=self._initial_cash,
                slippage_model=FixedSlippage(slippage_pct=self._slippage_pct),
                brokerage_model=NSEEquityBrokerage(),
                db_store=DuckDBStore(":memory:"),
                blotter_path=blotter_path,
            )

            result = engine.run(test_candles)
            summary.windows.append(
                WindowResult(
                    window_index=window_index,
                    train_size=len(train_candles),
                    test_size=len(test_candles),
                    result=result,
                )
            )

            log.info(
                "walkforward.window.complete",
                window=window_index,
                net_pnl=str(result.total_net_pnl),
                sharpe=round(result.sharpe_ratio, 4),
                win_rate=round(result.win_rate, 2),
            )

            start += self._step_bars
            window_index += 1

        log.info(
            "walkforward.complete",
            windows=len(summary.windows),
            total_pnl=str(summary.total_net_pnl),
        )
        return summary
