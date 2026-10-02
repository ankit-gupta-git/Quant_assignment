// Infrastructure health and observability status
export const systemHealthData = {
  lastHeartbeat: "09:32:14.412 IST",
  status: "OPERATIONAL",
  subsystems: [
    {
      name: "WebSocket Feed",
      component: "MockWebSocketServer (Kite WS)",
      status: "STREAMING",
      state: "healthy",
      detail: "240 ticks/sec • 0 packet drops",
      latencyMs: 1.2
    },
    {
      name: "Market Data Engine",
      component: "CSV/Live Ingestion Pipeline",
      status: "STREAMING",
      state: "healthy",
      detail: "sample_ohlc.csv • 500 bars loaded",
      latencyMs: 0.8
    },
    {
      name: "Order Manager (OMS)",
      component: "IdempotentOrderManager",
      status: "HEALTHY",
      state: "healthy",
      detail: "38 orders reconciled • 0 unconfirmed",
      latencyMs: 2.1
    },
    {
      name: "Storage Engine",
      component: "DuckDBStore (ACID OLAP)",
      status: "HEALTHY",
      state: "healthy",
      detail: "quant_engine.duckdb • 5.51 MB",
      latencyMs: 3.4
    },
    {
      name: "Broker Reconciliation",
      component: "ReconciliationEngine",
      status: "HEALTHY",
      state: "healthy",
      detail: "Zero position drift • 100% hash parity",
      latencyMs: 4.8
    },
    {
      name: "Asyncio Event Loop",
      component: "Python 3.12 uvloop / asyncio",
      status: "RUNNING",
      state: "healthy",
      detail: "Tick: 100ms interval • CPU: 2.4%",
      latencyMs: 0.4
    }
  ],
  telemetry: {
    processMemoryMb: 142.6,
    activeTasks: 3,
    duckdbWalSizeBytes: 131072,
    reconciliationIntervalSec: 5,
    lastReconciliation: "09:32:10 IST",
    brokerAdapter: "ZerodhaMockBroker (v3.0.3)"
  }
};
