"""
main.py
───────
Application entry point.

Modes
─────
  backtest   – Run historical backtest on data/sample_ohlc.csv
  simulate   – Run live simulation using the mock Zerodha broker + WebSocket
  walkforward – Run walk-forward test

Usage:
    python main.py backtest
    python main.py simulate
    python main.py walkforward

All configuration is read from .env (see .env.example).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from decimal import Decimal
from pathlib import Path

from app.core.config import get_settings
from app.core.logger import get_logger, setup_logging

log = get_logger(__name__)


# ── Backtest mode ─────────────────────────────────────────────────────────────

def run_backtest() -> None:
    """Run a historical backtest using the Grid strategy."""
    from app.backtest.engine import BacktestEngine
    from app.domain.enums import Exchange
    from app.domain.models import StrategyConfig
    from app.storage.duckdb_store import DuckDBStore
    from app.strategy.grid import GridStrategy

    settings = get_settings()

    log.info("main.backtest.start", ohlc=str(settings.backtest_ohlc_path))

    config = StrategyConfig(
        strategy_id="grid-backtest-01",
        symbol="NIFTY",
        exchange=Exchange.NSE,
        atr_multiplier=settings.grid_atr_multiplier,
        max_positions=settings.grid_max_positions,
        take_profit_multiplier=settings.grid_take_profit_multiplier,
        stop_loss_multiplier=settings.grid_stop_loss_multiplier,
        pyramid_enabled=True,
        stop_and_reverse=False,
    )

    strategy = GridStrategy(config)
    store = DuckDBStore(settings.duckdb_path)

    engine = BacktestEngine(
        strategy=strategy,
        initial_cash=Decimal("1000000"),
        db_store=store,
        blotter_path=settings.blotter_export_path,
    )

    candles = BacktestEngine.load_candles_from_csv(
        settings.backtest_ohlc_path,
        symbol="NIFTY",
        exchange=Exchange.NSE,
    )

    if len(candles) < 30:
        log.error("main.backtest.insufficient_data", bars=len(candles))
        sys.exit(1)

    result = engine.run(candles)

    print("\n" + "=" * 60)
    print("  BACKTEST RESULTS")
    print("=" * 60)
    for k, v in result.to_dict().items():
        print(f"  {k:<28} {v}")
    print("=" * 60)
    print(f"  Blotter exported -> {result.blotter_path}")
    print("=" * 60 + "\n")

    store.close()


# ── Walk-forward mode ─────────────────────────────────────────────────────────

def run_walkforward() -> None:
    """Run a walk-forward test on the full OHLC dataset."""
    from app.backtest.engine import BacktestEngine
    from app.backtest.walkforward import WalkForwardEngine
    from app.domain.enums import Exchange
    from app.domain.models import StrategyConfig
    from app.strategy.grid import GridStrategy

    settings = get_settings()

    log.info("main.walkforward.start")

    def strategy_factory() -> GridStrategy:
        cfg = StrategyConfig(
            strategy_id="grid-wf",
            symbol="NIFTY",
            exchange=Exchange.NSE,
            atr_multiplier=settings.grid_atr_multiplier,
            max_positions=settings.grid_max_positions,
            take_profit_multiplier=settings.grid_take_profit_multiplier,
            stop_loss_multiplier=settings.grid_stop_loss_multiplier,
            pyramid_enabled=True,
        )
        return GridStrategy(cfg)

    candles = BacktestEngine.load_candles_from_csv(
        settings.backtest_ohlc_path,
        symbol="NIFTY",
        exchange=Exchange.NSE,
    )

    wf_engine = WalkForwardEngine(
        strategy_factory=strategy_factory,
        train_bars=100,
        test_bars=50,
        step_bars=50,
        initial_cash=Decimal("1000000"),
        blotter_dir=Path("data/walkforward"),
    )

    summary = wf_engine.run(candles)

    print("\n" + "=" * 60)
    print("  WALK-FORWARD SUMMARY")
    print("=" * 60)
    d = summary.to_dict()
    for k, v in d.items():
        if k != "per_window":
            print(f"  {k:<32} {v}")
    print("\n  Per-window breakdown:")
    for w in d.get("per_window", []):
        print(
            f"    Window {w['window']:>3} | "
            f"trades={w['total_trades']:>4} | "
            f"pnl={w['total_net_pnl']:>12} | "
            f"sharpe={w['sharpe_ratio']:>6.3f}"
        )
    print("=" * 60 + "\n")


# ── Live simulation mode ──────────────────────────────────────────────────────

async def run_simulation(max_ticks: int = 30, interval_s: float = 0.1) -> None:
    """Run a live-simulation using the mock Zerodha broker and WebSocket."""
    from app.broker.zerodha_mock import ZerodhaMockBroker
    from app.broker.websocket import MockWebSocketServer
    from app.core.config import get_settings
    from app.domain.enums import Exchange
    from app.domain.models import StrategyConfig
    from app.execution.order_manager import OrderManager
    from app.monitoring.alerts import AlertManager
    from app.risk.kill_switch import KillSwitch
    from app.storage.duckdb_store import DuckDBStore
    from app.strategy.grid import GridStrategy

    settings = get_settings()

    log.info("main.simulation.start")

    broker = ZerodhaMockBroker(
        api_key=settings.zerodha_api_key,
        api_secret=settings.zerodha_api_secret,
        access_token=settings.zerodha_access_token,
    )
    await broker.connect()

    store = DuckDBStore(settings.duckdb_path)
    alert_mgr = AlertManager(
        webhook_url=settings.alert_webhook_url,
        phone_number=settings.alert_phone_number,
    )
    kill_switch = KillSwitch(
        max_daily_loss=settings.max_daily_loss,
        max_consecutive_losses=settings.max_consecutive_losses,
        max_drawdown_pct=settings.max_drawdown_pct,
        alert_manager=alert_mgr,
    )
    order_mgr = OrderManager(broker=broker, store=store)

    config = StrategyConfig(
        strategy_id="grid-live-01",
        symbol="NIFTY",
        exchange=Exchange.NSE,
        atr_multiplier=settings.grid_atr_multiplier,
        max_positions=settings.grid_max_positions,
    )
    strategy = GridStrategy(config)

    ws_server = MockWebSocketServer(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        tick_interval_s=interval_s,
        max_ticks=max_ticks,
    )

    print(f"\nStarting live simulation ({max_ticks} ticks @ {interval_s}s intervals)...\n")

    async for candle in ws_server.candle_stream():
        if kill_switch.is_triggered:
            log.warning("main.simulation.kill_switch_active")
            break

        signals = strategy.on_candle(candle)
        for signal in signals:
            await order_mgr.submit_signal(signal)

        log.info(
            "main.simulation.tick",
            symbol=candle.symbol,
            close=str(candle.close),
            signals=len(signals),
        )

    print("\nSimulation complete. Check logs for trade details.\n")
    store.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    setup_logging(get_settings().log_level, get_settings().log_format)

    parser = argparse.ArgumentParser(
        description="Quant Trading Engine – Institutional Grade"
    )
    parser.add_argument(
        "mode",
        choices=["backtest", "walkforward", "simulate"],
        help="Execution mode",
    )
    parser.add_argument(
        "--ticks",
        type=int,
        default=30,
        help="Number of simulated ticks for simulate mode (default: 30)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Interval in seconds between ticks for simulate mode (default: 0.1)",
    )
    args = parser.parse_args()

    if args.mode == "backtest":
        run_backtest()
    elif args.mode == "walkforward":
        run_walkforward()
    elif args.mode == "simulate":
        asyncio.run(run_simulation(max_ticks=args.ticks, interval_s=args.interval))


if __name__ == "__main__":
    main()
