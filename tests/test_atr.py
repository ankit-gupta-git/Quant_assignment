"""
tests/test_atr.py
──────────────────
Unit tests for the ATR indicator.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.indicators.atr import atr as compute_atr


def make_series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype=float)


class TestATR:
    """ATR indicator tests."""

    def test_basic_computation(self) -> None:
        """ATR should return a Series of the same length as inputs."""
        n = 20
        high = make_series([100 + i * 0.5 for i in range(n)])
        low = make_series([99 + i * 0.5 for i in range(n)])
        close = make_series([99.5 + i * 0.5 for i in range(n)])
        result = compute_atr(high, low, close, period=14)
        assert len(result) == n

    def test_atr_nonnegative(self) -> None:
        """ATR values must always be >= 0."""
        import random

        random.seed(1)
        n = 50
        high = make_series([100 + random.uniform(0, 2) for _ in range(n)])
        low = make_series([99 - random.uniform(0, 2) for _ in range(n)])
        close = make_series([99.5 + random.uniform(-1, 1) for _ in range(n)])
        result = compute_atr(high, low, close, period=14)
        assert (result.dropna() >= 0).all()

    def test_constant_prices_zero_atr(self) -> None:
        """Constant OHLC → ATR should converge to 0."""
        n = 30
        high = make_series([100.0] * n)
        low = make_series([100.0] * n)
        close = make_series([100.0] * n)
        result = compute_atr(high, low, close, period=14)
        # After warm-up, values should be 0 or very close
        assert float(result.dropna().iloc[-1]) == pytest.approx(0.0, abs=1e-6)

    def test_short_period_raises(self) -> None:
        """ATR raises ValueError when fewer bars than period+1 are provided."""
        high = make_series([100, 101, 102])
        low = make_series([99, 100, 101])
        close = make_series([99.5, 100.5, 101.5])
        with pytest.raises(ValueError):
            compute_atr(high, low, close, period=14)

    def test_high_volatility_larger_atr(self) -> None:
        """Higher price swings should produce higher ATR."""
        n = 30
        high_vol_high = make_series([100 + 5 * (i % 3) for i in range(n)])
        high_vol_low = make_series([100 - 5 * (i % 3) for i in range(n)])
        close = make_series([100.0] * n)

        low_vol_high = make_series([100.5] * n)
        low_vol_low = make_series([99.5] * n)

        atr_high = compute_atr(high_vol_high, high_vol_low, close, period=14)
        atr_low = compute_atr(low_vol_high, low_vol_low, close, period=14)

        last_high = float(atr_high.dropna().iloc[-1])
        last_low = float(atr_low.dropna().iloc[-1])
        assert last_high > last_low
