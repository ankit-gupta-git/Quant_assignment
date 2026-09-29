"""
app/indicators/adx.py
─────────────────────
Average Directional Index (ADX) with +DI and -DI.

ADX measures trend strength (not direction) on a 0-100 scale.
Values > 25 indicate a trending market; < 20 suggest range-bound conditions.
+DI > -DI indicates bullish trend; vice-versa for bearish.

Reference: J. Welles Wilder Jr., "New Concepts in Technical Trading Systems" (1978)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.indicators.atr import true_range


@dataclass(frozen=True)
class ADXResult:
    """Container for ADX output series."""
    adx: pd.Series
    plus_di: pd.Series
    minus_di: pd.Series


def adx(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    period: int = 14,
) -> ADXResult:
    """
    Compute ADX, +DI, and -DI using Wilder's smoothing.

    Algorithm::

        +DM = high - prev_high  (if > 0 and > |low - prev_low|, else 0)
        -DM = prev_low - low    (if > 0 and > |high - prev_high|, else 0)
        TR  = true_range(...)
        Smooth each with Wilder RMA(period)
        +DI  = 100 * RMA(+DM) / RMA(TR)
        -DI  = 100 * RMA(-DM) / RMA(TR)
        DX   = 100 * |+DI - -DI| / (+DI + -DI)
        ADX  = RMA(DX, period)

    Args:
        high:   Series of bar highs.
        low:    Series of bar lows.
        close:  Series of bar closes.
        period: Smoothing period (default 14).

    Returns:
        ``ADXResult`` with adx, plus_di, minus_di Series.

    Raises:
        ValueError: If period < 1 or insufficient data.
    """
    if period < 1:
        raise ValueError(f"ADX period must be >= 1, got {period}")

    n = len(close)
    if n < 2 * period + 1:
        raise ValueError(
            f"Need at least {2 * period + 1} bars for ADX({period}), got {n}"
        )

    tr = true_range(high, low, close).values
    up_move = high.diff().values
    down_move = (-low.diff()).values

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    def _wilders_rma(arr: np.ndarray, p: int) -> np.ndarray:
        """Wilder's RMA (identical to ATR smoothing)."""
        out = np.full(len(arr), np.nan)
        # Seed: mean of first p valid values (skip index 0 which is NaN)
        seed_end = p + 1  # index p (0-based) is the last of the seed window
        out[seed_end - 1] = np.nanmean(arr[1:seed_end])
        alpha = 1.0 / p
        for i in range(seed_end, len(arr)):
            out[i] = out[i - 1] * (1.0 - alpha) + arr[i] * alpha
        return out

    smooth_tr = _wilders_rma(tr, period)
    smooth_plus = _wilders_rma(plus_dm, period)
    smooth_minus = _wilders_rma(minus_dm, period)

    with np.errstate(divide="ignore", invalid="ignore"):
        plus_di_arr = np.where(smooth_tr == 0, 0, 100 * smooth_plus / smooth_tr)
        minus_di_arr = np.where(smooth_tr == 0, 0, 100 * smooth_minus / smooth_tr)
        di_sum = plus_di_arr + minus_di_arr
        di_diff = np.abs(plus_di_arr - minus_di_arr)
        dx = np.where(di_sum == 0, 0, 100 * di_diff / di_sum)

    adx_arr = _wilders_rma(dx, period)

    idx = close.index
    return ADXResult(
        adx=pd.Series(adx_arr, index=idx, name=f"ADX_{period}"),
        plus_di=pd.Series(plus_di_arr, index=idx, name=f"+DI_{period}"),
        minus_di=pd.Series(minus_di_arr, index=idx, name=f"-DI_{period}"),
    )
