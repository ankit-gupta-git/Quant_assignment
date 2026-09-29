"""
app/indicators/macd.py
──────────────────────
Moving Average Convergence / Divergence (MACD).

Classic Gerald Appel formulation:
    MACD Line  = EMA(fast) - EMA(slow)
    Signal     = EMA(MACD Line, signal_period)
    Histogram  = MACD Line - Signal
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.indicators.ema import ema


@dataclass(frozen=True)
class MACDResult:
    """Container for MACD output series."""
    macd: pd.Series
    signal: pd.Series
    histogram: pd.Series


def macd(
    series: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MACDResult:
    """
    Compute MACD, Signal, and Histogram.

    Args:
        series:        Input close price Series.
        fast_period:   Fast EMA period (default 12).
        slow_period:   Slow EMA period (default 26).
        signal_period: Signal line EMA period (default 9).

    Returns:
        A ``MACDResult`` named tuple containing three aligned Series.

    Raises:
        ValueError: If fast_period >= slow_period or insufficient data.
    """
    if fast_period >= slow_period:
        raise ValueError(
            f"fast_period ({fast_period}) must be less than slow_period ({slow_period})"
        )

    fast_ema = ema(series, fast_period)
    slow_ema = ema(series, slow_period)

    macd_line = (fast_ema - slow_ema).rename(f"MACD_{fast_period}_{slow_period}")

    # Drop leading NaNs before computing the signal EMA
    valid_macd = macd_line.dropna()
    signal_line = ema(valid_macd, signal_period).reindex(series.index)
    signal_line.name = f"MACD_Signal_{signal_period}"

    histogram = (macd_line - signal_line).rename("MACD_Histogram")

    return MACDResult(macd=macd_line, signal=signal_line, histogram=histogram)
