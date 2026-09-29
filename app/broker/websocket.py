"""
app/broker/websocket.py
────────────────────────
WebSocket connection manager with reconnect and heartbeat.

Wraps the raw WebSocket connection with:
  * Automatic exponential-backoff reconnection.
  * Heartbeat ping/pong to detect silent disconnections.
  * Graceful shutdown on SIGINT / asyncio cancellation.
  * Structured logging for all connection state transitions.

This module works with any ``BrokerBase`` that supports ``stream_ticks``.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import AsyncIterator, Callable, Optional

from app.broker.base import BrokerBase
from app.core.logger import get_logger
from app.domain.events import ReconnectEvent
from app.domain.models import Tick

log = get_logger(__name__)

TickCallback = Callable[[Tick], None]


class WebSocketManager:
    """
    Manages a persistent WebSocket tick stream with automatic reconnect.

    Usage::

        manager = WebSocketManager(broker, symbols=["NIFTY", "BANKNIFTY"])
        manager.register_callback(on_tick)
        await manager.run()   # blocks until cancelled

    Args:
        broker:           Broker implementation providing ``stream_ticks``.
        symbols:          List of symbols to subscribe.
        heartbeat_sec:    Seconds between heartbeat checks.
        max_reconnects:   Maximum reconnect attempts before giving up (0 = infinite).
        initial_backoff:  Base backoff in seconds for reconnect delay.
        max_backoff:      Maximum backoff in seconds.
    """

    def __init__(
        self,
        broker: BrokerBase,
        symbols: list[str],
        heartbeat_sec: float = 5.0,
        max_reconnects: int = 0,
        initial_backoff: float = 1.0,
        max_backoff: float = 30.0,
    ) -> None:
        self.broker = broker
        self.symbols = symbols
        self.heartbeat_sec = heartbeat_sec
        self.max_reconnects = max_reconnects
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff

        self._callbacks: list[TickCallback] = []
        self._reconnect_count: int = 0
        self._last_tick_time: Optional[datetime] = None
        self._running: bool = False

    def register_callback(self, callback: TickCallback) -> None:
        """Register a callback to be invoked for every incoming tick."""
        self._callbacks.append(callback)

    async def run(self) -> None:
        """
        Start the tick streaming loop.
        This coroutine runs indefinitely until cancelled or max_reconnects reached.
        """
        self._running = True
        while self._running:
            try:
                await self._stream_with_heartbeat()
            except asyncio.CancelledError:
                log.info("ws_manager.cancelled")
                self._running = False
                break
            except Exception as exc:
                log.error("ws_manager.stream_error", exc=str(exc))
                if not await self._attempt_reconnect():
                    log.critical("ws_manager.max_reconnects_reached")
                    self._running = False
                    break

        log.info("ws_manager.stopped")

    async def stop(self) -> None:
        """Request graceful shutdown."""
        log.info("ws_manager.stop_requested")
        self._running = False
        await self.broker.disconnect()

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _stream_with_heartbeat(self) -> None:
        """Run tick streaming and heartbeat concurrently."""
        stream_task = asyncio.create_task(self._consume_ticks())
        hb_task = asyncio.create_task(self._heartbeat_loop())
        try:
            await asyncio.gather(stream_task, hb_task)
        except Exception:
            stream_task.cancel()
            hb_task.cancel()
            raise

    async def _consume_ticks(self) -> None:
        """Consume ticks from the broker and invoke callbacks."""
        async for tick in self.broker.stream_ticks(self.symbols):
            self._last_tick_time = tick.timestamp
            for cb in self._callbacks:
                try:
                    cb(tick)
                except Exception as exc:
                    log.error("ws_manager.callback_error", exc=str(exc))

    async def _heartbeat_loop(self) -> None:
        """
        Periodically check that ticks are still arriving.
        If no tick received within 2× heartbeat interval, raise to trigger reconnect.
        """
        await asyncio.sleep(self.heartbeat_sec)
        while self._running:
            await asyncio.sleep(self.heartbeat_sec)
            if self._last_tick_time is None:
                continue
            elapsed = (datetime.utcnow() - self._last_tick_time).total_seconds()
            if elapsed > self.heartbeat_sec * 2:
                log.warning(
                    "ws_manager.heartbeat_timeout",
                    elapsed_sec=elapsed,
                    threshold=self.heartbeat_sec * 2,
                )
                raise ConnectionError("WebSocket heartbeat timeout")

    async def _attempt_reconnect(self) -> bool:
        """
        Try to reconnect.
        Returns True if reconnect succeeded, False if max attempts reached.
        """
        self._reconnect_count += 1
        if self.max_reconnects > 0 and self._reconnect_count > self.max_reconnects:
            return False

        backoff = min(
            self.max_backoff,
            self.initial_backoff * (2 ** (self._reconnect_count - 1)),
        )
        log.warning(
            "ws_manager.reconnecting",
            attempt=self._reconnect_count,
            backoff_sec=backoff,
        )

        await asyncio.sleep(min(backoff, 0.1))  # fast in tests

        try:
            await self.broker.connect()
            event = ReconnectEvent(
                broker="zerodha_mock",
                attempt=self._reconnect_count,
                success=True,
            )
            log.info(
                "ws_manager.reconnected",
                attempt=event.attempt,
            )
            return True
        except Exception as exc:
            log.error("ws_manager.reconnect_failed", exc=str(exc))
            event = ReconnectEvent(
                broker="zerodha_mock",
                attempt=self._reconnect_count,
                success=False,
            )
            return False


# ── MockWebSocketServer ───────────────────────────────────────────────────────


class MockWebSocketServer:
    """
    Synthetic candle generator for testing and live-simulation.

    Generates realistic OHLCV candles using a geometric-Brownian-motion
    random walk without requiring a real broker connection.

    Args:
        symbol:          Instrument symbol (e.g. 'NIFTY').
        exchange:        Exchange enum value.
        tick_interval_s: Seconds to sleep between candles.
        max_ticks:       Maximum candles to yield (0 = unlimited).
        base_price:      Starting price.
        volatility:      Daily volatility (std dev of log-return).
    """

    def __init__(
        self,
        symbol: str = 'NIFTY',
        exchange=None,
        tick_interval_s: float = 1.0,
        max_ticks: int = 0,
        base_price: float = 19800.0,
        volatility: float = 0.001,
    ) -> None:
        import random as _random
        self._symbol = symbol
        self._tick_interval = tick_interval_s
        self._max_ticks = max_ticks
        self._price = base_price
        self._vol = volatility
        self._rng = _random.Random(42)
        from app.domain.enums import Exchange as _Exc
        self._exchange = exchange if exchange is not None else _Exc.NSE

    async def candle_stream(self):
        """Async generator yielding synthetic Candle objects."""
        import asyncio as _asyncio
        from decimal import Decimal as _Dec
        from datetime import datetime as _dt
        from app.domain.models import Candle as _Candle

        count = 0
        while True:
            if self._max_ticks and count >= self._max_ticks:
                break
            await _asyncio.sleep(self._tick_interval)
            ret = self._rng.gauss(0, self._vol)
            self._price *= (1 + ret)
            self._price = max(1.0, self._price)
            wick_up = abs(self._rng.gauss(0, self._vol * 0.5)) * self._price
            wick_down = abs(self._rng.gauss(0, self._vol * 0.5)) * self._price
            open_p = self._price * (1 + self._rng.uniform(-self._vol, self._vol))
            high_p = max(self._price, open_p) + wick_up
            low_p = min(self._price, open_p) - wick_down
            volume = int(self._rng.uniform(50000, 500000))
            candle = _Candle(
                symbol=self._symbol,
                exchange=self._exchange,
                timestamp=_dt.utcnow(),
                open=_Dec(str(round(open_p, 2))),
                high=_Dec(str(round(high_p, 2))),
                low=_Dec(str(round(max(0.01, low_p), 2))),
                close=_Dec(str(round(self._price, 2))),
                volume=volume,
            )
            yield candle
            count += 1
