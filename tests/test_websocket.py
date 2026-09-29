"""
tests/test_websocket.py
────────────────────────
Tests for WebSocket reconnection and tick streaming.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal

import pytest

from app.broker.websocket import MockWebSocketServer
from app.domain.enums import Exchange
from app.domain.models import Candle


class TestMockWebSocketServer:
    @pytest.mark.asyncio
    async def test_candle_stream_yields_candles(self) -> None:
        """Candle stream should yield Candle objects."""
        server = MockWebSocketServer(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            tick_interval_s=0.01,
            max_ticks=5,
        )
        candles: list[Candle] = []
        async for candle in server.candle_stream():
            candles.append(candle)

        assert len(candles) == 5
        for c in candles:
            assert isinstance(c, Candle)
            assert c.symbol == "NIFTY"
            assert c.exchange == Exchange.NSE

    @pytest.mark.asyncio
    async def test_candle_prices_are_positive(self) -> None:
        server = MockWebSocketServer(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            tick_interval_s=0.01,
            max_ticks=10,
        )
        async for candle in server.candle_stream():
            assert candle.close > Decimal("0")
            assert candle.high >= candle.low
            assert candle.volume >= 0

    @pytest.mark.asyncio
    async def test_candle_stream_respects_max_ticks(self) -> None:
        max_ticks = 7
        server = MockWebSocketServer(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            tick_interval_s=0.001,
            max_ticks=max_ticks,
        )
        count = 0
        async for _ in server.candle_stream():
            count += 1
        assert count == max_ticks

    @pytest.mark.asyncio
    async def test_candle_timestamps_increasing(self) -> None:
        server = MockWebSocketServer(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            tick_interval_s=0.001,
            max_ticks=5,
        )
        timestamps: list[datetime] = []
        async for candle in server.candle_stream():
            timestamps.append(candle.timestamp)

        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i - 1]
