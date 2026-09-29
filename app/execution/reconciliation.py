"""
app/execution/reconciliation.py
────────────────────────────────
Order reconciliation between local state and broker state.

Run on startup (after crash recovery) and periodically during live trading
to ensure local order/position state matches the broker's books.

Reconciliation algorithm:
  1. Fetch all orders and positions from broker API.
  2. For each local non-terminal order, compare status with broker.
  3. If mismatch found, update local state and log the discrepancy.
  4. For each broker position not tracked locally, create a synthetic position.
  5. For each local position not found in broker, mark as closed.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.broker.base import BrokerBase
from app.core.logger import get_logger
from app.domain.models import Order, Portfolio, Position

log = get_logger(__name__)


class ReconciliationEngine:
    """
    Synchronises local order and position state with the broker.

    Args:
        broker:    The broker adapter.
        portfolio: The shared portfolio being reconciled.
    """

    def __init__(self, broker: BrokerBase, portfolio: Portfolio) -> None:
        self._broker = broker
        self._portfolio = portfolio

    async def reconcile_orders(
        self, local_orders: dict[str, Order]
    ) -> list[str]:
        """
        Reconcile local order state against the broker's order book.

        Args:
            local_orders: Dict of client_order_id → Order.

        Returns:
            List of client_order_ids that were updated.
        """
        broker_orders = await self._broker.orders()
        broker_map = {o.client_order_id: o for o in broker_orders if o.client_order_id}
        reconciled: list[str] = []

        for cid, local in list(local_orders.items()):
            if local.is_terminal:
                continue

            broker_order = broker_map.get(cid)
            if broker_order is None:
                log.warning(
                    "reconcile.order_not_found_at_broker",
                    client_order_id=cid,
                    local_status=local.status.value,
                )
                continue

            if broker_order.status != local.status:
                log.info(
                    "reconcile.order_status_mismatch",
                    client_order_id=cid,
                    local=local.status.value,
                    broker=broker_order.status.value,
                )
                local.status = broker_order.status
                local.filled_quantity = broker_order.filled_quantity
                local.average_price = broker_order.average_price
                local.updated_at = datetime.utcnow()
                reconciled.append(cid)

        return reconciled

    async def reconcile_positions(self) -> list[str]:
        """
        Reconcile local portfolio positions against the broker's positions.

        Returns:
            List of symbols whose positions were reconciled.
        """
        broker_positions = await self._broker.positions()
        broker_map = {
            f"{p.symbol}:{p.exchange.value}": p for p in broker_positions
        }
        local_map = self._portfolio.positions
        reconciled: list[str] = []

        # Update existing / add new from broker
        for key, bp in broker_map.items():
            local = local_map.get(key)
            if local is None:
                log.warning(
                    "reconcile.phantom_position",
                    symbol=bp.symbol,
                    qty=bp.quantity,
                    avg_price=str(bp.average_price),
                )
                self._portfolio.positions[key] = bp
                reconciled.append(key)
            elif local.quantity != bp.quantity or abs(local.average_price - bp.average_price) > Decimal("0.01"):
                log.info(
                    "reconcile.position_mismatch",
                    symbol=bp.symbol,
                    local_qty=local.quantity,
                    broker_qty=bp.quantity,
                    local_avg=str(local.average_price),
                    broker_avg=str(bp.average_price),
                )
                local.quantity = bp.quantity
                local.average_price = bp.average_price
                local.last_updated = datetime.utcnow()
                reconciled.append(key)

        # Remove stale positions not found in broker
        for key in list(local_map.keys()):
            if key not in broker_map:
                pos = local_map[key]
                log.warning(
                    "reconcile.stale_position_removed",
                    symbol=pos.symbol,
                    qty=pos.quantity,
                )
                del self._portfolio.positions[key]
                reconciled.append(key)

        return reconciled

    async def full_reconcile(
        self, local_orders: dict[str, Order]
    ) -> dict[str, list[str]]:
        """
        Run complete reconciliation of both orders and positions.

        Returns:
            Dict with 'orders' and 'positions' keys listing reconciled IDs.
        """
        order_ids = await self.reconcile_orders(local_orders)
        pos_keys = await self.reconcile_positions()
        log.info(
            "reconcile.complete",
            orders_reconciled=len(order_ids),
            positions_reconciled=len(pos_keys),
        )
        return {"orders": order_ids, "positions": pos_keys}
