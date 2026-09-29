"""
app/indicators/vwap.py
──────────────────────
Volume-Weighted Average Price (VWAP).

VWAP is the ratio of the cumulative dollar volume to the cumulative share
volume.  It resets at the start of each trading session (daily reset).

VWAP is used by institutional desks as a benchmark price; trading above VWAP
is considered bullish intraday, below VWAP bearish.
"""
from __future__ import annotations

import pandas as pd


def vwap(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    volume: pd.Series,
    reset_daily: bool = True,
) -> pd.Series:
    """
    Compute VWAP, optionally resetting at every calendar day.

    Formula::

        typical_price = (high + low + close) / 3
        VWAP          = cumsum(typical_price × volume) / cumsum(volume)

    Args:
        high:        Series of bar highs.
        low:         Series of bar lows.
        close:       Series of bar closes.
        volume:      Series of bar volumes.
        reset_daily: If True, reset cumulative sums at each new calendar day.
                     Requires a DatetimeIndex on the input Series.

    Returns:
        VWAP Series aligned to the input index.

    Raises:
        ValueError: If reset_daily=True but index is not a DatetimeIndex.
    """
    typical_price = (high + low + close) / 3.0
    tpv = typical_price * volume

    if reset_daily:
        if not isinstance(high.index, pd.DatetimeIndex):
            raise ValueError(
                "reset_daily=True requires a DatetimeIndex; "
                "set reset_daily=False or convert your index."
            )
        date_groups = high.index.date  # type: ignore[attr-defined]
        cumulative_tpv = tpv.groupby(date_groups).cumsum()
        cumulative_vol = volume.groupby(date_groups).cumsum()
    else:
        cumulative_tpv = tpv.cumsum()
        cumulative_vol = volume.cumsum()

    vwap_series = cumulative_tpv / cumulative_vol
    vwap_series.name = "VWAP"
    return vwap_series


def vwap_from_df(df: pd.DataFrame, reset_daily: bool = True) -> pd.Series:
    """
    Convenience wrapper accepting a DataFrame with columns
    ``high``, ``low``, ``close``, ``volume``.
    """
    return vwap(
        df["high"],
        df["low"],
        df["close"],
        df["volume"],
        reset_daily=reset_daily,
    )
