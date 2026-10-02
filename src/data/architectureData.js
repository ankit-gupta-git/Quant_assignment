// Quantitative Trading Engine architecture layers, modules, and component specifications
export const architectureLayers = [
  {
    id: "DATA_LAYER",
    step: "01",
    name: "DATA & BROKER LAYER",
    subtitle: "Ingestion, Stream Handling & Brokerage Protocol",
    description: "Decoupled broker abstraction interface providing real-time WebSocket tick ingestion and KiteConnect v3 REST API compatibility in simulated or live environments.",
    components: [
      {
        name: "MockWebSocketServer",
        module: "app/broker/websocket.py",
        role: "Generates high-frequency NIFTY tick stream at configurable millisecond intervals with synthetic price noise."
      },
      {
        name: "WebSocketManager",
        module: "app/broker/websocket.py",
        role: "Maintains persistent socket connection with auto-reconnection backoff, heartbeats, and frame validation."
      },
      {
        name: "ZerodhaMockBroker",
        module: "app/broker/zerodha_mock.py",
        role: "Mock KiteConnect implementation matching Zerodha REST endpoints for order placement, margins, and book queries."
      },
      {
        name: "BrokerBase (Interface)",
        module: "app/broker/base.py",
        role: "Abstract Base Class standardizing order submission, cancellations, positions, and cash balance retrieval."
      }
    ]
  },
  {
    id: "ANALYTICS_LAYER",
    step: "02",
    name: "ANALYTICS & MACRO REGIME",
    subtitle: "Vectorized Indicators & Multi-Factor Regime Scoring",
    description: "NumPy-accelerated indicator calculations without look-ahead bias, combined with macroeconomic multi-variable classification.",
    components: [
      {
        name: "Technical Indicators Engine",
        module: "app/indicators/",
        role: "Vectorized indicators: ATR (Wilder), EMA, RSI, MACD, ADX/DMI, Bollinger Bands, and Volume-Weighted Average Price."
      },
      {
        name: "MacroScorer",
        module: "app/macro/scoring.py",
        role: "Multi-proxy scoring across India VIX, USDINR, Brent Crude, and 10Y Indian Government Bond Yields."
      },
      {
        name: "MacroRegimeEngine",
        module: "app/macro/regime.py",
        role: "Classifies regime (BULL, BEAR, RISK_OFF, SIDEWAYS) and emits dynamic parameter overrides to the strategy engine."
      }
    ]
  },
  {
    id: "STRATEGY_LAYER",
    step: "03",
    name: "STRATEGY EXECUTION ENGINE",
    subtitle: "Pure Signal Generation & Position Direction",
    description: "Clean domain strategies consuming immutable Candle models and emitting pure Signal objects without broker coupling.",
    components: [
      {
        name: "GridStrategy",
        module: "app/strategy/grid.py",
        role: "ATR-spaced dynamic grid with reference price tracking, multi-layer pyramiding, and take-profit/stop-loss boundaries."
      },
      {
        name: "StopAndReverseStrategy (SAR)",
        module: "app/strategy/stop_reverse.py",
        role: "Parabolic SAR trailing stop-and-reverse engine maintaining continuous market engagement on trend pivots."
      },
      {
        name: "BaseStrategy",
        module: "app/strategy/base.py",
        role: "Common interface ensuring strategies are 100% agnostic to backtest vs live execution environments."
      }
    ]
  },
  {
    id: "RISK_LAYER",
    step: "04",
    name: "RISK & PROTECTION CONTROLS",
    subtitle: "Pre-Trade Gateways & Emergency Circuit Breakers",
    description: "Hard stop limits evaluated on every tick. Rejects signals if daily loss limits, drawdown thresholds, or exposure caps are breached.",
    components: [
      {
        name: "KillSwitch",
        module: "app/risk/kill_switch.py",
        role: "Global circuit breaker triggered by daily loss breach (₹50k), max drawdown (10%), or 5 consecutive losses."
      },
      {
        name: "PositionCapController",
        module: "app/risk/position_cap.py",
        role: "Restricts max active open grid layers (cap=10) and caps gross portfolio exposure to ₹1,000,000."
      },
      {
        name: "PyramidingController",
        module: "app/risk/pyramiding.py",
        role: "Enforces minimum favorable price movement before allowing subsequent position layers to be added."
      }
    ]
  },
  {
    id: "EXECUTION_LAYER",
    step: "05",
    name: "ORDER MANAGEMENT & BACKTEST",
    subtitle: "Idempotent Routing, Anti-Lookahead Simulation & Statutory Taxes",
    description: "Translates validated signals into broker orders with UUID deduplication, slippage modeling, and Indian statutory exchange taxes.",
    components: [
      {
        name: "IdempotentOrderManager",
        module: "app/execution/order_manager.py",
        role: "Deterministic client_order_id hashing, order deduplication, and atomic synchronization with DuckDB storage."
      },
      {
        name: "ReconciliationEngine",
        module: "app/execution/reconciliation.py",
        role: "Periodic reconciliation between local position book and broker trade history to eliminate drift."
      },
      {
        name: "BacktestEngine",
        module: "app/backtest/engine.py",
        role: "Strict bar-by-bar event loop enforcing zero look-ahead bias with realistic fill queuing."
      },
      {
        name: "WalkForwardEngine",
        module: "app/backtest/walkforward.py",
        role: "Anchored and rolling walk-forward cross-validation across Out-of-Sample (OOS) evaluation windows."
      },
      {
        name: "NSE Statutory Tax Engine",
        module: "app/backtest/brokerage.py",
        role: "Calculates Indian exchange costs: STT (0.025%), Turnover fee, SEBI fee, GST (18%), and Stamp Duty."
      }
    ]
  },
  {
    id: "STORAGE_LAYER",
    step: "06",
    name: "PERSISTENCE & OBSERVABILITY",
    subtitle: "ACID State Recovery, Parquet Analytics & Audit Trail",
    description: "Resilient state storage capable of warm restart recovery after crashes, high-speed Parquet telemetry, and structured logging.",
    components: [
      {
        name: "DuckDBStore",
        module: "app/storage/duckdb_store.py",
        role: "Embedded analytical columnar database storing orders, fills, positions, and blotter snapshots with ACID guarantees."
      },
      {
        name: "ParquetExporter",
        module: "app/storage/parquet_export.py",
        role: "High-compression historical market data and execution trace dumps for offline research and quant modeling."
      },
      {
        name: "TradeBlotter",
        module: "app/monitoring/trade_blotter.py",
        role: "Real-time audit log of executed trades with running P&L, fees, and exportable CSV blotter format."
      },
      {
        name: "AlertManager",
        module: "app/monitoring/alerts.py",
        role: "Webhook alerts and critical notifications for kill switch triggers and high volatility regime shifts."
      }
    ]
  }
];
