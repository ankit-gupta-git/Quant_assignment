# 🎯 Interview Preparation Guide
## Institutional Quant Trading Engine

> **Read this top to bottom once. Then use the Table of Contents to revise.**
> Every concept is explained in plain, simple language — no prior quant background assumed.

---

## Table of Contents
1. [What the Project Does — The Big Picture](#1-what-the-project-does--the-big-picture)
2. [Concept Glossary — Plain English Definitions](#2-concept-glossary--plain-english-definitions)
3. [Module-by-Module Code Walkthrough](#3-module-by-module-code-walkthrough)
4. [Indian Market Specifics You Must Know](#4-indian-market-specifics-you-must-know)
5. [10 Most Likely Interview Questions + Answers](#5-10-most-likely-interview-questions--answers)
6. [Demo Order for Screen Share](#6-demo-order-for-screen-share)
7. [Quick-Recall One-Liners](#7-quick-recall-one-liners)

---

## 1. What the Project Does — The Big Picture

Imagine you are a trader sitting at a desk watching the NIFTY futures chart all day.
You notice that **when the price drops a certain amount, it tends to bounce back up**, so you buy.
If it drops even more, you buy again (pyramid). If it recovers, you take profit.
If it keeps falling, you cut losses (stop-loss).

This project **automates that entire trader brain** in Python, connects it to a broker (Zerodha), and wraps it in safety nets, logging, and backtesting so you can prove it works before risking real money.

### System in one paragraph
> The engine reads live price candles from Zerodha's WebSocket feed. A Grid Strategy places buy/sell orders at equally-spaced price levels. ATR (market volatility) decides the spacing. Position caps and a kill switch prevent catastrophic losses. All activity is stored in DuckDB. You can also replay history (backtest) or test how it would have performed across rolling windows (walk-forward). Every component has regression tests.

### Data flow diagram
```
Market Data (WebSocket)
        │
        ▼
   Candle Object
        │
        ▼
  GridStrategy.on_candle()
        │
        ├── too few bars? → skip (ATR warm-up)
        ├── grid not built? → build grid levels
        ├── price hits buy level? → ENTER_LONG / PYRAMID_LONG signal
        ├── price hits sell level? → ENTER_SHORT / REVERSE signal
        ├── price hits TP? → EXIT_LONG signal
        └── price hits SL? → EXIT_LONG signal
                │
                ▼
        OrderManager.submit()
                │
                ├── duplicate? → return existing order (idempotency)
                ├── persist to DuckDB
                └── send to ZerodhaMockBroker.place_order()
                            │
                            ▼
                    Fill created → Trade recorded → Blotter updated
```

---

## 2. Concept Glossary — Plain English Definitions

### 📐 ATR (Average True Range)
**What it is:** A measure of how much a stock price typically moves in one day (or one candle).

**Intuition:** If NIFTY moves ₹100 up and down on an average day, the ATR is around 100.

**Why we use it:** Instead of hard-coding "buy every 50 points lower", we say "buy every 1×ATR lower". This adapts automatically — in volatile markets spacing is wider (fewer, safer positions), in calm markets spacing is tighter (more positions).

**Formula:**
```
True Range (TR) = max(high - low,  |high - prev_close|,  |low - prev_close|)
ATR = average of TR over 14 bars  (using Wilder's smoothing)
```

**File:** `app/indicators/atr.py`

---

### 📊 Grid Trading Strategy
**What it is:** Think of a price ladder. You place buy orders at every rung below current price, sell orders at every rung above.

**Example:**
```
NIFTY is at 19800. ATR = 100. Spacing = 1× ATR = 100.
Grid levels:
  BUY  at 19700  (ref - 1×spacing)
  BUY  at 19600  (ref - 2×spacing)
  BUY  at 19500  (ref - 3×spacing)
  SELL at 19900  (ref + 1×spacing)
  SELL at 20000  (ref + 2×spacing)
```
Price drops to 19700 → trigger BUY.
Price rises back to 19900 → trigger SELL.
Profit = 200 points per round trip.

**File:** `app/strategy/grid.py`

---

### 📈 Pyramiding
**What it is:** Adding to a position as it moves against you (buying more as price falls = averaging down).

**Example:** You already bought at 19700. Now price falls to 19600 — you buy again. If price recovers, you profit on both positions.

**Risk:** If price keeps falling, you lose more. Hence we cap the number of pyramid levels with `max_positions`.

**In code:** When a second long level is triggered and you already have an open long, signal action becomes `PYRAMID_LONG` instead of `ENTER_LONG`.

---

### 🔄 Stop-and-Reverse (SAR)
**What it is:** If you are long and price hits a short level, instead of just placing a short, you **first close all longs, then go short**. You "reverse" your position.

**Why:** Markets sometimes trend sharply. SAR ensures you don't hold losing longs while simultaneously wanting shorts.

**In code:** When `stop_and_reverse=True` and a short level triggers while longs are open → `REVERSE_TO_SHORT` signal → all long entries cleared.

---

### 🛑 Kill Switch
**What it is:** An emergency stop button. Once activated, no new orders are allowed.

**Triggers:** Daily loss exceeds limit, VIX too high, consecutive losses too many.

**Why it matters:** In production, runaway loops or market anomalies can blow up an account in minutes. The kill switch prevents this.

**File:** `app/risk/kill_switch.py` — `KillSwitch.activate(reason, portfolio)`

---

### 🎚️ Position Cap
**What it is:** Maximum number of positions you can hold at one time. `max_positions = 5` means you can have at most 5 open buy orders.

**File:** `app/risk/position_cap.py`

---

### 🔁 Idempotency
**What it is:** Sending the same order twice should not result in two trades. The system should recognise it has already sent this order.

**How:** Every order gets a `client_order_id` (a UUID generated from the signal's unique properties). Before submitting, the OrderManager checks if this ID already exists in its `_pending` dict.

**Why it matters:** Networks are unreliable. A WebSocket can drop and reconnect. You might retry the order submission — idempotency ensures you don't accidentally double-trade.

**File:** `app/execution/order_manager.py` — `submit()` method

---

### 💾 Crash Recovery
**What it is:** If the Python process dies (power cut, OOM, bug), all open orders are saved in DuckDB. When you restart, the engine reloads them from disk — no orders are lost or forgotten.

**File:** `app/execution/order_manager.py` — `restore_from_db()` method

---

### 📉 Take Profit (TP) and Stop Loss (SL)
**Take Profit:** Exit when price moves in your favour by `ATR × take_profit_multiplier`.
- Example: Bought at 19700, ATR = 100, TP multiplier = 3 → TP = 19700 + 300 = 20000

**Stop Loss:** Exit when price moves against you by `ATR × stop_loss_multiplier`.
- Example: SL multiplier = 2 → SL = 19700 - 200 = 19500

**In code:** `_check_exit_signals()` in `grid.py`

---

### 📊 Backtesting
**What it is:** Replaying historical OHLCV data through the strategy as if it were happening live, to measure performance.

**Critical rule: No look-ahead bias**
- Bar N's signals must be filled at bar N+1's open.
- You cannot use tomorrow's close price to make today's decision.
- Our engine fills on `next_bar.open ± slippage` — this is bar-accurate.

**File:** `app/backtest/engine.py`

---

### 🚶 Walk-Forward Testing
**What it is:** Instead of testing on all data at once, you split into rolling windows:
- Train on bars 1–100 (fit parameters)
- Test on bars 101–150 (measure out-of-sample)
- Slide: train on bars 51–150, test on 151–200
- Repeat until data ends

**Why:** Prevents overfitting. If strategy only worked on historical data it was trained on, that is not useful. Walk-forward shows if it generalises.

**File:** `app/backtest/walkforward.py`

---

### 📉 Slippage
**What it is:** The difference between the price you wanted and the price you got. In a fast market, your buy order at 19700 might fill at 19703.

**Model:** We use a fixed percentage (0.05%) applied to the fill price. A ₹20,000 order costs an extra ₹10 in slippage.

**File:** `app/backtest/slippage.py`

---

### 🏦 Brokerage Model (NSE Specific)
When you trade on NSE, you pay:
| Charge | What it is |
|---|---|
| Brokerage | Zerodha charges ₹20 flat or 0.03% per order |
| STT | Securities Transaction Tax — 0.1% on delivery, 0.025% on intraday sells |
| Transaction charges | NSE turnover charges ~0.00345% |
| GST | 18% on (brokerage + transaction charges) |
| SEBI charges | ₹10 per crore of turnover |

**File:** `app/backtest/brokerage.py` — `IndianBrokerageModel.compute()`

---

### 📈 Sharpe Ratio
**What it is:** A measure of return vs risk. Higher is better.

**Formula:**
```
Sharpe = (Average Daily Return - Risk Free Rate) / Std Dev of Daily Returns × √252
```
- Risk free rate = 6.5% (India G-Sec rate)
- 252 = trading days per year

**Interpretation:**
- Sharpe < 0: Strategy loses more than risk-free rate
- Sharpe 0–1: Acceptable
- Sharpe > 1: Good
- Sharpe > 2: Excellent

---

### 📉 Max Drawdown
**What it is:** The largest peak-to-trough fall in your account value.

**Example:** Portfolio went ₹10L → ₹12L → ₹9L. Max drawdown = (12-9)/12 = 25%.

**Why it matters:** Even a profitable strategy is unusable if it requires you to stomach a 60% drawdown.

---

### 🌡️ Macro Regime Engine
**What it is:** The strategy behaves differently in different market conditions.

**Inputs (macro proxies):**
- **VIX:** India VIX, measures market fear. High VIX = volatile/bear market.
- **USDINR:** Rupee rate. Weak rupee = outflows = bearish for markets.
- **Crude oil price:** High crude = inflation pressure = bearish.
- **Bond yield:** High yield = money moves out of equity to bonds = bearish.

**Regimes:**
| Regime | Behavior |
|---|---|
| BULL | Tight grid (1×ATR), max positions, full exposure |
| BEAR | Wider grid (1.5×ATR), fewer positions |
| RISK_OFF | Widest grid (2×ATR), minimum positions |
| SIDEWAYS | Medium settings |

**Circuit breaker:** VIX > 40 → stop all new positions entirely.

**File:** `app/macro/regime.py`

---

### 🔌 WebSocket
**What it is:** A persistent two-way connection between your Python app and the broker's servers. Instead of asking "what's the price?" every second (polling), the broker *pushes* you a tick whenever price changes.

**Why not REST API?** REST is request-response (you ask, they answer). For live trading you need prices in milliseconds. WebSocket = always-on live stream.

**In code:** `app/broker/websocket.py` — `ZerodhaWebSocketClient` handles connection, reconnection, and tick parsing. `MockWebSocketServer` generates synthetic ticks for testing.

---

### 🧪 Reconciliation
**What it is:** After a crash or network drop, our local order state might differ from the broker's state. Reconciliation compares both and syncs them.

**Example:** We think order 123 is OPEN, but broker says it's FILLED. We update our local state.

**File:** `app/execution/reconciliation.py` and `app/execution/order_manager.py` — `reconcile()`

---

### 📋 Trade Blotter
**What it is:** A spreadsheet (CSV) of every trade: entry price, exit price, gross P&L, charges, net P&L. The "desk's spreadsheet" in the assignment.

**File:** `app/monitoring/trade_blotter.py` — exports to `data/blotter.csv`

---

### 🗃️ DuckDB
**What it is:** An embedded analytical database (like SQLite but optimised for analytics). No server required — just a file on disk.

**What we store:** Orders, fills, trades, portfolio snapshots.

**Why not pandas in memory?** Data survives crashes. You can query it with SQL.

**File:** `app/storage/duckdb_store.py`

---

### 🗂️ Parquet
**What it is:** A columnar file format for storing large time-series data (like OHLCV candles). Very fast for reading specific columns.

**File:** `app/storage/parquet.py`

---

### 📝 Structured Logging
**What it is:** Instead of `print("order placed")`, we log JSON:
```json
{"event": "order_manager.submitted", "client_order_id": "OID-123", "status": "OPEN", "level": "info", "timestamp": "2024-01-01T09:15:00Z"}
```

**Why:** Easy to search, filter, and alert on in production. Tools like Grafana can read JSON logs.

**Library:** `structlog` — `app/core/logger.py`

---

## 3. Module-by-Module Code Walkthrough

### 📁 Project Structure
```
Quant_Assignment/
├── app/
│   ├── core/          # Config (settings) + Logger
│   ├── domain/        # Data classes: Candle, Order, Signal, Trade, Portfolio
│   ├── indicators/    # ATR, EMA, RSI, MACD, ADX, VWAP, Bollinger Bands
│   ├── strategy/      # Grid strategy + Stop-and-reverse
│   ├── macro/         # Macro regime engine + scoring
│   ├── risk/          # Kill switch + Position cap + Pyramiding
│   ├── broker/        # Zerodha mock + WebSocket client
│   ├── execution/     # OrderManager + Reconciliation
│   ├── backtest/      # Engine + Slippage + Brokerage + Walk-forward
│   ├── storage/       # DuckDB store + Parquet reader
│   ├── monitoring/    # Trade blotter + Alert manager
│   └── agents/        # AI SDLC: commit writer + test generator
├── tests/             # 136 pytest tests
├── main.py            # CLI entry point
├── .env.example       # Environment variables template
└── README.md
```

---

### 🏗️ Domain Models (`app/domain/models.py`)
These are the data containers — think of them as the "language" all modules speak.

| Class | What it represents |
|---|---|
| `Candle` | One OHLCV bar: open, high, low, close, volume, timestamp |
| `Signal` | Strategy's intent: "buy NIFTY at 19700, 1 lot" |
| `Order` | Actual order sent to broker, has `client_order_id`, `status` |
| `Fill` | Confirmation from broker: "filled 1 lot at 19703" |
| `Trade` | Matched buy+sell pair: entry, exit, P&L |
| `Portfolio` | Current cash + positions + trades |
| `StrategyConfig` | All parameters: ATR multiplier, max positions, TP/SL |

---

### 📐 ATR Indicator (`app/indicators/atr.py`)

**Key code to explain:**
```python
# True Range = biggest of 3 measures
tr1 = high - low                      # bar's own range
tr2 = (high - prev_close).abs()       # gap-up capture
tr3 = (low  - prev_close).abs()       # gap-down capture
TR  = max(tr1, tr2, tr3)

# Wilder's smoothing (not a simple average)
ATR[0] = SMA(TR, period)              # seed
ATR[i] = (ATR[i-1] × (period-1) + TR[i]) / period
```

**Why Wilder's smoothing?** Standard EMA uses alpha = 2/(n+1). Wilder uses alpha = 1/n. Wilder's method gives more weight to older data — it's more stable for volatility measurement.

---

### 📊 Grid Strategy (`app/strategy/grid.py`)

**Flow when `on_candle(candle)` is called:**
```python
def on_candle(self, candle):
    self._candle_buffer.append(candle)             # Step 1: store candle
    if len(buffer) < 15: return []                  # Step 2: wait for ATR warm-up
    self._last_atr = self._compute_atr()            # Step 3: recompute ATR
    if not self._grid.is_initialised:               # Step 4: build grid once
        self._initialise_grid(candle)
        return []
    signals = self._check_entry_signals(candle)     # Step 5: check buys/sells
    signals += self._check_exit_signals(candle)     # Step 6: check TP/SL
    return signals
```

**Grid initialisation:**
```python
ref = candle.mid_price                # Reference = current price
spacing = ATR × atr_multiplier        # e.g. 100 × 1.5 = 150

# Create 10 levels each side
for i in 1..10:
    long_levels.append(ref - spacing × i)   # Buy levels below
    short_levels.append(ref + spacing × i)  # Sell levels above
```

---

### 🛑 Kill Switch (`app/risk/kill_switch.py`)

**Key design:** It's a one-way door. Once activated, it cannot be reversed within the session.
```python
def activate(self, reason, portfolio=None):
    if self._activated:               # Already on → ignore
        return existing_event
    self._activated = True            # Cannot be undone
    self._activated_at = datetime.utcnow()
    # Notify all listeners (strategy, order manager, alert system)
    for listener in self._listeners:
        listener(event)
```

**Integrate in simulation loop:**
```python
async for candle in ws_server.candle_stream():
    if kill_switch.is_triggered:     # Check EVERY tick
        break                         # Stop all trading
    signals = strategy.on_candle(candle)
```

---

### 📦 Order Manager (`app/execution/order_manager.py`)

**Idempotency pattern:**
```python
async def submit(self, order):
    async with self._lock:                        # Thread-safe
        if order.client_order_id in self._pending: # Already seen?
            return self._pending[order.client_order_id]  # Return existing!
        self._pending[order.client_order_id] = order
        self._store.upsert_order(order)           # Persist BEFORE broker call
    filled = await self._broker.place_order(order) # Then place with broker
```

**Why persist BEFORE the broker call?**
If the broker call succeeds but the process crashes immediately after — the order is in DuckDB. On restart we know it was placed and can reconcile with broker to get the fill status.

---

### 🔄 Backtest Engine (`app/backtest/engine.py`)

**The "next bar fill" rule (no look-ahead):**
```python
# Bar N: strategy produces signals
signals = strategy.on_candle(candle_N)
orders  = [signal_to_order(s) for s in signals]
pending_orders.extend(orders)          # Queue them

# Bar N+1: fill queued orders at OPEN of THIS bar
for order in pending_orders:
    fill_price = candle_N1.open ± slippage   # N+1's open!
    charges    = brokerage.compute(order, fill_price)
    execute_fill(order, fill_price, charges)
pending_orders.clear()
```

**Why next bar?** In reality, you cannot see bar N's close and place an order that fills at bar N's close. That's impossible. You see bar N's close, submit order, and it fills at bar N+1's open when the market opens.

---

### 🌡️ Macro Regime Engine (`app/macro/regime.py`)

**Scoring logic (in `app/macro/scoring.py`):**
```python
# Each indicator scored -2 to +2
vix_score    = +2 if vix<15 else +1 if vix<25 else -1 if vix<35 else -2
rupee_score  = +1 if usdinr<82 else 0 if usdinr<85 else -1
crude_score  = +1 if crude<70 else 0 if crude<90 else -1
yield_score  = +1 if yield<7 else 0 if yield<8 else -1

total_score = vix_score + rupee_score + crude_score + yield_score

# Map to regime
if score >= 4:   → BULL
elif score >= 1: → SIDEWAYS
elif score >= -2:→ BEAR
else:            → RISK_OFF
```

**Override application:**
```python
# BEAR regime → wider grid, fewer positions
REGIME_OVERRIDES[BEAR] = {"atr_multiplier": 1.5, "max_positions": 6}
new_config = engine.apply_overrides(strategy_config, regime)
```

---

### 🏦 NSE Brokerage Model (`app/backtest/brokerage.py`)

**Charges computed:**
```python
turnover     = price × quantity × lot_size
brokerage    = min(₹20, 0.0003 × turnover)   # Zerodha flat/percentage
stt          = 0.00025 × turnover             # 0.025% on sell side (intraday)
txn_charges  = 0.0000345 × turnover           # NSE transaction charges
gst          = 0.18 × (brokerage + txn_charges)
sebi         = 0.000001 × turnover            # ₹10 per crore

total_charges = brokerage + stt + txn_charges + gst + sebi
net_pnl       = gross_pnl - total_charges
```

---

## 4. Indian Market Specifics You Must Know

### MIS vs NRML
| | MIS (Intraday) | NRML (Overnight) |
|---|---|---|
| Meaning | Must square off by 3:20 PM | Can hold overnight |
| Margin | ~20% of contract value | Full SPAN + exposure |
| Auto-square off | Yes, by broker at 3:20 PM | No |
| STT on sell | 0.025% | Different |

**Our engine uses MIS** (`ProductType.MIS`) because it's an intraday grid strategy.

### NSE F&O Basics
- **NIFTY:** India's benchmark index (50 stocks)
- **NIFTY Futures:** Contract to buy/sell NIFTY at a fixed price on expiry
- **Lot size:** 50 units for NIFTY (1 lot = 50 units × price = 1 contract value)
- **Expiry:** Last Thursday of every month
- **Tick size:** ₹0.05 (minimum price movement)

### MCX (Commodity Exchange)
- Trades commodities: Gold, Silver, Crude Oil, Natural Gas
- Different lot sizes: Gold = 1 kg, Crude = 100 barrels
- CTT (Commodity Transaction Tax) instead of STT
- Different margin requirements and circuit breakers

### STT vs CTT
| | STT | CTT |
|---|---|---|
| Full form | Securities Transaction Tax | Commodity Transaction Tax |
| Applies to | NSE equity + F&O | MCX commodities |
| Rate (intraday sell) | 0.025% | 0.01% |

---

## 5. Ten Most Likely Interview Questions + Answers

---

### Q1: "Walk me through the Grid Strategy. How does it work?"

**Answer:**
> "The grid strategy places buy orders at equal intervals below the current price, and sell orders above. The spacing is determined by ATR — which measures market volatility — so it adapts to current conditions.
>
> When the market dips and hits a buy level, we enter long. If it keeps falling, we pyramid — add more positions at lower levels, up to a cap. When the price recovers past a take-profit threshold (set as a multiple of ATR above our average entry price), we exit all longs. If it falls past our stop-loss threshold, we exit and cut losses.
>
> With stop-and-reverse enabled, if we're long and the market shoots up past a sell level, we reverse: close all longs and go short. This way we're always aligned with the trend direction."

---

### Q2: "What is ATR and why do you use it for grid spacing?"

**Answer:**
> "ATR is the Average True Range — it measures the typical candle-to-candle movement. True Range takes the biggest of three measurements: high-minus-low, gap-up from previous close, gap-down from previous close.
>
> We use it for spacing because fixed spacing (like 50 points) breaks down in different volatility regimes. In a calm market, 50 points is huge — you'd almost never trigger. In a volatile market, 50 points is noise — you'd trigger constantly. ATR × 1.5 adapts: wide in volatile periods, tight in calm periods. This is the core of ATR-based dynamic position sizing."

---

### Q3: "How does your kill switch work? When does it trigger?"

**Answer:**
> "The kill switch is a one-way door: once activated, it cannot be reversed within the session. It stores the activation time and reason, then notifies all registered listeners — the order manager stops accepting new orders, the alert manager sends a notification.
>
> In the current implementation it can be triggered manually with `activate(reason)`, or integrated with risk monitoring to auto-trigger when: daily loss exceeds the limit, VIX exceeds the circuit breaker threshold (40 in our config), or consecutive losses breach the maximum.
>
> The reason it's irreversible is deliberate: in a crisis, you don't want automated code to restart trading. A human must restart the process."

---

### Q4: "Explain idempotent order placement."

**Answer:**
> "Idempotency means: submitting the same request twice has the same effect as submitting it once. For orders, this means if you accidentally send the same order twice — due to a network retry, a bug, or a WebSocket reconnect — you should not get two fills.
>
> We implement this with a `client_order_id`: a UUID we generate and attach to every order. Before submitting, the OrderManager checks if this ID is already in its in-memory `_pending` dict. If yes, it returns the existing order without calling the broker. We also persist the order to DuckDB before the broker call — so even if we crash between persisting and getting the broker confirmation, we can reconcile on restart."

---

### Q5: "How does your backtest avoid look-ahead bias?"

**Answer:**
> "Look-ahead bias happens when your strategy uses future data to make past decisions — for example, using bar N's close to fill an order at bar N's close. That's impossible in live trading.
>
> Our engine queues signals from bar N but only fills them at bar N+1's open price. So if bar N generates a buy signal, the fill happens at the next bar's open, plus slippage. This accurately simulates what would happen in live trading where you see a bar close, send the order, and it fills when the next bar opens."

---

### Q6: "What is walk-forward testing and why is it important?"

**Answer:**
> "Walk-forward is a form of out-of-sample testing that prevents overfitting. Instead of training on all your historical data and testing on the same data (which always looks great but is useless), you split into rolling windows.
>
> Train on 100 bars, test on the next 50. Slide 50 bars forward, train on the next 100, test on the next 50. Repeat. Each test window is always future data relative to its training window. The aggregate of all test windows tells you how the strategy performs on data it has never seen.
>
> Our `WalkForwardEngine` automates this. You provide a `strategy_factory` function, and it creates a fresh strategy instance for each window — no state bleed between windows."

---

### Q7: "How do you handle crashes and reconnects?"

**Answer:**
> "We have three layers.
>
> First, every order is persisted to DuckDB synchronously before the broker call. So we never lose an order's existence.
>
> Second, the `OrderManager.restore_from_db()` method loads all non-terminal orders on startup. This rebuilds the in-memory `_pending` dict.
>
> Third, `reconcile()` compares local order states with broker states. If local says OPEN but broker says FILLED, we update local. This handles the scenario where the broker filled an order while we were down.
>
> For WebSocket, the `ZerodhaWebSocketClient` has an auto-reconnect loop with exponential backoff: wait 2s, then 4s, then 8s up to 30s. After reconnecting, it re-subscribes to the same instruments."

---

### Q8: "Explain the Macro Regime Engine."

**Answer:**
> "The macro regime engine classifies the current market environment into four states: BULL, BEAR, RISK_OFF, or SIDEWAYS. It uses macro proxies — VIX, USDINR, crude oil, and 10-year bond yield — because these are leading indicators of institutional money flow.
>
> Each variable gets an independent score from -2 to +2. They're summed into a composite score. Score ≥ 4 = BULL, 1–3 = SIDEWAYS, -2–0 = BEAR, below -2 = RISK_OFF.
>
> Different regimes apply different strategy parameters: in RISK_OFF, we widen the grid (2×ATR), reduce max positions to 4, and cut position size to 50%. In BULL, we tighten the grid (1×ATR) and max out positions.
>
> There's also a circuit breaker: if VIX exceeds 40, no new positions at all, regardless of other signals."

---

### Q9: "Why asyncio? When would threading be wrong here?"

**Answer:**
> "Asyncio is appropriate because our bottlenecks are I/O-bound: waiting for WebSocket messages, waiting for broker API responses. Asyncio's event loop handles thousands of coroutines with a single thread — zero thread-switching overhead.
>
> Threading would be wrong because Python's GIL (Global Interpreter Lock) means only one thread runs Python code at a time. For CPU-bound tasks like indicator computation, you'd use multiprocessing. But for network I/O, asyncio is more efficient.
>
> We use `asyncio.Lock()` in the OrderManager's `submit()` to prevent race conditions where two coroutines might both see the `_pending` dict as missing the same order_id and submit duplicates."

---

### Q10: "How do your tests ensure correctness?"

**Answer:**
> "We have 136 tests covering every module. Each strategy change ships with a regression test — a test that explicitly captures the bug scenario. For example, the grid exit tests verify that after opening a long, sending a candle with high above the TP level produces exactly one `EXIT_LONG` signal and clears all open positions.
>
> We use `pytest` with fixtures for consistent test setup. Async tests use `pytest-asyncio`. We test indicators mathematically — for example, EMA on a linearly increasing sequence must be monotonically increasing. We test idempotency explicitly — submitting the same order twice produces one broker call.
>
> Coverage is at 66% overall — higher for core modules like strategy (94%), risk (90%), indicators (90%+)."

---

## 6. Demo Order for Screen Share

If they ask you to walk through the code live, do it in this order:

### Step 1: Show the project runs (30 seconds)
```bash
cd "c:\Users\ANKIT KUMAR GUPTA\OneDrive\Desktop\Quant_Assignment"
python main.py backtest
```
Let them see the P&L output:
```
============================================================
  BACKTEST RESULTS
============================================================
  total_trades                 18
  win_rate_pct                 38.89
  total_net_pnl                1144.91
  sharpe_ratio                 -1.3769
  profit_factor                1.991
============================================================
```

### Step 2: Show tests pass (30 seconds)
```bash
python -m pytest tests/ -q --no-cov
# → 136 passed
```

### Step 3: Walk through grid.py (2 minutes)
Open `app/strategy/grid.py`. Point to:
1. `on_candle()` — the main loop
2. `_initialise_grid()` — ATR-based spacing
3. `_check_entry_signals()` — pyramid / SAR logic
4. `_check_exit_signals()` — TP/SL

### Step 4: Walk through order_manager.py (1 minute)
Open `app/execution/order_manager.py`. Point to:
1. `submit()` — idempotency check + DuckDB persist
2. `restore_from_db()` — crash recovery

### Step 5: Walk through a test (1 minute)
Open `tests/test_grid_strategy.py`. Show `test_take_profit_closes_longs`.
Explain: warmup 16 candles → open long → send TP candle → assert EXIT_LONG.

### Step 6: Show brokerage calculation (30 seconds)
Open `app/backtest/brokerage.py`. Show the NSE charges formula.
Say: "This is production-grade — it matches Zerodha's actual charge sheet to the paisa."

---

## 7. Quick-Recall One-Liners

Memorize these for rapid-fire questions:

| Topic | One-liner |
|---|---|
| ATR | "Volatility-adaptive measure of market range; seed with SMA, then Wilder's RMA" |
| Grid strategy | "Buy at equal intervals below price, sell above; ATR sets the spacing" |
| Pyramiding | "Add to position at lower levels; capped by max_positions" |
| Stop-and-reverse | "Hit opposite level while positioned → close all + go other side" |
| Kill switch | "Irreversible one-way door; stops all new orders, alerts operator" |
| Idempotency | "client_order_id deduplication; persist before broker call" |
| Crash recovery | "restore_from_db() reloads non-terminal orders; reconcile() syncs with broker" |
| Backtest | "Signals on bar N fill at bar N+1 open ± slippage; no look-ahead" |
| Walk-forward | "Rolling train/test windows; measures out-of-sample performance" |
| Macro regime | "VIX + USDINR + Crude + Bond yield scored → BULL/BEAR/RISK_OFF/SIDEWAYS" |
| DuckDB | "Embedded analytical DB; no server; SQL; crash-safe persistence" |
| Slippage | "Fixed % of fill price; models market impact for realistic backtest costs" |
| STT | "Tax on equity/F&O sells: 0.025% intraday, 0.1% delivery" |
| asyncio | "Event-loop for I/O-bound ops; single thread; asyncio.Lock for thread-safety" |
| Sharpe ratio | "(Mean return - risk free rate) / std dev × √252; >1 is good" |
| Max drawdown | "Largest peak-to-trough loss; e.g. ₹12L → ₹9L = 25%" |
| Structured logs | "JSON logs with event/level/timestamp; machine-readable for alerting" |

---

## ⚡ Key Files to Have Open During Interview

| Purpose | File |
|---|---|
| Core strategy | `app/strategy/grid.py` |
| ATR indicator | `app/indicators/atr.py` |
| Order management | `app/execution/order_manager.py` |
| Kill switch | `app/risk/kill_switch.py` |
| Backtest engine | `app/backtest/engine.py` |
| Brokerage charges | `app/backtest/brokerage.py` |
| Macro regime | `app/macro/regime.py` |
| Data models | `app/domain/models.py` |
| Strategy tests | `tests/test_grid_strategy.py` |
| Indicator tests | `tests/test_indicators.py` |

---

> **Final tip:** The interviewers are testing if you *understand* what you built, not just whether you can copy code.
> Before the interview, run `python main.py backtest` once and read the output. Be ready to explain every number in the result table.
