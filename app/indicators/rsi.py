"""
app/indicators/rsi.py
─────────────────────
Relative Strength Index (RSI) – Wilder's smoothing method.

RSI measures the velocity and magnitude of directional price movements.
Values > 70 are conventionally considered overbought; < 30 oversold.

Reference: J. Welles Wilder Jr., "New Concepts in Technical Trading Systems" (1978)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute the Relative Strength Index using Wilder's smoothing (RMA).

    Algorithm::

        delta    = series.diff()
        gains    = delta.where(delta > 0, 0)
        losses   = -delta.where(delta < 0, 0)
        avg_gain = RMA(gains, period)   # Wilder smoothing
        avg_loss = RMA(losses, period)
        RS       = avg_gain / avg_loss
        RSI      = 100 - (100 / (1 + RS))

    Edge cases:
        - When avg_loss == 0 the RSI is defined as 100 (pure bull strength).
        - When avg_gain == 0 the RSI is defined as 0  (pure bear strength).

    Args:
        series: Close price Series.
        period: Smoothing period (default 14).

    Returns:
        RSI Series in range [0, 100], aligned to input index.

    Raises:
        ValueError: If ``period`` < 1 or insufficient data.
    """
    if period < 1:
        raise ValueError(f"RSI period must be >= 1, got {period}")
    if len(series) < period + 1:
        raise ValueError(
            f"Need at least {period + 1} bars for RSI({period}), got {len(series)}"
        )

    delta = series.diff()
    gains = delta.clip(lower=0).values
    losses = (-delta).clip(lower=0).values

    avg_gain = np.full(len(series), np.nan)
    avg_loss = np.full(len(series), np.nan)

    # Wilder seed: simple average of first ``period`` gains/losses
    seed_idx = period  # index of first valid RSI
    avg_gain[seed_idx] = float(np.mean(gains[1 : seed_idx + 1]))
    avg_loss[seed_idx] = float(np.mean(losses[1 : seed_idx + 1]))

    alpha = 1.0 / period
    for i in range(seed_idx + 1, len(series)):
        avg_gain[i] = avg_gain[i - 1] * (1.0 - alpha) + gains[i] * alpha
        avg_loss[i] = avg_loss[i - 1] * (1.0 - alpha) + losses[i] * alpha

    with np.errstate(divide="ignore", invalid="ignore"):
        rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
        rsi_values = np.where(
            np.isinf(rs), 100.0, 100.0 - (100.0 / (1.0 + rs))
        )

    # Mask positions that don't yet have a valid value
    rsi_values[:seed_idx] = np.nan

    return pd.Series(rsi_values, index=series.index, name=f"RSI_{period}")
