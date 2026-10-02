// Operational logs strictly formatted from app/core/logger.py and system run traces
export const terminalLogs = [
  {
    id: "LOG-1001",
    timestamp: "09:31:20.104",
    level: "INFO",
    module: "main",
    event: "engine.bootstrapped",
    message: "Initializing Quantitative Trading Engine v2.4 (Python 3.12.3 uvloop)",
    rawJson: '{"event": "engine.bootstrapped", "version": "2.4.0", "level": "info", "logger": "main", "env": "simulation"}'
  },
  {
    id: "LOG-1002",
    timestamp: "09:31:20.312",
    level: "INFO",
    module: "duckdb_store",
    event: "duckdb.connected",
    message: "Connected to DuckDB storage store at data/quant_engine.duckdb (WAL=128KB)",
    rawJson: '{"path": "data/quant_engine.duckdb", "event": "duckdb.connected", "level": "info", "logger": "app.storage.duckdb_store"}'
  },
  {
    id: "LOG-1003",
    timestamp: "09:31:20.489",
    level: "INFO",
    module: "zerodha_mock",
    event: "broker.connected",
    message: "Zerodha Mock Broker session authenticated. Session token validated for API key 'mock_api_key'",
    rawJson: '{"broker": "ZerodhaMockBroker", "event": "broker.connected", "level": "info", "logger": "app.broker.zerodha_mock"}'
  },
  {
    id: "LOG-1004",
    timestamp: "09:31:21.050",
    level: "INFO",
    module: "macro_regime",
    event: "macro.snapshot_loaded",
    message: "Ingested data/macro.csv: India VIX=18.52 (ELEVATED), USDINR=83.18, Brent=$84.00, 10Y=7.112%",
    rawJson: '{"regime": "HIGH_VOLATILITY", "vix": 18.52, "event": "macro.snapshot_loaded", "level": "info", "logger": "app.macro.regime"}'
  },
  {
    id: "LOG-1005",
    timestamp: "09:31:21.085",
    level: "WARN",
    module: "macro_regime",
    event: "macro.regime_override",
    message: "VIX > 18.0 triggered HIGH_VOLATILITY policy: ATR spacing multiplier adjusted 1.0x -> 1.5x, max positions throttled 10 -> 6",
    rawJson: '{"grid_mult": 1.5, "max_pos": 6, "event": "macro.regime_override", "level": "warn", "logger": "app.macro.regime"}'
  },
  {
    id: "LOG-1006",
    timestamp: "09:31:21.412",
    level: "INFO",
    module: "grid_strategy",
    event: "grid.initialised",
    message: "Grid initialized on NIFTY: Reference Price=17605.00, ATR(14)=154.64, Spacing=231.97 pts (20 levels armed)",
    rawJson: '{"ref_price": "17605.00", "spacing": "231.97", "levels": 20, "event": "grid.initialised", "level": "info", "logger": "app.strategy.grid"}'
  },
  {
    id: "LOG-1007",
    timestamp: "09:31:22.015",
    level: "DEBUG",
    module: "websocket",
    event: "market.tick_received",
    message: "WebSocket tick: NIFTY 17381.70, vol=142000, ltp=17381.70, bid=17381.50, ask=17381.80",
    rawJson: '{"symbol": "NIFTY", "close": "17381.70", "event": "market.tick_received", "level": "debug", "logger": "app.broker.websocket"}'
  },
  {
    id: "LOG-1008",
    timestamp: "09:31:23.018",
    level: "INFO",
    module: "indicators",
    event: "atr.recalculated",
    message: "ATR recalculated on candle #482: 154.64 (TrueRange=210.40, Wilder alpha=0.0714)",
    rawJson: '{"atr": 154.64, "event": "atr.recalculated", "level": "info", "logger": "app.indicators.atr"}'
  },
  {
    id: "LOG-1009",
    timestamp: "09:31:24.110",
    level: "INFO",
    module: "grid_strategy",
    event: "signal.generated",
    message: "Signal generated: ENTER_LONG @ 17381.70 (Grid Level -1 crossed, Distance=-231.97 pts)",
    rawJson: '{"action": "ENTER_LONG", "price": "17381.70", "event": "signal.generated", "level": "info", "logger": "app.strategy.grid"}'
  },
  {
    id: "LOG-1010",
    timestamp: "09:31:24.115",
    level: "INFO",
    module: "risk_manager",
    event: "risk.pre_trade_passed",
    message: "Pre-trade risk verification PASSED: Daily loss ₹1,144.91 < ₹50k, DD 1.12% < 10%, Open pos 0 < 6",
    rawJson: '{"checks": ["daily_loss", "max_drawdown", "position_cap"], "status": "passed", "event": "risk.pre_trade_passed", "level": "info"}'
  },
  {
    id: "LOG-1011",
    timestamp: "09:31:24.120",
    level: "INFO",
    module: "order_manager",
    event: "order.dispatched",
    message: "OMS dispatch: client_order_id=CID-547e112d-42ba-4b2e-a57c-f17b9b187654 BUY 50 NIFTY @ 17381.70 LIMIT",
    rawJson: '{"cid": "CID-547e112d-42ba", "side": "BUY", "qty": 50, "price": "17381.70", "event": "order.dispatched", "level": "info"}'
  },
  {
    id: "LOG-1012",
    timestamp: "09:31:24.122",
    module: "zerodha_mock",
    level: "INFO",
    event: "broker.order_accepted",
    message: "Mock broker accepted order ORD-9481023 in 1.8ms (simulated slip=0.02 pts)",
    rawJson: '{"broker_order_id": "ORD-9481023", "event": "broker.order_accepted", "level": "info", "logger": "app.broker.zerodha_mock"}'
  },
  {
    id: "LOG-1013",
    timestamp: "09:31:25.045",
    level: "INFO",
    module: "execution_fills",
    event: "order.filled",
    message: "Fill processed: ORD-9481023 filled 50 units @ 17381.72. STT=₹43.45, Exch=₹12.30, GST=₹13.20. Net cash debited",
    rawJson: '{"trade_id": "TRD-0122C93A522B", "fill_price": "17381.72", "qty": 50, "event": "order.filled", "level": "info"}'
  },
  {
    id: "LOG-1014",
    timestamp: "09:31:25.060",
    level: "INFO",
    module: "reconciliation",
    event: "position.reconciled",
    message: "Broker state reconciled: Internal position 1.0 == Broker book position 1.0 (Hash 0x8f2a confirmed)",
    rawJson: '{"drift": 0, "status": "synced", "event": "position.reconciled", "level": "info", "logger": "app.execution.reconciliation"}'
  },
  {
    id: "LOG-1015",
    timestamp: "09:31:25.065",
    level: "INFO",
    module: "trade_blotter",
    event: "blotter.trade_recorded",
    message: "Recorded TRD-0122C93A522B to data/blotter.csv: Gross P&L=+₹246.77, Charges=₹28.62, Net P&L=+₹218.14, Running P&L=+₹1,144.91",
    rawJson: '{"trade_id": "TRD-0122C93A522B", "net_pnl": "218.14", "running_pnl": "1144.91", "event": "blotter.trade_recorded", "level": "info"}'
  },
  {
    id: "LOG-1016",
    timestamp: "09:32:00.001",
    level: "DEBUG",
    module: "heartbeat",
    event: "system.heartbeat",
    message: "Event loop cycle latency 0.38ms, memory RSS 142.6MB, active coroutines: 3, DuckDB commit OK",
    rawJson: '{"rss_mb": 142.6, "latency_ms": 0.38, "event": "system.heartbeat", "level": "debug", "logger": "app.core.monitoring"}'
  }
];
