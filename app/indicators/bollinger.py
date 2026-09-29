"""
app/indicators/bollinger.py
───────────────────────────
Bollinger Bands – John Bollinger (1983).

Bands are drawn at ±N standard deviations around a simple moving average.
Default parameters: 20-period SMA, ±2 standard deviations.

Useful for:
  * Identifying squeeze conditions (bands narrow → breakout imminent)
  * Mean-reversion signals (price touches/crosses a band)
  * Volatility normalisation (%B oscillator)
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class BollingerResult:
    """Container for Bollinger Band output."""
    upper: pd.Series
    middle: pd.Series
    lower: pd.Series
    bandwidth: pd.Series
    percent_b: pd.Series


def bollinger_bands(
    series: pd.Series,
    period: int = 20,
    std_dev: float = 2.0,
) -> BollingerResult:
    """
    Compute Bollinger Bands.

    Formula::

        Middle = SMA(series, period)
        StdDev = rolling_std(series, period, ddof=1)
        Upper  = Middle + std_dev * StdDev
        Lower  = Middle - std_dev * StdDev

    Derived::

        Bandwidth = (Upper - Lower) / Middle * 100  [% of middle band]
        %B        = (series - Lower) / (Upper - Lower)

    Args:
        series:  Input price series (typically close).
        period:  Rolling window for SMA and StdDev (default 20).
        std_dev: Number of standard deviations for bands (default 2.0).

    Returns:
        ``BollingerResult`` with upper, middle, lower, bandwidth, percent_b.

    Raises:
        ValueError: If period < 2 or std_dev <= 0.
    """
    if period < 2:
        raise ValueError(f"Bollinger period must be >= 2, got {period}")
    if std_dev <= 0:
        raise ValueError(f"std_dev must be > 0, got {std_dev}")

    middle = series.rolling(window=period, min_periods=period).mean()
    rolling_std = series.rolling(window=period, min_periods=period).std(ddof=1)

    upper = middle + std_dev * rolling_std
    lower = middle - std_dev * rolling_std

    with_zero_guard = (upper - lower).replace(0, float("nan"))
    percent_b = (series - lower) / with_zero_guard
    bandwidth = with_zero_guard / middle * 100.0

    return BollingerResult(
        upper=upper.rename(f"BB_Upper_{period}"),
        middle=middle.rename(f"BB_Middle_{period}"),
        lower=lower.rename(f"BB_Lower_{period}"),
        bandwidth=bandwidth.rename(f"BB_Bandwidth_{period}"),
        percent_b=percent_b.rename(f"BB_PercentB_{period}"),
    )
