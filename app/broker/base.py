"""
app/broker/base.py
──────────────────
Abstract Broker interface (Port in Clean Architecture / Ports & Adapters).

All concrete broker implementations (Zerodha, ICICI, mock, etc.) must
implement this interface.  The rest of the engine depends ONLY on this
abstract type — never on a concrete implementation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.domain.models import Fill, Order, Position, Tick


class BrokerBase(ABC):
    """
    Abstract async broker adapter.

    Every method is ``async`` because all real broker communications
    involve I/O (HTTP or WebSocket).

    Implementations must be fully idempotent:
      * ``place_order`` called twice with the same ``client_order_id`` must
        not create a duplicate order.
      * ``cancel_order`` on an already-cancelled order must succeed silently.
    """

    # ── Connection lifecycle ──────────────────────────────────────────────────

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the broker API.
        For REST brokers this may be a no-op (connections are per-request).
        For WebSocket brokers this opens the persistent connection.
        """

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully close all broker connections."""

    # ── Order management ──────────────────────────────────────────────────────

    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """
        Submit an order to the exchange.

        Args:
            order: The order to place.  ``client_order_id`` is used for
                   idempotency.

        Returns:
            The updated ``Order`` with ``broker_order_id`` and ``status`` set.
        """

    @abstractmethod
    async def cancel_order(self, order: Order) -> Order:
        """
        Cancel an open order.

        Args:
            order: The order to cancel.

        Returns:
            The updated ``Order`` with status CANCELLED.
        """

    @abstractmethod
    async def modify_order(
        self,
        order: Order,
        new_price: float | None = None,
        new_quantity: int | None = None,
    ) -> Order:
        """
        Modify an open order's price or quantity.

        Args:
            order:        The order to modify.
            new_price:    New limit price (optional).
            new_quantity: New quantity (optional).

        Returns:
            Updated ``Order`` object.
        """

    # ── Account state ─────────────────────────────────────────────────────────

    @abstractmethod
    async def positions(self) -> list[Position]:
        """Return all current open positions from the broker."""

    @abstractmethod
    async def orders(self) -> list[Order]:
        """Return all orders (open and terminal) for the current session."""

    # ── Market data ───────────────────────────────────────────────────────────

    @abstractmethod
    async def stream_ticks(self, symbols: list[str]) -> AsyncIterator[Tick]:
        """
        Stream live ticks for the given symbols via WebSocket.

        Args:
            symbols: List of instrument tokens / symbols.

        Yields:
            ``Tick`` objects as they arrive from the feed.
        """
        # ``yield`` required to make this an async generator in ABC
        if False:
            yield  # type: ignore[misc]

    @abstractmethod
    async def get_fills(self, order_id: str) -> list[Fill]:
        """
        Fetch all fills for a specific order.

        Args:
            order_id: The broker order ID.

        Returns:
            List of ``Fill`` objects.
        """
