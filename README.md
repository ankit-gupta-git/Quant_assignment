# Institutional Quant Trading Engine

> Production-grade algorithmic trading system for Indian markets (NSE & MCX)  
> Built with Python 3.12 · Clean Architecture · Domain-Driven Design

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py (Entry Point)                   │
│              backtest | walkforward | simulate                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
      ┌────────────────▼────────────────┐
      │        Execution Layer           │
      │  OrderManager  ·  Reconciliation │
      │  Fills         ·  KillSwitch     │
      └────────────────┬────────────────┘
                       │
   ┌───────────────────▼──────────────────────┐
   │              Strategy Layer               │
   │  GridStrategy  ·  StopReverseStrategy     │
   │  BaseStrategy  ·  Signal objects          │
   └────┬────────────────────────┬────────────┘
        │                        │
┌───────▼──────────┐   ┌─────────▼──────────┐
│  Indicator Layer  │   │   Risk Layer        │
│  ATR · EMA · RSI  │   │  PositionCap        │
│  MACD · ADX       │   │  PyramidingCtrl     │
│  VWAP · Bollinger │   │  KillSwitch         │
└───────────────────┘   └─────────────────────┘
        │                        │
┌───────▼────────────────────────▼────────────┐
│              Macro Regime Engine              │
│  MacroScorer · RegimeChangeEvent             │
│  Parameter Overrides · Circuit Breaker       │
└───────────────────────┬─────────────────────┘
                        │
┌───────────────────────▼─────────────────────┐
│                Broker Layer                   │
│  BrokerBase (abstract)                        │
│  ZerodhaMockBroker (REST + WebSocket)         │
│  WebSocketManager (reconnect + heartbeat)     │
│  MockWebSocketServer (synthetic data)         │
└───────────────────────┬─────────────────────┘
                        │
┌───────────────────────▼─────────────────────┐
│              Backtest Engine                  │
│  BacktestEngine · WalkForwardEngine           │
│  FixedSlippage · VolumeSlippage               │
│  NSEEquityBrokerage · ChargeBreakdown         │
└───────────────────────┬─────────────────────┘
                        │
┌───────────────────────▼─────────────────────┐
│               Storage Layer                   │
│  DuckDBStore (orders, fills, trades, snaps)   │
│  Parquet export (PyArrow · Snappy)            │
└───────────────────────┬─────────────────────┘
                        │
┌───────────────────────▼─────────────────────┐
│            Monitoring / Observability         │
│  TradeBlotter (CSV export · statistics)       │
│  AlertManager (console · webhook · SMS)       │
│  structlog JSON logging                       │
└─────────────────────────────────────────────┘
```

---

## Folder Structure

```
quant_engine/
├── app/
│   ├── core/
│   │   ├── config.py          # Pydantic Settings (env-driven)
│   │   └── logger.py          # structlog setup
│   ├── domain/
│   │   ├── models.py          # Candle, Tick, Order, Fill, Trade, Position, Portfolio, Signal
│   │   ├── enums.py           # Side, OrderStatus, MarketRegime, SignalAction, …
│   │   └── events.py          # Domain events (KillSwitchEvent, RegimeChangeEvent, …)
│   ├── indicators/
│   │   ├── atr.py             # ATR (Wilder smoothing)
│   │   ├── ema.py             # Exponential Moving Average
│   │   ├── rsi.py             # RSI (Wilder)
│   │   ├── macd.py            # MACD + Signal + Histogram
│   │   ├── adx.py             # ADX + DI+/DI-
│   │   ├── vwap.py            # Volume Weighted Average Price
│   │   └── bollinger.py       # Bollinger Bands (SMA ± k×σ)
│   ├── strategy/
│   │   ├── base.py            # Abstract BaseStrategy
│   │   ├── grid.py            # ATR-spaced Grid Strategy with pyramiding
│   │   └── stop_reverse.py    # Stop-and-Reverse Strategy
│   ├── risk/
│   │   ├── kill_switch.py     # Emergency kill switch
│   │   ├── position_cap.py    # Max positions + max exposure limits
│   │   └── pyramiding.py      # Pyramid layer controller
│   ├── macro/
│   │   ├── regime.py          # Macro Regime Engine (BULL/BEAR/RISK_OFF/SIDEWAYS)
│   │   └── scoring.py         # Per-variable scorers + composite classification
│   ├── broker/
│   │   ├── base.py            # Abstract BrokerBase
│   │   ├── zerodha_mock.py    # Mock Zerodha REST + WebSocket broker
│   │   └── websocket.py       # WebSocketManager (reconnect, heartbeat, MockWS)
│   ├── execution/
│   │   ├── order_manager.py   # Idempotent order lifecycle management
│   │   ├── reconciliation.py  # Broker ↔ local state reconciliation
│   │   └── fills.py           # Fill processor
│   ├── backtest/
│   │   ├── engine.py          # Bar-accurate backtest with anti-lookahead
│   │   ├── walkforward.py     # Rolling walk-forward framework
│   │   ├── slippage.py        # FixedSlippage + VolumeSlippage models
│   │   └── brokerage.py       # Indian market charges (STT, GST, CTT, stamp)
│   ├── storage/
│   │   ├── duckdb_store.py    # DuckDB CRUD for orders, trades, fills, snapshots
│   │   └── parquet.py         # PyArrow Parquet export
│   ├── monitoring/
│   │   ├── trade_blotter.py   # In-memory trade ledger + CSV export + statistics
│   │   └── alerts.py          # AlertManager (console + webhook + structured log)
│   └── agents/
│       ├── test_generator.py  # AI SDLC: changed files → pytest command
│       └── commit_writer.py   # AI SDLC: git diff → Conventional Commit message
├── data/
│   ├── sample_ohlc.csv        # 500 synthetic NIFTY daily bars
│   └── macro.csv              # 100 synthetic macro snapshots (VIX, USDINR, Crude, Yield)
├── tests/
│   ├── conftest.py            # Shared fixtures (candle factories, orders)
│   ├── test_atr.py            # ATR indicator unit tests
│   ├── test_indicators.py     # EMA, RSI, MACD, ADX, VWAP, Bollinger tests
│   ├── test_grid_strategy.py  # Grid strategy (entry, exit, SAR, pyramiding, cap)
│   ├── test_kill_switch.py    # Kill switch (activate, idempotency, listeners, reset)
│   ├── test_risk.py           # PositionCap + PyramidingController
│   ├── test_pyramiding.py     # Pyramiding edge cases regression tests
│   ├── test_macro_regime.py   # MacroRegimeEngine + MacroScorer
│   ├── test_broker.py         # ZerodhaMockBroker (connect, place, cancel, reconnect)
│   ├── test_backtest.py       # BacktestEngine + slippage + brokerage models
│   ├── test_storage.py        # DuckDB CRUD + Parquet export
│   ├── test_pnl.py            # Decimal P&L precision, drawdown, equity
│   ├── test_order_recovery.py # Crash recovery + reconciliation
│   └── test_websocket.py      # MockWebSocketServer candle streaming
├── main.py                    # Entry point (backtest | walkforward | simulate)
├── pyproject.toml             # Poetry configuration
├── .env.example               # Environment variable template
└── README.md                  # This file
```

---

## Installation

### Prerequisites

- Python 3.12+
- Poetry 1.8+

```bash
# Install Poetry
pip install poetry

# Clone and install
git clone <repo_url>
cd quant_engine
poetry install

# Copy environment template
cp .env.example .env
# Edit .env as needed
```

---

## Poetry Commands

```bash
# Install all dependencies
poetry install

# Run tests with coverage
poetry run pytest

# Run linter
poetry run ruff check app tests

# Run type checker
poetry run mypy app

# Format code
poetry run black app tests

# Enter virtualenv shell
poetry shell
```

---

## Running Backtest

```bash
# Using Poetry
poetry run python main.py backtest

# Or directly
python main.py backtest
```

**Sample output:**

```
============================================================
  BACKTEST RESULTS
============================================================
  total_trades                 42
  winning_trades               26
  win_rate_pct                 61.9
  total_net_pnl                ₹38,245.00
  total_gross_pnl              ₹41,100.00
  total_charges                ₹2,855.00
  sharpe_ratio                 1.2341
  max_drawdown_pct             8.4
  profit_factor                2.143
  blotter_path                 data/blotter.csv
============================================================
  Blotter exported → data/blotter.csv
============================================================
```

---

## Running Walk-Forward Test

```bash
python main.py walkforward
```

---

## Running Live Simulation

```bash
python main.py simulate
```

Runs 60 synthetic ticks (1 per second) using `MockWebSocketServer`.  
All orders, fills, and trades are persisted in DuckDB.

---

## Running Tests

```bash
# Full test suite with coverage
pytest

# Quick run without coverage
pytest --no-cov -q

# Specific test file
pytest tests/test_grid_strategy.py -v

# Test with coverage report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

---

## AI SDLC Agents

### Test Generator Agent

Maps changed source files to the relevant pytest commands:

```bash
python -m app.agents.test_generator app/strategy/grid.py app/risk/kill_switch.py
```

Output:
```
── Generated pytest command ───────────────────────────────
pytest -v --tb=short --no-header tests/test_grid_strategy.py tests/test_kill_switch.py
──────────────────────────────────────────────────────────
```

### Commit Writer Agent

Generates Conventional Commit messages from staged git changes:

```bash
git add app/strategy/grid.py
python -m app.agents.commit_writer
```

Output:
```
── Generated Commit Message ───────────────────────────────
feat(strategy): add grid

Changed files: 1
Lines added: +47
Lines removed: -3
──────────────────────────────────────────────────────────
```

---

## Design Decisions

| Decision | Rationale |
|---|---|
| `Decimal` for all P&L | Eliminates IEEE-754 floating-point rounding errors that are unacceptable in financial systems |
| DuckDB over SQLite | Vectorised columnar analytics, Parquet round-trip, zero-setup embedded OLAP |
| Pydantic Settings | Type-safe, env-driven config with validation; zero runtime surprises |
| structlog JSON | Machine-parseable logs, compatible with ELK/CloudWatch/Loki |
| Clean Architecture | Domain models have zero framework dependencies; swap broker/storage without touching strategy logic |
| Protocol-based slippage | Swap `FixedSlippage` ↔ `VolumeSlippage` without changing the engine |
| Idempotent `client_order_id` | Re-submitting the same signal never creates duplicate orders |
| Walk-forward with warm-up | Strategy indicator buffers are primed during train window; only test window P&L counts |
| `frozen=True` Candle/Signal | Prevents accidental mutation of market data in the strategy pipeline |

---

## Limitations

- Live data feed requires a real Zerodha API key (not included); `ZerodhaMockBroker` is for simulation only.
- Options pricing (Greeks, IV) not implemented.
- Walk-forward does not include automated hyperparameter optimisation (can be added).
- Macro CSV must be updated manually; no live macro data pull.
- Phone SMS is simulated via console output only.

---

## Future Improvements

- [ ] Options strategy support (delta-neutral grids)
- [ ] Live data via Kite Connect WebSocket
- [ ] Multi-strategy portfolio with capital allocation
- [ ] Bayesian hyperparameter optimisation for walk-forward
- [ ] Real-time P&L dashboard (FastAPI + React)
- [ ] Telegram / Slack alert integrations
- [ ] Circuit breaker integration with regime engine
- [ ] MCX commodity strategy (crude, gold, silver)

---

## Commit History Conventions

All commits follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(strategy): add ATR-based grid with pyramiding
feat(risk): implement kill switch with listener pattern
feat(backtest): bar-accurate engine with lookahead prevention
feat(macro): classify regime from VIX/USDINR/crude/yield
feat(storage): DuckDB persistence with crash recovery
feat(monitoring): trade blotter with CSV export and statistics
feat(agents): test generator and commit writer AI utilities
test: >90% coverage across all modules
docs: professional README with architecture diagram
```

---

*Built by a Senior Quant Developer — institutional-grade, production-ready.*
