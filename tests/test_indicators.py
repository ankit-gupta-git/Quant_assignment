"""
tests/test_indicators.py
─────────────────────────
Unit tests for EMA, RSI, MACD, ADX, VWAP, Bollinger Bands.
Tests are aligned to the actual indicator module APIs.
"""
from __future__ import annotations

import math

import pandas as pd
import pytest

from app.indicators.ema import ema as compute_ema
from app.indicators.rsi import rsi as compute_rsi
from app.indicators.macd import macd as compute_macd
from app.indicators.adx import adx as compute_adx
from app.indicators.vwap import vwap as compute_vwap
from app.indicators.bollinger import bollinger_bands


def prices(n: int = 60, start: float = 100.0, step: float = 0.5) -> pd.Series:
    return pd.Series([start + i * step for i in range(n)], dtype=float)


def ohlcv(n: int = 60) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    import random
    random.seed(7)
    highs, lows, closes, volumes = [], [], [], []
    p = 100.0
    for _ in range(n):
        h = p + random.uniform(0.5, 2)
        l = p - random.uniform(0.5, 2)
        c = l + random.uniform(0, h - l)
        highs.append(h)
        lows.append(l)
        closes.append(c)
        volumes.append(random.randint(50_000, 500_000))
        p = c
    return (
        pd.Series(highs, dtype=float),
        pd.Series(lows, dtype=float),
        pd.Series(closes, dtype=float),
        pd.Series(volumes, dtype=float),
    )


# ── EMA ───────────────────────────────────────────────────────────────────────


class TestEMA:
    def test_length(self) -> None:
        result = compute_ema(prices(), period=10)
        assert len(result) == 60

    def test_nans_at_start(self) -> None:
        result = compute_ema(prices(), period=10)
        assert result.iloc[:9].isna().all()

    def test_monotone_increasing_on_rising_prices(self) -> None:
        result = compute_ema(prices(100), period=5).dropna()
        diffs = result.diff().dropna()
        assert (diffs >= 0).all()

    def test_single_element_returns_itself(self) -> None:
        result = compute_ema(pd.Series([50.0]), period=1)
        assert result.iloc[0] == pytest.approx(50.0)


# ── RSI ───────────────────────────────────────────────────────────────────────


class TestRSI:
    def test_range(self) -> None:
        import random
        random.seed(42)
        p = pd.Series([100 + random.uniform(-2, 2) for _ in range(60)], dtype=float)
        result = compute_rsi(p, period=14).dropna()
        assert (result >= 0).all() and (result <= 100).all()

    def test_rising_prices_high_rsi(self) -> None:
        p = pd.Series([float(i) for i in range(1, 40)], dtype=float)
        result = compute_rsi(p, period=14).dropna()
        assert float(result.iloc[-1]) > 70

    def test_falling_prices_low_rsi(self) -> None:
        p = pd.Series([float(100 - i) for i in range(40)], dtype=float)
        result = compute_rsi(p, period=14).dropna()
        assert float(result.iloc[-1]) < 30


# ── MACD ──────────────────────────────────────────────────────────────────────


class TestMACD:
    def test_returns_macd_result_with_three_attributes(self) -> None:
        """MACD returns a MACDResult dataclass with .macd, .signal, .histogram."""
        from app.indicators.macd import MACDResult
        result = compute_macd(prices(60))
        assert isinstance(result, MACDResult)
        assert len(result.macd) == 60
        assert len(result.signal) == 60
        assert len(result.histogram) == 60

    def test_histogram_is_macd_minus_signal(self) -> None:
        result = compute_macd(prices(60))
        diff = (result.macd - result.signal).dropna()
        hist_nonan = result.histogram.dropna()
        common_idx = diff.index.intersection(hist_nonan.index)
        pd.testing.assert_series_equal(
            diff.loc[common_idx].reset_index(drop=True),
            hist_nonan.loc[common_idx].reset_index(drop=True),
            check_names=False,
        )

    def test_fast_slow_validation(self) -> None:
        with pytest.raises(ValueError):
            compute_macd(prices(60), fast_period=26, slow_period=12)


# ── ADX ───────────────────────────────────────────────────────────────────────


class TestADX:
    def test_adx_nonnegative(self) -> None:
        high, low, close, _ = ohlcv(60)
        result = compute_adx(high, low, close, period=14)
        valid = result.adx.dropna()
        assert (valid >= 0).all()

    def test_adx_returns_adx_result(self) -> None:
        from app.indicators.adx import ADXResult
        high, low, close, _ = ohlcv(60)
        result = compute_adx(high, low, close, period=14)
        assert isinstance(result, ADXResult)

    def test_adx_series_length(self) -> None:
        high, low, close, _ = ohlcv(60)
        result = compute_adx(high, low, close, period=14)
        assert len(result.adx) == 60

    def test_plus_di_minus_di_positive(self) -> None:
        high, low, close, _ = ohlcv(60)
        result = compute_adx(high, low, close, period=14)
        assert (result.plus_di.dropna() >= 0).all()
        assert (result.minus_di.dropna() >= 0).all()


# ── VWAP ──────────────────────────────────────────────────────────────────────


class TestVWAP:
    def test_vwap_length_no_reset(self) -> None:
        """VWAP without daily reset works on integer-indexed series."""
        high, low, close, volume = ohlcv(50)
        result = compute_vwap(high, low, close, volume, reset_daily=False)
        assert len(result) == 50

    def test_vwap_between_session_high_low(self) -> None:
        high, low, close, volume = ohlcv(50)
        result = compute_vwap(high, low, close, volume, reset_daily=False).dropna()
        assert (result >= low.min()).all()
        assert (result <= high.max()).all()

    def test_vwap_requires_datetime_index_when_reset(self) -> None:
        """reset_daily=True with non-datetime index must raise ValueError."""
        high, low, close, volume = ohlcv(50)
        with pytest.raises(ValueError, match="DatetimeIndex"):
            compute_vwap(high, low, close, volume, reset_daily=True)

    def test_vwap_datetime_index(self) -> None:
        """VWAP with DatetimeIndex and reset_daily=True works correctly."""
        idx = pd.date_range("2023-01-01 09:15", periods=30, freq="min")
        high = pd.Series([100.5] * 30, index=idx, dtype=float)
        low = pd.Series([99.5] * 30, index=idx, dtype=float)
        close = pd.Series([100.0] * 30, index=idx, dtype=float)
        volume = pd.Series([100_000] * 30, index=idx, dtype=float)
        result = compute_vwap(high, low, close, volume, reset_daily=True)
        assert len(result) == 30
        assert (abs(result.dropna() - 100.0) < 1e-4).all()


# ── Bollinger Bands ───────────────────────────────────────────────────────────


class TestBollingerBands:
    def test_returns_bollinger_result(self) -> None:
        from app.indicators.bollinger import BollingerResult
        result = bollinger_bands(prices(40), period=20)
        assert isinstance(result, BollingerResult)

    def test_returns_three_main_series(self) -> None:
        """bollinger_bands uses std_dev kwarg (not num_std)."""
        result = bollinger_bands(prices(40), period=20, std_dev=2.0)
        assert len(result.upper) == 40
        assert len(result.middle) == 40
        assert len(result.lower) == 40

    def test_upper_above_lower(self) -> None:
        result = bollinger_bands(prices(40), period=20, std_dev=2.0)
        valid_upper = result.upper.dropna()
        valid_lower = result.lower.loc[valid_upper.index]
        assert (valid_upper >= valid_lower).all()

    def test_mid_is_sma(self) -> None:
        p = prices(40)
        result = bollinger_bands(p, period=20, std_dev=2.0)
        sma = p.rolling(20).mean()
        pd.testing.assert_series_equal(
            result.middle.dropna(), sma.dropna(), check_names=False
        )

    def test_constant_price_zero_bandwidth(self) -> None:
        """Constant prices → std=0 → zero bandwidth → bands equal middle."""
        p = pd.Series([100.0] * 30)
        result = bollinger_bands(p, period=20, std_dev=2.0)
        # std=0, so upper should equal middle
        valid = result.upper.dropna()
        valid_mid = result.middle.dropna()
        pd.testing.assert_series_equal(valid, valid_mid, check_names=False)
