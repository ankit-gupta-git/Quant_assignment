import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';
import Card from '../common/Card';
import { equityTimeframeSlices, equityCurveAll } from '../../data/equityCurveData';
import { summaryMetrics } from '../../data/metricsData';

export default function EquityChart() {
  const [timeframe, setTimeframe] = useState('ALL');
  const [viewMode, setViewMode] = useState('equity'); // 'equity' | 'drawdown'

  const activeData = equityTimeframeSlices[timeframe] || equityCurveAll;
  const m = summaryMetrics;

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#070a0f] border border-[#2a374d] p-2 font-mono text-[11px] shadow-none rounded-none select-none min-w-[200px]">
          <div className="text-[9px] text-slate-500 border-b border-[#1a2231] pb-1 mb-1 flex justify-between">
            <span>BAR / TIME:</span>
            <span className="text-slate-200">{label || data.date || data.time}</span>
          </div>
          <div className="space-y-0.5 text-[11px]">
            <div className="flex justify-between items-center">
              <span className="text-slate-500">EQUITY:</span>
              <span className="text-slate-100 font-semibold tabular-nums">
                ₹{data.equity?.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500">NET P&L:</span>
              <span className={`font-semibold tabular-nums ${data.pnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                {data.pnl >= 0 ? '+' : ''}₹{data.pnl?.toFixed(2)}
              </span>
            </div>
            {data.drawdown !== undefined && (
              <div className="flex justify-between items-center">
                <span className="text-slate-500">DRAWDOWN:</span>
                <span className="text-rose-400 tabular-nums">
                  {data.drawdown === 0 ? '0.00%' : `${data.drawdown.toFixed(2)}%`}
                </span>
              </div>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <Card
      title="EQUITY CURVE & SYSTEM TELEMETRY"
      subtitle="Anti-lookahead event execution"
      className="w-full"
      headerAction={
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex items-center border border-[#1a2231] font-mono text-[9px]">
            <button
              onClick={() => setViewMode('equity')}
              className={`px-1.5 py-0.5 transition-none ${
                viewMode === 'equity'
                  ? 'bg-[#152030] text-sky-300 font-semibold'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              EQUITY
            </button>
            <button
              onClick={() => setViewMode('drawdown')}
              className={`px-1.5 py-0.5 border-l border-[#1a2231] transition-none ${
                viewMode === 'drawdown'
                  ? 'bg-[#152030] text-rose-300 font-semibold'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              DRAWDOWN
            </button>
          </div>

          {/* Timeframe Controls */}
          <div className="flex items-center border border-[#1a2231] font-mono text-[9px]">
            {['1D', '1W', '1M', 'ALL'].map((tf, idx) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-1.5 py-0.5 transition-none ${
                  idx > 0 ? 'border-l border-[#1a2231]' : ''
                } ${
                  timeframe === tf
                    ? 'bg-[#152030] text-sky-300 font-semibold'
                    : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>
      }
    >
      {/* Top Embedded Metric Mini Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2 pb-1.5 border-b border-[#141b28] font-mono text-xs">
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] text-slate-500 uppercase">INITIAL:</span>
          <span className="text-slate-200 font-semibold tabular-nums text-xs">
            ₹{m.initialCapital.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] text-slate-500 uppercase">CURRENT:</span>
          <span className="text-emerald-400 font-semibold tabular-nums text-xs">
            ₹{m.currentEquity.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] text-slate-500 uppercase">PEAK:</span>
          <span className="text-slate-200 font-semibold tabular-nums text-xs">
            ₹{m.peakEquity.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-[9px] text-slate-500 uppercase">MAX DD:</span>
          <span className="text-rose-400 font-semibold tabular-nums text-xs">
            -{m.maxDrawdownPct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Chart Canvas: Crisp flat lines, zero decorative gradients */}
      <div className="h-56 sm:h-64 w-full font-mono text-[9px]">
        <ResponsiveContainer width="100%" height="100%">
          {viewMode === 'equity' ? (
            <LineChart data={activeData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="1 3" stroke="#121824" vertical={false} />
              <XAxis
                dataKey={timeframe === 'ALL' ? 'date' : 'time'}
                stroke="#334155"
                tick={{ fill: '#64748b', fontSize: 9 }}
                tickLine={false}
                axisLine={{ stroke: '#1a2231' }}
              />
              <YAxis
                domain={['auto', 'auto']}
                stroke="#334155"
                tick={{ fill: '#64748b', fontSize: 9 }}
                tickLine={false}
                axisLine={{ stroke: '#1a2231' }}
                tickFormatter={(val) => `₹${(val / 1000).toFixed(1)}k`}
                orientation="right"
              />
              <ReferenceLine y={1000000} stroke="#2a374d" strokeDasharray="2 2" />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="equity"
                stroke="#10b981"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          ) : (
            <LineChart data={activeData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="1 3" stroke="#121824" vertical={false} />
              <XAxis
                dataKey={timeframe === 'ALL' ? 'date' : 'time'}
                stroke="#334155"
                tick={{ fill: '#64748b', fontSize: 9 }}
                tickLine={false}
                axisLine={{ stroke: '#1a2231' }}
              />
              <YAxis
                domain={[-5.5, 0.5]}
                stroke="#334155"
                tick={{ fill: '#64748b', fontSize: 9 }}
                tickLine={false}
                axisLine={{ stroke: '#1a2231' }}
                tickFormatter={(val) => `${val.toFixed(1)}%`}
                orientation="right"
              />
              <ReferenceLine y={0} stroke="#334155" />
              <ReferenceLine y={-4.99} stroke="#ef4444" strokeDasharray="2 2" />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="stepAfter"
                dataKey="drawdown"
                stroke="#ef4444"
                strokeWidth={1.5}
                dot={false}
                isAnimationActive={false}
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
