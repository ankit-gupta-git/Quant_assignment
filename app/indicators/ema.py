"""
app/indicators/ema.py
─────────────────────
Exponential Moving Average (EMA).

Uses the standard initialisation: seed with a simple average of the first
``period`` bars, then apply the recursive EMA formula.

Reference: Robert D. Edwards & John Magee, "Technical Analysis of Stock Trends"
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Compute the Exponential Moving Average.

    Formula::

        k   = 2 / (period + 1)
        EMA[seed] = mean(series[0:period])
        EMA[i]    = series[i] * k + EMA[i-1] * (1 - k)

    Args:
        series: Input price series (typically close prices).
        period: Smoothing window length.

    Returns:
        EMA Series aligned to the input index; the first ``period - 1``
        values are NaN.

    Raises:
        ValueError: If ``period`` < 1.
    """
    if period < 1:
        raise ValueError(f"EMA period must be >= 1, got {period}")
    if len(series) < period:
        raise ValueError(
            f"Need at least {period} bars for EMA({period}), got {len(series)}"
        )

    k = 2.0 / (period + 1)
    values = np.full(len(series), np.nan)

    # SMA seed
    values[period - 1] = float(series.iloc[:period].mean())

    for i in range(period, len(series)):
        values[i] = float(series.iloc[i]) * k + values[i - 1] * (1.0 - k)

    return pd.Series(values, index=series.index, name=f"EMA_{period}")


def double_ema(series: pd.Series, period: int) -> pd.Series:
    """
    Double Exponential Moving Average (DEMA) for reduced lag.

    DEMA = 2 * EMA(series, n) - EMA(EMA(series, n), n)
    """
    e1 = ema(series, period)
    e2 = ema(e1.dropna(), period)
    e2 = e2.reindex(series.index)
    return (2 * e1 - e2).rename(f"DEMA_{period}")
