"""
app/indicators/atr.py
─────────────────────
Average True Range (ATR) – Wilder's smoothing method.

ATR is the cornerstone of the grid spacing calculation.
It measures market volatility by decomposing the typical trading range into
three components and applying an exponential-like smoothing.

Reference: J. Welles Wilder Jr., "New Concepts in Technical Trading Systems" (1978)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    """
    Compute the True Range for each bar.

    TR = max(
        high - low,
        |high - prev_close|,
        |low  - prev_close|
    )

    Args:
        high:  Series of bar highs.
        low:   Series of bar lows.
        close: Series of bar closes.

    Returns:
        A Series of True Range values (first value is NaN because there is no
        previous close for the very first bar).
    """
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    return pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)


def atr(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> pd.Series:
    """
    Compute the Average True Range using Wilder's smoothing (RMA).

    Wilder's RMA is equivalent to an EMA with ``alpha = 1 / period``.
    This differs from a simple rolling average (SMA of TR) and from a
    standard EMA with ``alpha = 2 / (period + 1)``.

    Formula::

        ATR[0] = mean(TR[0:period])          # initialisation (SMA seed)
        ATR[i] = (ATR[i-1] * (period-1) + TR[i]) / period

    Args:
        high:   Series of bar highs.
        low:    Series of bar lows.
        close:  Series of bar closes.
        period: Smoothing window (default 14, per Wilder).

    Returns:
        A Series of ATR values; the first ``period`` values are NaN until
        the indicator has enough bars to initialise.

    Raises:
        ValueError: If ``period`` < 1 or the input series have fewer than
                    ``period + 1`` bars.
    """
    if period < 1:
        raise ValueError(f"ATR period must be >= 1, got {period}")
    if len(close) < period + 1:
        raise ValueError(
            f"Need at least {period + 1} bars to compute ATR({period}), "
            f"got {len(close)}"
        )

    tr = true_range(high, low, close)

    # Seed with the SMA of the first ``period`` TR values.
    atr_values = np.full(len(tr), np.nan)
    first_valid = tr.first_valid_index()
    start_idx = tr.index.get_loc(first_valid)  # type: ignore[arg-type]

    seed_end = start_idx + period
    if seed_end > len(tr):
        raise ValueError("Not enough data to seed ATR.")

    atr_values[seed_end - 1] = float(tr.iloc[start_idx:seed_end].mean())

    for i in range(seed_end, len(tr)):
        atr_values[i] = (atr_values[i - 1] * (period - 1) + float(tr.iloc[i])) / period

    return pd.Series(atr_values, index=close.index, name=f"ATR_{period}")


def atr_from_df(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Convenience wrapper that accepts a DataFrame with columns
    ``high``, ``low``, ``close``.

    Args:
        df:     DataFrame with 'high', 'low', 'close' columns.
        period: ATR period.

    Returns:
        ATR Series aligned to the DataFrame index.
    """
    return atr(df["high"], df["low"], df["close"], period=period)
