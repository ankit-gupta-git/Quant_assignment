import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { strategyConfigData } from '../../data/strategyConfigData';
import { ArrowRight } from 'lucide-react';

export default function StrategyPage() {
  const s = strategyConfigData;

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Banner */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">STRATEGY EXECUTION ENGINE</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">ATR Grid + Parabolic Stop-and-Reverse</span>
        </div>
        <Badge variant="success" size="xs">
          ARMED
        </Badge>
      </div>

      {/* Visual Workflow Pipelines (2 Columns: Grid Strategy & SAR Strategy) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        {/* 1. ATR Grid Pipeline */}
        <Card
          title="ATR GRID STRATEGY"
          subtitle="Execution pipeline"
        >
          {/* Engineering Pipeline Flow */}
          <div className="flex items-center justify-between gap-1 p-1.5 bg-[#090d14] border border-[#1a2231] text-[10px] mb-2">
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">ATR</span>
              <span className="font-semibold text-sky-300">{s.atrValue.toFixed(1)}</span>
            </div>
            <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">Spacing</span>
              <span className="font-semibold text-amber-300">{s.gridSpacing.toFixed(1)}p</span>
            </div>
            <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">Levels</span>
              <span className="font-semibold text-emerald-300">20 Ladder</span>
            </div>
            <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">Position</span>
              <span className="font-semibold text-slate-200">Pyramid/TP</span>
            </div>
          </div>

          {/* Current Parameters */}
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Reference Price:</span>
              <span className="text-slate-200 tabular-nums font-semibold">₹{s.referencePrice.toFixed(2)}</span>
            </div>
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Grid Spacing:</span>
              <span className="text-slate-200 tabular-nums">{s.gridSpacing.toFixed(2)} points ({s.atrMultiplier}x ATR)</span>
            </div>
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Take Profit:</span>
              <span className="text-emerald-400 tabular-nums">
                Entry ± {s.takeProfitDistance.toFixed(2)} pts ({s.takeProfitMultiplier}x ATR)
              </span>
            </div>
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Stop Loss:</span>
              <span className="text-rose-400 tabular-nums">
                Entry ∓ {s.stopLossDistance.toFixed(2)} pts ({s.stopLossMultiplier}x ATR)
              </span>
            </div>
            <div className="flex justify-between py-0.5">
              <span className="text-slate-500">Pyramiding:</span>
              <span className="text-slate-200">ENABLED (Max 3 Layers • Min step 1.0x ATR)</span>
            </div>
          </div>
        </Card>

        {/* 2. Parabolic SAR Pipeline */}
        <Card
          title="STOP-AND-REVERSE (SAR)"
          subtitle="Reversal pipeline"
        >
          {/* Engineering Pipeline Flow */}
          <div className="flex items-center justify-between gap-1 p-1.5 bg-[#090d14] border border-[#1a2231] text-[10px] mb-2">
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">SAR</span>
              <span className="font-semibold text-sky-300">Trailing Stop</span>
            </div>
            <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">Trigger</span>
              <span className="font-semibold text-rose-300">Trend Reversal</span>
            </div>
            <ArrowRight className="w-3 h-3 text-slate-500 shrink-0" />
            <div className="text-center p-1 bg-[#101622] border border-[#1a2231] flex-1">
              <span className="text-slate-500 uppercase block text-[8px]">Execution</span>
              <span className="font-semibold text-emerald-300">Position Flip</span>
            </div>
          </div>

          {/* Current Parameters */}
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Current Direction:</span>
              <Badge variant="buy" size="xs">LONG (1 Unit)</Badge>
            </div>
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Trailing Stop:</span>
              <span className="text-rose-400 tabular-nums font-semibold">₹{s.sarTrailingStop.toFixed(2)}</span>
            </div>
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Reversal Gap:</span>
              <span className="text-slate-200 tabular-nums font-semibold">-463.76 pts (-2.63%)</span>
            </div>
            <div className="flex justify-between py-0.5">
              <span className="text-slate-500">Order Routing:</span>
              <span className="text-slate-300">Idempotent Market Order • Instant Reversal</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Live 20-Level Price Ladder */}
      <Card
        title="20-LEVEL GRID MATRIX"
        subtitle="Order book bounds"
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto select-none">
          <table className="w-full text-left font-mono terminal-table">
            <thead>
              <tr>
                <th>Level</th>
                <th>Side</th>
                <th className="text-right">Price</th>
                <th className="text-right">Distance</th>
                <th>Status</th>
                <th>Fill ID</th>
              </tr>
            </thead>
            <tbody>
              {s.gridLevels.map((lvl) => {
                const isAbove = lvl.level > 0;
                return (
                  <tr
                    key={lvl.level}
                    className={`border-b border-[#101622] ${
                      lvl.status === 'FILLED' ? 'bg-[#101824]' : 'hover:bg-[#0f1420]'
                    }`}
                  >
                    <td className={`font-semibold ${isAbove ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {lvl.level > 0 ? `+L${lvl.level}` : `-L${Math.abs(lvl.level)}`}
                    </td>
                    <td>
                      <Badge variant={isAbove ? 'sell' : 'buy'} size="xs">
                        {lvl.type.split(' / ')[0]}
                      </Badge>
                    </td>
                    <td className="text-right font-semibold text-slate-200">
                      ₹{lvl.price.toFixed(2)}
                    </td>
                    <td className="text-right text-slate-500 text-[10px]">
                      {lvl.distancePct}
                    </td>
                    <td>
                      <span className={`text-[9px] px-1 py-0.2 border ${
                        lvl.status === 'FILLED'
                          ? 'text-emerald-400 bg-emerald-950/80 border-emerald-800'
                          : 'text-slate-500 bg-slate-900 border-[#1a2231]'
                      }`}>
                        {lvl.status}
                      </span>
                    </td>
                    <td className="text-slate-400 text-[10px]">
                      {lvl.fillId || '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
