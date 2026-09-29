"""
app/storage/parquet.py
──────────────────────
Parquet export helpers using PyArrow.

Writes domain collections (trades, orders, fills) to Parquet files
that can be consumed by downstream analytics tools (DBeaver, Polars,
Spark, etc.).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.core.logger import get_logger
from app.domain.models import Fill, Order, Trade

log = get_logger(__name__)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def export_trades(trades: list[Trade], output_dir: Path) -> Path:
    """
    Serialise a list of ``Trade`` objects to a Parquet file.

    Args:
        trades:     Completed trade records.
        output_dir: Directory where the file will be written.

    Returns:
        Path to the written Parquet file.
    """
    _ensure_dir(output_dir)
    if not trades:
        log.warning("parquet.export_trades.empty")
        return output_dir / "trades.parquet"

    records = [
        {
            "trade_id": t.trade_id,
            "symbol": t.symbol,
            "exchange": t.exchange.value,
            "side": t.side.value,
            "quantity": t.quantity,
            "entry_price": float(t.entry_price),
            "exit_price": float(t.exit_price),
            "entry_time": t.entry_time,
            "exit_time": t.exit_time,
            "strategy_id": t.strategy_id,
            "gross_pnl": float(t.gross_pnl),
            "charges": float(t.charges),
            "net_pnl": float(t.net_pnl),
            "reason": t.reason,
        }
        for t in trades
    ]
    df = pd.DataFrame(records)
    table = pa.Table.from_pandas(df)
    out_path = output_dir / "trades.parquet"
    pq.write_table(table, out_path, compression="snappy")
    log.info("parquet.trades.written", path=str(out_path), rows=len(trades))
    return out_path


def export_orders(orders: list[Order], output_dir: Path) -> Path:
    """
    Serialise a list of ``Order`` objects to a Parquet file.

    Args:
        orders:     Order records.
        output_dir: Directory where the file will be written.

    Returns:
        Path to the written Parquet file.
    """
    _ensure_dir(output_dir)
    if not orders:
        log.warning("parquet.export_orders.empty")
        return output_dir / "orders.parquet"

    records = [
        {
            "client_order_id": o.client_order_id,
            "broker_order_id": o.broker_order_id,
            "symbol": o.symbol,
            "exchange": o.exchange.value,
            "side": o.side.value,
            "order_type": o.order_type.value,
            "product_type": o.product_type.value,
            "quantity": o.quantity,
            "price": float(o.price),
            "status": o.status.value,
            "filled_quantity": o.filled_quantity,
            "average_price": float(o.average_price),
            "strategy_id": o.strategy_id,
            "tag": o.tag,
            "created_at": o.created_at,
            "updated_at": o.updated_at,
        }
        for o in orders
    ]
    df = pd.DataFrame(records)
    table = pa.Table.from_pandas(df)
    out_path = output_dir / "orders.parquet"
    pq.write_table(table, out_path, compression="snappy")
    log.info("parquet.orders.written", path=str(out_path), rows=len(orders))
    return out_path


def export_fills(fills: list[Fill], output_dir: Path) -> Path:
    """
    Serialise a list of ``Fill`` objects to a Parquet file.

    Args:
        fills:      Fill records.
        output_dir: Directory where the file will be written.

    Returns:
        Path to the written Parquet file.
    """
    _ensure_dir(output_dir)
    if not fills:
        log.warning("parquet.export_fills.empty")
        return output_dir / "fills.parquet"

    records = [
        {
            "fill_id": f.fill_id,
            "order_id": f.order_id,
            "symbol": f.symbol,
            "exchange": f.exchange.value,
            "side": f.side.value,
            "quantity": f.quantity,
            "price": float(f.price),
            "brokerage": float(f.brokerage),
            "stt": float(f.stt),
            "transaction_charges": float(f.transaction_charges),
            "gst": float(f.gst),
            "timestamp": f.timestamp,
        }
        for f in fills
    ]
    df = pd.DataFrame(records)
    table = pa.Table.from_pandas(df)
    out_path = output_dir / "fills.parquet"
    pq.write_table(table, out_path, compression="snappy")
    log.info("parquet.fills.written", path=str(out_path), rows=len(fills))
    return out_path


def read_parquet(path: Path) -> pd.DataFrame:
    """
    Read any Parquet file back into a DataFrame.

    Args:
        path: Absolute path to a ``.parquet`` file.

    Returns:
        Loaded DataFrame.
    """
    table = pq.read_table(str(path))
    return table.to_pandas()
