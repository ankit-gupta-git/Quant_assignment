"""
app/execution/order_manager.py
───────────────────────────────
Idempotent Order Manager.

Responsibilities:
  * Accept ``Signal`` objects from strategies.
  * Build ``Order`` objects with unique client_order_id.
  * Prevent duplicate submissions using a client_order_id registry.
  * Submit orders to the broker.
  * Track order state transitions.
  * Persist all orders to DuckDB for crash recovery.
  * Restore state on restart.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.broker.base import BrokerBase
from app.core.logger import get_logger
from app.domain.enums import (
    OrderStatus,
    OrderType,
    ProductType,
    Side,
    SignalAction,
)
from app.domain.models import Order, Portfolio, Signal
from app.storage.duckdb_store import DuckDBStore

log = get_logger(__name__)


class OrderManager:
    """
    Manages the full lifecycle of orders from signal to settlement.

    Args:
        broker:    Broker implementation (injected).
        store:     DuckDB persistence layer (injected).
        portfolio: Shared portfolio state (injected).
    """

    def __init__(
        self,
        broker: BrokerBase,
        store: DuckDBStore,
        portfolio: Portfolio | None = None,
    ) -> None:
        self._broker = broker
        self._store = store
        self._portfolio = portfolio or Portfolio(cash=Decimal("1000000"))
        self._pending: dict[str, Order] = {}  # client_order_id -> Order
        self._lock = asyncio.Lock()

    # ── Public interface ──────────────────────────────────────────────────────

    async def on_signal(self, signal: Signal) -> Optional[Order]:
        """
        Convert a strategy signal to an order and submit it.

        This is the primary entry point called by the execution engine.

        Args:
            signal: The trading signal from a strategy.

        Returns:
            The submitted Order, or None if the signal was rejected.
        """
        order = self._signal_to_order(signal)
        return await self.submit(order)

    async def submit(self, order: Order) -> Optional[Order]:
        """
        Submit an order to the broker with idempotency protection.

        If an order with the same ``client_order_id`` is already tracked,
        the existing order is returned without re-submitting.

        Args:
            order: The order to submit.

        Returns:
            The resulting Order (may be PENDING, OPEN, FILLED, or REJECTED).
        """
        async with self._lock:
            if order.client_order_id in self._pending:
                log.warning(
                    "order_manager.duplicate_blocked",
                    client_order_id=order.client_order_id,
                )
                return self._pending[order.client_order_id]

            self._pending[order.client_order_id] = order
            self._store.upsert_order(order)

        try:
            filled_order = await self._broker.place_order(order)
            self._update_tracked(filled_order)
            log.info(
                "order_manager.submitted",
                client_order_id=filled_order.client_order_id,
                broker_order_id=filled_order.broker_order_id,
                status=filled_order.status.value,
            )
            return filled_order
        except Exception as exc:
            log.error(
                "order_manager.submit_error",
                client_order_id=order.client_order_id,
                exc=str(exc),
            )
            order.status = OrderStatus.REJECTED
            order.reject_reason = str(exc)
            self._update_tracked(order)
            return order

    async def cancel(self, order: Order) -> Order:
        """Cancel an open order."""
        cancelled = await self._broker.cancel_order(order)
        self._update_tracked(cancelled)
        log.info(
            "order_manager.cancelled",
            client_order_id=cancelled.client_order_id,
        )
        return cancelled

    async def cancel_all(self) -> list[Order]:
        """Cancel all non-terminal orders (used by kill switch)."""
        cancelled: list[Order] = []
        async with self._lock:
            open_orders = [
                o for o in self._pending.values() if not o.is_terminal
            ]
        for order in open_orders:
            c = await self.cancel(order)
            cancelled.append(c)
        log.info("order_manager.cancel_all", count=len(cancelled))
        return cancelled

    # ── Crash recovery ────────────────────────────────────────────────────────

    async def restore_from_db(self) -> int:
        """
        Reload all non-terminal orders from DuckDB on startup.

        Returns the number of orders restored.
        """
        orders = self._store.load_open_orders()
        for order in orders:
            self._pending[order.client_order_id] = order
        log.info("order_manager.restored", count=len(orders))
        return len(orders)

    # ── Reconciliation ────────────────────────────────────────────────────────

    async def reconcile(self) -> list[str]:
        """
        Compare local order state with broker state and resolve discrepancies.

        Returns a list of order IDs that were reconciled.
        """
        broker_orders = await self._broker.orders()
        broker_map = {o.client_order_id: o for o in broker_orders if o.client_order_id}
        reconciled: list[str] = []

        for cid, local_order in list(self._pending.items()):
            if local_order.is_terminal:
                continue
            broker_order = broker_map.get(cid)
            if broker_order and broker_order.status != local_order.status:
                log.info(
                    "order_manager.reconcile",
                    client_order_id=cid,
                    local=local_order.status.value,
                    broker=broker_order.status.value,
                )
                local_order.status = broker_order.status
                local_order.filled_quantity = broker_order.filled_quantity
                local_order.average_price = broker_order.average_price
                self._store.upsert_order(local_order)
                reconciled.append(cid)

        return reconciled

    # ── Private helpers ───────────────────────────────────────────────────────

    def _update_tracked(self, order: Order) -> None:
        """Update in-memory store and DuckDB after a state transition."""
        self._pending[order.client_order_id] = order
        self._store.upsert_order(order)

    @staticmethod
    def _signal_to_order(signal: Signal) -> Order:
        """Convert a Signal to an Order with appropriate defaults."""
        side = Side.BUY if signal.action in {
            SignalAction.ENTER_LONG,
            SignalAction.PYRAMID_LONG,
            SignalAction.REVERSE_TO_LONG,
        } else Side.SELL

        order_type = (
            OrderType.MARKET
            if signal.action in {
                SignalAction.EXIT_LONG,
                SignalAction.EXIT_SHORT,
                SignalAction.REVERSE_TO_LONG,
                SignalAction.REVERSE_TO_SHORT,
            }
            else OrderType.LIMIT
        )

        return Order(
            symbol=signal.symbol,
            exchange=signal.exchange,
            side=side,
            order_type=order_type,
            product_type=ProductType.MIS,
            quantity=signal.quantity,
            price=signal.price,
            strategy_id=signal.strategy_id,
            tag=signal.action.value,
        )

    @property
    def open_order_count(self) -> int:
        return sum(1 for o in self._pending.values() if not o.is_terminal)

    @property
    def all_orders(self) -> list[Order]:
        return list(self._pending.values())
