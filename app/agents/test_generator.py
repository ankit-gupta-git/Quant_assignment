"""
app/agents/test_generator.py
─────────────────────────────
AI SDLC Agent: Regression Test Generator

Given a list of changed Python files, this agent analyses which modules
are affected and generates the appropriate pytest command(s) to run.

Usage (CLI):
    python -m app.agents.test_generator app/strategy/grid.py app/risk/kill_switch.py

It also prints the generated pytest invocation so it can be piped into CI.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# ── Module → test file mapping ────────────────────────────────────────────────

_MODULE_TO_TEST: dict[str, str] = {
    "app/indicators/atr.py": "tests/test_atr.py",
    "app/indicators/ema.py": "tests/test_indicators.py",
    "app/indicators/rsi.py": "tests/test_indicators.py",
    "app/indicators/macd.py": "tests/test_indicators.py",
    "app/indicators/adx.py": "tests/test_indicators.py",
    "app/indicators/vwap.py": "tests/test_indicators.py",
    "app/indicators/bollinger.py": "tests/test_indicators.py",
    "app/strategy/grid.py": "tests/test_grid_strategy.py",
    "app/strategy/stop_reverse.py": "tests/test_grid_strategy.py",
    "app/strategy/base.py": "tests/test_grid_strategy.py",
    "app/risk/kill_switch.py": "tests/test_kill_switch.py",
    "app/risk/position_cap.py": "tests/test_risk.py",
    "app/risk/pyramiding.py": "tests/test_pyramiding.py",
    "app/macro/regime.py": "tests/test_macro_regime.py",
    "app/macro/scoring.py": "tests/test_macro_regime.py",
    "app/broker/zerodha_mock.py": "tests/test_broker.py",
    "app/broker/websocket.py": "tests/test_websocket.py",
    "app/backtest/engine.py": "tests/test_backtest.py",
    "app/backtest/walkforward.py": "tests/test_backtest.py",
    "app/backtest/slippage.py": "tests/test_backtest.py",
    "app/backtest/brokerage.py": "tests/test_backtest.py",
    "app/storage/duckdb_store.py": "tests/test_storage.py",
    "app/execution/order_manager.py": "tests/test_order_recovery.py",
    "app/execution/reconciliation.py": "tests/test_order_recovery.py",
    "app/domain/models.py": "tests/test_pnl.py",
}


def resolve_test_files(changed_files: list[str]) -> list[str]:
    """
    Map changed source files to corresponding test files.

    Args:
        changed_files: Relative paths to changed source files.

    Returns:
        Deduplicated list of test file paths that should be run.
    """
    test_files: set[str] = set()
    unmapped: list[str] = []

    for f in changed_files:
        # Normalise separators
        normalised = f.replace("\\", "/").lstrip("./")
        mapped = _MODULE_TO_TEST.get(normalised)
        if mapped:
            test_files.add(mapped)
        else:
            unmapped.append(f)

    if unmapped:
        print(f"[test_generator] WARNING: No test mapping for: {unmapped}", file=sys.stderr)
        # Fall back to running the whole test suite
        test_files.add("tests/")

    return sorted(test_files)


def build_pytest_command(test_files: list[str], verbose: bool = True) -> str:
    """
    Construct the pytest CLI command string.

    Args:
        test_files: Test files / directories to include.
        verbose:    Add ``-v`` flag.

    Returns:
        Complete pytest command string.
    """
    flags = ["-v"] if verbose else []
    flags += ["--tb=short", "--no-header"]
    targets = " ".join(test_files)
    return f"pytest {' '.join(flags)} {targets}"


def main(argv: list[str] | None = None) -> None:
    """Entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Generate pytest command for changed files"
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="Changed source file paths (relative to project root)",
    )
    parser.add_argument(
        "--no-verbose",
        action="store_true",
        help="Omit -v flag from generated command",
    )
    args = parser.parse_args(argv)

    test_files = resolve_test_files(args.files)
    if not test_files:
        print("No test files resolved. Run the full suite: pytest tests/")
        return

    cmd = build_pytest_command(test_files, verbose=not args.no_verbose)
    print("\n── Generated pytest command ───────────────────────────────")
    print(cmd)
    print("──────────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    main()
