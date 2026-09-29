"""
app/storage/duckdb_store.py
───────────────────────────
DuckDB-backed persistence layer.

Responsibilities
────────────────
* Bootstrap the schema (DDL) on first run.
* Persist ``Order``, ``Trade``, ``Fill`` and ``Portfolio`` snapshots.
* Reload state after a crash / restart (idempotent).
* Provide query helpers used by the backtest engine and monitoring.

All writes are wrapped in explicit transactions so partial failures
do not leave the database in an inconsistent state.
"""
from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import duckdb

from app.core.logger import get_logger
from app.domain.enums import Exchange, OrderStatus, OrderType, ProductType, Side
from app.domain.models import Fill, Order, Portfolio, Position, Trade

log = get_logger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS orders (
    client_order_id   VARCHAR PRIMARY KEY,
    broker_order_id   VARCHAR,
    symbol            VARCHAR NOT NULL,
    exchange          VARCHAR NOT NULL,
    side              VARCHAR NOT NULL,
    order_type        VARCHAR NOT NULL,
    product_type      VARCHAR NOT NULL,
    quantity          INTEGER NOT NULL,
    price             DECIMAL(18, 4) NOT NULL,
    trigger_price     DECIMAL(18, 4) DEFAULT 0,
    status            VARCHAR NOT NULL,
    filled_quantity   INTEGER DEFAULT 0,
    average_price     DECIMAL(18, 4) DEFAULT 0,
    strategy_id       VARCHAR NOT NULL,
    tag               VARCHAR DEFAULT '',
    reject_reason     VARCHAR DEFAULT '',
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS fills (
    fill_id               VARCHAR PRIMARY KEY,
    order_id              VARCHAR NOT NULL,
    symbol                VARCHAR NOT NULL,
    exchange              VARCHAR NOT NULL,
    side                  VARCHAR NOT NULL,
    quantity              INTEGER NOT NULL,
    price                 DECIMAL(18, 4) NOT NULL,
    brokerage             DECIMAL(18, 4) DEFAULT 0,
    stt                   DECIMAL(18, 4) DEFAULT 0,
    transaction_charges   DECIMAL(18, 4) DEFAULT 0,
    gst                   DECIMAL(18, 4) DEFAULT 0,
    timestamp             TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS trades (
    trade_id      VARCHAR PRIMARY KEY,
    symbol        VARCHAR NOT NULL,
    exchange      VARCHAR NOT NULL,
    side          VARCHAR NOT NULL,
    quantity      INTEGER NOT NULL,
    entry_price   DECIMAL(18, 4) NOT NULL,
    exit_price    DECIMAL(18, 4) NOT NULL,
    entry_time    TIMESTAMP NOT NULL,
    exit_time     TIMESTAMP NOT NULL,
    strategy_id   VARCHAR NOT NULL,
    gross_pnl     DECIMAL(18, 4) NOT NULL,
    charges       DECIMAL(18, 4) NOT NULL,
    net_pnl       DECIMAL(18, 4) NOT NULL,
    reason        VARCHAR DEFAULT ''
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    snapshot_id    VARCHAR PRIMARY KEY,
    timestamp      TIMESTAMP NOT NULL,
    cash           DECIMAL(18, 4) NOT NULL,
    equity         DECIMAL(18, 4) NOT NULL,
    daily_pnl      DECIMAL(18, 4) NOT NULL,
    drawdown_pct   DOUBLE NOT NULL,
    positions_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS risk_events (
    event_id   VARCHAR PRIMARY KEY,
    timestamp  TIMESTAMP NOT NULL,
    event_type VARCHAR NOT NULL,
    message    TEXT NOT NULL,
    level      VARCHAR NOT NULL,
    metadata   TEXT DEFAULT '{}'
);
"""


class DuckDBStore:
    """
    Thin wrapper around a DuckDB connection providing CRUD operations
    for all domain objects.

    Args:
        db_path: Path to the ``.duckdb`` file.  Use ``:memory:`` for tests.
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self._path = str(db_path)
        self._conn: duckdb.DuckDBPyConnection = duckdb.connect(self._path)
        self._bootstrap()
        log.info("duckdb.connected", path=self._path)

    # ── Schema ────────────────────────────────────────────────────────────────

    def _bootstrap(self) -> None:
        """Create tables if they do not exist."""
        self._conn.execute(_DDL)
        self._conn.commit()

    # ── Orders ────────────────────────────────────────────────────────────────

    def upsert_order(self, order: Order) -> None:
        """Insert or update an order row (idempotent on client_order_id)."""
        self._conn.execute(
            """
            INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (client_order_id) DO UPDATE SET
                broker_order_id  = excluded.broker_order_id,
                status           = excluded.status,
                filled_quantity  = excluded.filled_quantity,
                average_price    = excluded.average_price,
                updated_at       = excluded.updated_at,
                reject_reason    = excluded.reject_reason
            """,
            [
                order.client_order_id,
                order.broker_order_id,
                order.symbol,
                order.exchange.value,
                order.side.value,
                order.order_type.value,
                order.product_type.value,
                order.quantity,
                str(order.price),
                str(order.trigger_price),
                order.status.value,
                order.filled_quantity,
                str(order.average_price),
                order.strategy_id,
                order.tag,
                order.reject_reason,
                order.created_at,
                order.updated_at,
            ],
        )
        self._conn.commit()

    def load_open_orders(self) -> list[Order]:
        """Return all orders that are not in a terminal state."""
        rows = self._conn.execute(
            "SELECT * FROM orders WHERE status NOT IN ('FILLED','CANCELLED','REJECTED')"
        ).fetchall()
        return [self._row_to_order(r) for r in rows]

    def load_all_orders(self) -> list[Order]:
        """Return every order stored in the database."""
        rows = self._conn.execute("SELECT * FROM orders").fetchall()
        return [self._row_to_order(r) for r in rows]

    # ── Fills ─────────────────────────────────────────────────────────────────

    def insert_fill(self, fill: Fill) -> None:
        """Persist a fill record."""
        self._conn.execute(
            """
            INSERT INTO fills VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (fill_id) DO NOTHING
            """,
            [
                fill.fill_id,
                fill.order_id,
                fill.symbol,
                fill.exchange.value,
                fill.side.value,
                fill.quantity,
                str(fill.price),
                str(fill.brokerage),
                str(fill.stt),
                str(fill.transaction_charges),
                str(fill.gst),
                fill.timestamp,
            ],
        )
        self._conn.commit()

    def load_fills_for_order(self, order_id: str) -> list[Fill]:
        """Load all fills for a given order id."""
        rows = self._conn.execute(
            "SELECT * FROM fills WHERE order_id = ?", [order_id]
        ).fetchall()
        return [self._row_to_fill(r) for r in rows]

    # ── Trades ────────────────────────────────────────────────────────────────

    def insert_trade(self, trade: Trade) -> None:
        """Persist a completed trade."""
        self._conn.execute(
            """
            INSERT INTO trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (trade_id) DO NOTHING
            """,
            [
                trade.trade_id,
                trade.symbol,
                trade.exchange.value,
                trade.side.value,
                trade.quantity,
                str(trade.entry_price),
                str(trade.exit_price),
                trade.entry_time,
                trade.exit_time,
                trade.strategy_id,
                str(trade.gross_pnl),
                str(trade.charges),
                str(trade.net_pnl),
                trade.reason,
            ],
        )
        self._conn.commit()

    def load_trades(self, strategy_id: str | None = None) -> list[Trade]:
        """Load trades, optionally filtering by strategy."""
        if strategy_id:
            rows = self._conn.execute(
                "SELECT * FROM trades WHERE strategy_id = ? ORDER BY entry_time",
                [strategy_id],
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM trades ORDER BY entry_time"
            ).fetchall()
        return [self._row_to_trade(r) for r in rows]

    # ── Portfolio snapshots ───────────────────────────────────────────────────

    def save_portfolio_snapshot(self, portfolio: Portfolio) -> None:
        """Persist a portfolio state snapshot for crash recovery."""
        import uuid

        positions_data: dict[str, Any] = {
            sym: {
                "symbol": pos.symbol,
                "exchange": pos.exchange.value,
                "side": pos.side.value,
                "quantity": pos.quantity,
                "average_price": str(pos.average_price),
                "strategy_id": pos.strategy_id,
                "realised_pnl": str(pos.realised_pnl),
                "unrealised_pnl": str(pos.unrealised_pnl),
            }
            for sym, pos in portfolio.positions.items()
        }
        self._conn.execute(
            "INSERT INTO portfolio_snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                f"SNAP-{uuid.uuid4().hex[:12].upper()}",
                datetime.utcnow(),
                str(portfolio.cash),
                str(portfolio.equity),
                str(portfolio.daily_realised_pnl),
                portfolio.drawdown_pct,
                json.dumps(positions_data),
            ],
        )
        self._conn.commit()

    def load_latest_portfolio_snapshot(self) -> dict[str, Any] | None:
        """Return the most recent snapshot as a raw dict, or None."""
        row = self._conn.execute(
            "SELECT * FROM portfolio_snapshots ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        return {
            "snapshot_id": row[0],
            "timestamp": row[1],
            "cash": Decimal(str(row[2])),
            "equity": Decimal(str(row[3])),
            "daily_pnl": Decimal(str(row[4])),
            "drawdown_pct": float(row[5]),
            "positions": json.loads(row[6]),
        }

    # ── Risk events ───────────────────────────────────────────────────────────

    def insert_risk_event(
        self,
        event_type: str,
        message: str,
        level: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Record a risk-engine event."""
        import uuid

        self._conn.execute(
            "INSERT INTO risk_events VALUES (?, ?, ?, ?, ?, ?)",
            [
                f"RISK-{uuid.uuid4().hex[:8].upper()}",
                datetime.utcnow(),
                event_type,
                message,
                level,
                json.dumps(metadata or {}),
            ],
        )
        self._conn.commit()

    # ── Analytics queries ─────────────────────────────────────────────────────

    def daily_pnl_summary(self) -> list[dict[str, Any]]:
        """Aggregate net P&L per calendar date."""
        rows = self._conn.execute(
            """
            SELECT
                CAST(exit_time AS DATE)                       AS date,
                SUM(net_pnl)                                  AS net_pnl,
                COUNT(*)                                      AS trades,
                SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) AS wins
            FROM trades
            GROUP BY 1
            ORDER BY 1
            """
        ).fetchall()
        return [
            {
                "date": str(r[0]),
                "net_pnl": Decimal(str(r[1])),
                "trades": r[2],
                "wins": r[3],
            }
            for r in rows
        ]

    def close(self) -> None:
        """Release the DuckDB connection."""
        self._conn.close()
        log.info("duckdb.disconnected", path=self._path)

    # ── Row → Domain object helpers ───────────────────────────────────────────

    @staticmethod
    def _row_to_order(row: tuple) -> Order:  # type: ignore[type-arg]
        return Order(
            client_order_id=row[0],
            broker_order_id=row[1],
            symbol=row[2],
            exchange=Exchange(row[3]),
            side=Side(row[4]),
            order_type=OrderType(row[5]),
            product_type=ProductType(row[6]),
            quantity=int(row[7]),
            price=Decimal(str(row[8])),
            trigger_price=Decimal(str(row[9])),
            status=OrderStatus(row[10]),
            filled_quantity=int(row[11]),
            average_price=Decimal(str(row[12])),
            strategy_id=row[13],
            tag=row[14] or "",
            reject_reason=row[15] or "",
            created_at=row[16],
            updated_at=row[17],
        )

    @staticmethod
    def _row_to_fill(row: tuple) -> Fill:  # type: ignore[type-arg]
        return Fill(
            fill_id=row[0],
            order_id=row[1],
            symbol=row[2],
            exchange=Exchange(row[3]),
            side=Side(row[4]),
            quantity=int(row[5]),
            price=Decimal(str(row[6])),
            brokerage=Decimal(str(row[7])),
            stt=Decimal(str(row[8])),
            transaction_charges=Decimal(str(row[9])),
            gst=Decimal(str(row[10])),
            timestamp=row[11],
        )

    @staticmethod
    def _row_to_trade(row: tuple) -> Trade:  # type: ignore[type-arg]
        return Trade(
            trade_id=row[0],
            symbol=row[1],
            exchange=Exchange(row[2]),
            side=Side(row[3]),
            quantity=int(row[4]),
            entry_price=Decimal(str(row[5])),
            exit_price=Decimal(str(row[6])),
            entry_time=row[7],
            exit_time=row[8],
            strategy_id=row[9],
            gross_pnl=Decimal(str(row[10])),
            charges=Decimal(str(row[11])),
            net_pnl=Decimal(str(row[12])),
            reason=row[13] or "",
        )
