import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { currentMacroSnapshot } from '../../data/macroData';

export default function MacroRegime() {
  const m = currentMacroSnapshot;
  const p = m.policyAdjustments;

  return (
    <Card
      title="MACRO REGIME"
      subtitle="Multi-proxy model"
      headerAction={<Badge variant="warning" size="xs">HIGH_VOLATILITY</Badge>}
    >
      <div className="font-mono text-[11px] space-y-1.5 select-none">
        {/* Macro Indicators 4-column compact grid */}
        <div className="grid grid-cols-2 gap-1 text-slate-300">
          <div className="bg-[#090d14] p-1.5 border border-[#1a2231]">
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>INDIA VIX</span>
              <span className="text-amber-400">{m.indiaVix.change}</span>
            </div>
            <div className="text-sm font-semibold text-slate-100 tabular-nums">
              {m.indiaVix.value}
            </div>
          </div>

          <div className="bg-[#090d14] p-1.5 border border-[#1a2231]">
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>USDINR</span>
              <span className="text-slate-400">{m.usdinr.change}</span>
            </div>
            <div className="text-sm font-semibold text-slate-100 tabular-nums">
              ₹{m.usdinr.value}
            </div>
          </div>

          <div className="bg-[#090d14] p-1.5 border border-[#1a2231]">
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>BRENT CRUDE</span>
              <span className="text-emerald-400">{m.brentCrude.change}</span>
            </div>
            <div className="text-sm font-semibold text-slate-100 tabular-nums">
              ${m.brentCrude.value.toFixed(1)}
            </div>
          </div>

          <div className="bg-[#090d14] p-1.5 border border-[#1a2231]">
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>10Y G-SEC</span>
              <span className="text-emerald-400">{m.tenYearYield.change}</span>
            </div>
            <div className="text-sm font-semibold text-slate-100 tabular-nums">
              {m.tenYearYield.value}%
            </div>
          </div>
        </div>

        {/* Dynamic Policy Impacts */}
        <div className="pt-1 border-t border-[#141b28] space-y-1 text-[10px]">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Grid multiplier:</span>
            <div className="flex items-center gap-1">
              <span className="text-amber-400 font-semibold tabular-nums">{p.gridMultiplier}</span>
              <span className="text-slate-600">(Norm: {p.normalGridMultiplier})</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-500">Position sizing:</span>
            <div className="flex items-center gap-1">
              <span className="text-amber-400 font-semibold tabular-nums">{p.positionSizing}</span>
              <span className="text-slate-600">({p.maxPositionsAllowed} max)</span>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <span className="text-slate-500">Circuit breaker:</span>
            <span className="text-emerald-400 font-semibold">
              {p.circuitBreakerStatus}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
