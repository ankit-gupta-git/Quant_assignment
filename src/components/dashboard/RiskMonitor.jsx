import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { summaryMetrics } from '../../data/metricsData';

export default function RiskMonitor() {
  const m = summaryMetrics;
  const positionUtilPct = (m.currentPositionUnits / m.positionCapUnits) * 100;

  return (
    <Card
      title="RISK MONITOR"
      subtitle="Operational gateways"
      headerAction={<Badge variant="success" size="xs">STATUS: NORMAL</Badge>}
    >
      <div className="font-mono text-[11px] space-y-1 select-none">
        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Daily P&L:</span>
          <span className={`font-semibold tabular-nums ${m.dailyPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
            {m.dailyPnl >= 0 ? '+' : ''}₹{m.dailyPnl.toFixed(2)}
          </span>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Daily Loss Limit:</span>
          <div className="flex items-center gap-1">
            <span className="text-slate-200 tabular-nums">₹{m.dailyLossLimit.toLocaleString('en-IN')}</span>
            <span className="text-[9px] text-slate-500">(Cap)</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Current Drawdown:</span>
          <div className="flex items-center gap-1">
            <span className="text-slate-200 tabular-nums">-{m.currentDrawdownPct.toFixed(2)}%</span>
            <span className="text-[9px] text-slate-500">/ 10.0% Max</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Position Size:</span>
          <div className="flex items-center gap-1">
            <span className="text-slate-200 font-semibold tabular-nums">{m.currentPositionUnits}</span>
            <span className="text-slate-500">/ {m.positionCapUnits} units</span>
            <span className="text-[9px] text-slate-500">({positionUtilPct.toFixed(0)}%)</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Consecutive Losses:</span>
          <div className="flex items-center gap-1">
            <span className="text-slate-200 tabular-nums">{m.maxConsecutiveLosses}</span>
            <span className="text-slate-500">/ {m.consecutiveLossLimit} Limit</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-0.5">
          <span className="text-slate-500">Kill Switch:</span>
          <Badge variant="warning" size="xs">
            ARMED
          </Badge>
        </div>

        {/* Flat 1px progress gauge for gross exposure */}
        <div className="mt-1 pt-1.5 border-t border-[#141b28] space-y-1">
          <div className="flex justify-between text-[9px] text-slate-500">
            <span>GROSS EXPOSURE:</span>
            <span className="text-slate-300 tabular-nums">₹{m.portfolioExposure.toLocaleString('en-IN')} / ₹1,000,000 (1.76%)</span>
          </div>
          <div className="w-full bg-[#07090e] border border-[#1a2231] h-1.5">
            <div className="bg-sky-500 h-full" style={{ width: '1.76%' }}></div>
          </div>
        </div>
      </div>
    </Card>
  );
}
