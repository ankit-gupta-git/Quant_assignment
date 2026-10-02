import React from 'react';
import StatModule from '../common/StatModule';
import { summaryMetrics } from '../../data/metricsData';

export default function MetricStrip() {
  const m = summaryMetrics;

  const formatCurrency = (val) => {
    const sign = val >= 0 ? '+' : '-';
    return `${sign}₹${Math.abs(val).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div className="bg-[#090d14] border border-[#1a2231] grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-x divide-y sm:divide-y-0 divide-[#1a2231]">
      <StatModule
        label="NET P&L"
        value={formatCurrency(m.netPnl)}
        valueColor={m.netPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}
        subtext={`GROSS: ₹${m.grossPnl.toFixed(2)} | CHG: ₹${m.charges.toFixed(2)}`}
        trend={m.netPnl >= 0 ? 'up' : 'down'}
      />
      <StatModule
        label="TOTAL TRADES"
        value={m.totalTrades}
        valueColor="text-slate-100"
        subtext={`${m.winningTrades} WINS / ${m.losingTrades} LOSS`}
      />
      <StatModule
        label="WIN RATE"
        value={`${m.winRatePct.toFixed(1)}%`}
        valueColor={m.winRatePct >= 50 ? 'text-emerald-400' : 'text-amber-400'}
        subtext={`W/L RATIO: ${m.winLossRatio}x`}
      />
      <StatModule
        label="SHARPE RATIO"
        value={m.sharpeRatio.toFixed(2)}
        valueColor={m.sharpeRatio >= 1.0 ? 'text-emerald-400' : m.sharpeRatio >= 0 ? 'text-slate-200' : 'text-amber-400'}
        subtext={`CALMAR: ${m.calmarRatio} | SORTINO: ${m.sortinoRatio}`}
      />
      <StatModule
        label="MAX DRAWDOWN"
        value={`-${m.maxDrawdownPct.toFixed(2)}%`}
        valueColor="text-rose-400"
        subtext={`CURRENT DD: -${m.currentDrawdownPct.toFixed(2)}%`}
        trend="down"
      />
      <StatModule
        label="PROFIT FACTOR"
        value={m.profitFactor.toFixed(2)}
        valueColor={m.profitFactor >= 1.5 ? 'text-emerald-400' : 'text-slate-200'}
        subtext={`EXPECTANCY: +₹${m.expectancyPerTrade.toFixed(2)}`}
      />
    </div>
  );
}
