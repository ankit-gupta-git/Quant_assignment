import React, { useState } from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import StatModule from '../common/StatModule';
import { summaryMetrics, nseChargesBreakdown } from '../../data/metricsData';
import { tradesData } from '../../data/tradesData';
import { equityCurveAll } from '../../data/equityCurveData';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  LineChart,
  Line,
  ReferenceLine
} from 'recharts';
import { Play, RotateCcw } from 'lucide-react';

export default function BacktestPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [progressStep, setProgressStep] = useState('');

  // Controls
  const [instrument, setInstrument] = useState('NIFTY');
  const [strategy, setStrategy] = useState('ATR Grid');
  const [startDate, setStartDate] = useState('2023-01-02');
  const [endDate, setEndDate] = useState('2024-12-06');
  const [initialCapital, setInitialCapital] = useState(1000000);
  const [slippagePct, setSlippagePct] = useState(0.05);
  const [brokeragePct, setBrokeragePct] = useState(0.03);
  const [positionSize, setPositionSize] = useState(50);

  const m = summaryMetrics;

  const handleRunBacktest = () => {
    setIsRunning(true);
    setProgressStep('Ingesting sample_ohlc.csv (500 bars)...');

    setTimeout(() => {
      setProgressStep('Computing vectorized ATR(14) & Grid level anchors...');
    }, 400);

    setTimeout(() => {
      setProgressStep('Simulating bar-by-bar fills with anti-lookahead & 0.05% slippage...');
    }, 900);

    setTimeout(() => {
      setProgressStep('Calculating statutory NSE charges (STT, GST, SEBI, Turnover)...');
    }, 1400);

    setTimeout(() => {
      setIsRunning(false);
      setProgressStep('');
    }, 1900);
  };

  const tradeDistribution = tradesData.map((t, idx) => ({
    name: `#${idx + 1}`,
    pnl: t.netPnl,
    tradeId: t.tradeId
  }));

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Notice */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">HISTORICAL BACKTEST ENGINE</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">Anti-lookahead event execution with NSE charges</span>
        </div>
        <div className="text-[10px] text-amber-400">
          Demo visualization — execution handled by the Python engine.
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
        {/* Left: Controls Panel */}
        <Card
          title="BACKTEST CONTROLS"
          subtitle="Model parameters"
          className="lg:col-span-1"
        >
          <div className="space-y-2 text-[11px]">
            {/* Instrument */}
            <div>
              <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Instrument</span>
              <select
                value={instrument}
                onChange={(e) => setInstrument(e.target.value)}
                className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-2 py-1 text-xs focus:outline-none"
              >
                <option value="NIFTY">NIFTY</option>
                <option value="BANKNIFTY">BANKNIFTY</option>
              </select>
            </div>

            {/* Strategy */}
            <div>
              <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Strategy</span>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-2 py-1 text-xs focus:outline-none"
              >
                <option value="ATR Grid">ATR Grid</option>
                <option value="SAR">Parabolic SAR</option>
              </select>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-2 gap-1.5">
              <div>
                <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Start Date</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-1.5 py-0.5 text-[10px] focus:outline-none"
                />
              </div>
              <div>
                <span className="text-[9px] uppercase text-slate-500 block mb-0.5">End Date</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-1.5 py-0.5 text-[10px] focus:outline-none"
                />
              </div>
            </div>

            {/* Initial Capital */}
            <div>
              <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Initial Capital</span>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-2 py-1 text-xs focus:outline-none tabular-nums"
              />
            </div>

            {/* Slippage & Brokerage */}
            <div className="grid grid-cols-2 gap-1.5">
              <div>
                <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Slippage (%)</span>
                <input
                  type="number"
                  step="0.01"
                  value={slippagePct}
                  onChange={(e) => setSlippagePct(Number(e.target.value))}
                  className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-2 py-1 text-xs focus:outline-none tabular-nums"
                />
              </div>
              <div>
                <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Brokerage (%)</span>
                <input
                  type="number"
                  step="0.01"
                  value={brokeragePct}
                  onChange={(e) => setBrokeragePct(Number(e.target.value))}
                  className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-2 py-1 text-xs focus:outline-none tabular-nums"
                />
              </div>
            </div>

            {/* Position Size */}
            <div>
              <span className="text-[9px] uppercase text-slate-500 block mb-0.5">Position Size (Qty)</span>
              <input
                type="number"
                value={positionSize}
                onChange={(e) => setPositionSize(Number(e.target.value))}
                className="w-full bg-[#080b11] border border-[#1a2231] text-slate-200 px-2 py-1 text-xs focus:outline-none tabular-nums"
              />
            </div>

            {/* Run Backtest Button */}
            <div className="pt-1">
              <button
                disabled={isRunning}
                onClick={handleRunBacktest}
                className={`w-full py-1.5 px-2 font-mono font-semibold text-xs flex items-center justify-center gap-1.5 border transition-none ${
                  isRunning
                    ? 'bg-slate-800 border-slate-700 text-slate-400 cursor-not-allowed'
                    : 'bg-[#0e241b] hover:bg-[#133226] border-emerald-700 text-emerald-300'
                }`}
              >
                {isRunning ? (
                  <>
                    <RotateCcw className="w-3 h-3 animate-spin text-sky-400" />
                    <span>SIMULATING ENGINE...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 fill-current" />
                    <span>RUN BACKTEST</span>
                  </>
                )}
              </button>
            </div>

            {isRunning && (
              <div className="bg-[#05070b] border border-[#1a2231] p-1.5 text-[10px] text-sky-400">
                <span>EXEC: {progressStep}</span>
              </div>
            )}
          </div>
        </Card>

        {/* Right: Results Strip, Equity curve, and Trade Distribution */}
        <div className="lg:col-span-2 space-y-2">
          {/* Results Metric Strip */}
          <div className="bg-[#090d14] border border-[#1a2231] grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-x divide-y sm:divide-y-0 divide-[#1a2231]">
            <StatModule
              label="NET P&L"
              value={`+₹${m.netPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
              valueColor="text-emerald-400"
              subtext="+0.11% on initial"
            />
            <StatModule
              label="SHARPE"
              value={m.sharpeRatio.toFixed(2)}
              valueColor="text-slate-200"
              subtext={`Calmar: ${m.calmarRatio}`}
            />
            <StatModule
              label="MAX DD"
              value={`-${m.maxDrawdownPct.toFixed(2)}%`}
              valueColor="text-rose-400"
              subtext="Historical low"
            />
            <StatModule
              label="WIN RATE"
              value={`${m.winRatePct.toFixed(1)}%`}
              valueColor="text-slate-200"
              subtext={`${m.winningTrades}W / ${m.losingTrades}L`}
            />
            <StatModule
              label="TRADES"
              value={m.totalTrades}
              valueColor="text-slate-200"
              subtext="18 roundtrips"
            />
            <StatModule
              label="PROFIT FACTOR"
              value={m.profitFactor.toFixed(2)}
              valueColor="text-emerald-400"
              subtext="Win / Loss ratio"
            />
          </div>

          {/* Equity Curve Minimal */}
          <Card
            title="EQUITY CURVE"
            subtitle="Backtest performance"
          >
            <div className="h-44 w-full font-mono text-[9px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={equityCurveAll} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="1 3" stroke="#121824" vertical={false} />
                  <XAxis dataKey="date" stroke="#334155" tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} />
                  <YAxis
                    domain={['auto', 'auto']}
                    stroke="#334155"
                    tick={{ fill: '#64748b', fontSize: 9 }}
                    tickLine={false}
                    orientation="right"
                    tickFormatter={(val) => `₹${(val / 1000).toFixed(1)}k`}
                  />
                  <ReferenceLine y={1000000} stroke="#2a374d" strokeDasharray="2 2" />
                  <Line
                    type="monotone"
                    dataKey="equity"
                    stroke="#10b981"
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Trade Distribution */}
          <Card
            title="TRADE DISTRIBUTION"
            subtitle="Net P&L per trade"
          >
            <div className="h-40 w-full font-mono text-[9px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tradeDistribution} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="1 3" stroke="#121824" vertical={false} />
                  <XAxis dataKey="name" stroke="#334155" tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} />
                  <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 9 }} tickLine={false} orientation="right" tickFormatter={(val) => `₹${val}`} />
                  <ReferenceLine y={0} stroke="#334155" />
                  <Bar dataKey="pnl" isAnimationActive={false}>
                    {tradeDistribution.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.pnl >= 0 ? '#10b981' : '#ef4444'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
