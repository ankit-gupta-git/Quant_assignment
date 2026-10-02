import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { strategyConfigData } from '../../data/strategyConfigData';

export default function StrategyState() {
  const s = strategyConfigData;

  return (
    <Card
      title="STRATEGY STATE"
      subtitle="ATR Grid + Parabolic SAR"
      headerAction={<Badge variant="success" size="xs">ARMED</Badge>}
    >
      <div className="font-mono text-[11px] space-y-1 select-none">
        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Strategy:</span>
          <span className="text-slate-200 font-semibold">{s.activeStrategy}</span>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Instrument:</span>
          <span className="text-slate-200 font-medium">{s.instrument} / {s.exchange}</span>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Timeframe:</span>
          <span className="text-sky-300 font-medium">{s.timeframe} [OHLC]</span>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">ATR ({s.atrPeriod}):</span>
          <span className="text-slate-200 tabular-nums">{s.atrValue.toFixed(2)} pts</span>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Grid Spacing:</span>
          <div className="flex items-center gap-1">
            <span className="text-slate-200 font-semibold tabular-nums">{s.gridSpacing.toFixed(2)} pts</span>
            <span className="text-[9px] text-slate-500">({s.atrMultiplier}x)</span>
          </div>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Position:</span>
          <div className="flex items-center gap-1.5">
            <Badge variant="buy" size="xs">
              {s.currentPosition} ({s.currentPositionUnits})
            </Badge>
            <span className="text-emerald-400 font-semibold tabular-nums">
              +₹{s.unrealizedPnl.toFixed(2)}
            </span>
          </div>
        </div>

        <div className="flex items-center justify-between py-0.5 border-b border-[#141b28]">
          <span className="text-slate-500">Regime:</span>
          <Badge variant="warning" size="xs">
            HIGH_VOLATILITY
          </Badge>
        </div>

        <div className="flex items-center justify-between py-0.5">
          <span className="text-slate-500">Signal:</span>
          <Badge variant="info" size="xs">
            HOLD / MONITOR
          </Badge>
        </div>

        {/* Micro boundary targets */}
        <div className="mt-1 pt-1.5 border-t border-[#141b28] grid grid-cols-2 gap-2 text-[10px]">
          <div>
            <span className="text-slate-500 block text-[9px]">TP TARGET:</span>
            <span className="text-emerald-400 font-semibold tabular-nums">₹{s.takeProfitTarget.toFixed(2)}</span>
          </div>
          <div>
            <span className="text-slate-500 block text-[9px]">SAR STOP:</span>
            <span className="text-rose-400 font-semibold tabular-nums">₹{s.sarTrailingStop.toFixed(2)}</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
