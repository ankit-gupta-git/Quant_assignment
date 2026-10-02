import React, { useState } from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { ShieldAlert, AlertTriangle } from 'lucide-react';

export default function RiskPage() {
  const [flattenTriggered, setFlattenTriggered] = useState(false);

  // Exact figures from prompt example
  const dailyLossCurrent = 8200;
  const dailyLossLimit = 20000;
  const drawdownCurrent = 3.4;
  const drawdownLimit = 10.0;
  const consecutiveLossesCurrent = 2;
  const consecutiveLossesLimit = 5;
  const positionCurrent = 100;
  const positionCap = 150;

  const handleFlattenPositions = () => {
    setFlattenTriggered(true);
    setTimeout(() => setFlattenTriggered(false), 3000);
  };

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Banner */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">RISK MANAGEMENT & CIRCUIT BREAKERS</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">Pre-trade gateways and exposure controls</span>
        </div>
        <div className="flex items-center gap-1.5 text-emerald-400">
          <span className="w-1.5 h-1.5 bg-emerald-500 inline-block"></span>
          <span>GATEWAYS ACTIVE</span>
        </div>
      </div>

      {/* Operational Controls Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
        {/* 1. Daily Loss Limit */}
        <Card
          title="DAILY LOSS LIMIT"
          subtitle="Intraday cap"
        >
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between items-baseline">
              <span className="text-slate-500">DAILY LOSS:</span>
              <span className="text-sm font-semibold text-slate-100 tabular-nums">
                ₹{dailyLossCurrent.toLocaleString('en-IN')} <span className="text-slate-500 text-xs">/ ₹{dailyLossLimit.toLocaleString('en-IN')}</span>
              </span>
            </div>
            <div className="w-full bg-[#07090e] border border-[#1a2231] h-1.5">
              <div
                className="bg-amber-400 h-full"
                style={{ width: `${(dailyLossCurrent / dailyLossLimit) * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>{((dailyLossCurrent / dailyLossLimit) * 100).toFixed(1)}% consumed</span>
              <span className="text-emerald-400">₹{(dailyLossLimit - dailyLossCurrent).toLocaleString('en-IN')} headroom</span>
            </div>
          </div>
        </Card>

        {/* 2. Drawdown Limit */}
        <Card
          title="DRAWDOWN LIMIT"
          subtitle="Peak-to-trough"
        >
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between items-baseline">
              <span className="text-slate-500">DRAWDOWN:</span>
              <span className="text-sm font-semibold text-rose-400 tabular-nums">
                {drawdownCurrent.toFixed(1)}% <span className="text-slate-500 text-xs">/ {drawdownLimit.toFixed(1)}%</span>
              </span>
            </div>
            <div className="w-full bg-[#07090e] border border-[#1a2231] h-1.5">
              <div
                className="bg-rose-500 h-full"
                style={{ width: `${(drawdownCurrent / drawdownLimit) * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>Current DD: -3.4%</span>
              <span>Tripwire: -10.0%</span>
            </div>
          </div>
        </Card>

        {/* 3. Consecutive Loss Limit */}
        <Card
          title="CONSECUTIVE LOSS LIMIT"
          subtitle="Martingale brake"
        >
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between items-baseline">
              <span className="text-slate-500">STREAK:</span>
              <span className="text-sm font-semibold text-slate-100 tabular-nums">
                {consecutiveLossesCurrent} <span className="text-slate-500 text-xs">/ {consecutiveLossesLimit}</span>
              </span>
            </div>
            <div className="grid grid-cols-5 gap-1 h-1.5">
              {[1, 2, 3, 4, 5].map((idx) => (
                <div
                  key={idx}
                  className={`h-full border border-[#1a2231] ${
                    idx <= consecutiveLossesCurrent ? 'bg-amber-400' : 'bg-[#07090e]'
                  }`}
                ></div>
              ))}
            </div>
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>Status: NORMAL</span>
              <span className="text-emerald-400">3 strikes remaining</span>
            </div>
          </div>
        </Card>

        {/* 4. Position Cap */}
        <Card
          title="POSITION CAP"
          subtitle="Inventory limit"
        >
          <div className="space-y-1.5 text-[11px]">
            <div className="flex justify-between items-baseline">
              <span className="text-slate-500">POSITION:</span>
              <span className="text-sm font-semibold text-slate-100 tabular-nums">
                {positionCurrent} <span className="text-slate-500 text-xs">/ {positionCap}</span>
              </span>
            </div>
            <div className="w-full bg-[#07090e] border border-[#1a2231] h-1.5">
              <div
                className="bg-sky-400 h-full"
                style={{ width: `${(positionCurrent / positionCap) * 100}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[9px] text-slate-500">
              <span>Utilization: 66.7%</span>
              <span className="text-slate-300">50 units headroom</span>
            </div>
          </div>
        </Card>

        {/* 5. Pyramiding */}
        <Card
          title="PYRAMIDING"
          subtitle="Layer spacing"
          headerAction={<Badge variant="success" size="xs">ENABLED</Badge>}
        >
          <div className="space-y-1 text-[11px]">
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Spacing Step:</span>
              <span className="text-slate-200 tabular-nums">1.0x ATR (154.6 pts)</span>
            </div>
            <div className="flex justify-between py-0.5 border-b border-[#141b28]">
              <span className="text-slate-500">Max Open Layers:</span>
              <span className="text-slate-200 tabular-nums">3 layers</span>
            </div>
            <div className="flex justify-between py-0.5">
              <span className="text-slate-500">Adverse Reject:</span>
              <span className="text-emerald-400">ACTIVE</span>
            </div>
          </div>
        </Card>

        {/* 6. Kill Switch */}
        <Card
          title="KILL SWITCH"
          subtitle="Emergency liquidation"
          headerAction={<Badge variant="warning" size="xs">ARMED</Badge>}
        >
          <div className="space-y-1.5 text-[11px]">
            <div className="flex items-center justify-between">
              <span className="text-slate-500">STATUS:</span>
              <span className="text-amber-400 font-semibold">ARMED (WATCHING 3 RULES)</span>
            </div>
            <div className="text-[9px] text-slate-500 bg-[#07090e] p-1 border border-[#1a2231]">
              Triggers: Loss &gt; ₹20k OR Drawdown &gt; 10% OR Streak &gt; 5.
            </div>
            <button
              onClick={handleFlattenPositions}
              className="w-full py-1 px-2 bg-[#220b0e] hover:bg-[#301115] border border-rose-800 text-rose-300 text-[10px] font-semibold flex items-center justify-center gap-1 transition-none"
            >
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              <span>TRIGGER EMERGENCY FLATTEN (MOCK)</span>
            </button>
          </div>
        </Card>
      </div>

      {flattenTriggered && (
        <div className="p-2 bg-[#220b0e] border border-rose-800 text-rose-300 text-[11px]">
          [SIMULATION LOG] Emergency flatten triggered. Cancel-all requested. Local DuckDB audit recorded.
        </div>
      )}

      {/* Pre-trade checks table */}
      <Card
        title="RISK GATEWAY AUDIT LOG"
        subtitle="Recent pre-trade verification events"
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto select-none">
          <table className="w-full text-left font-mono terminal-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Check Type</th>
                <th>Threshold</th>
                <th>Observed</th>
                <th>Decision</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-[#101622] hover:bg-[#121926]">
                <td className="text-slate-500 text-[10px]">14:44:59.102</td>
                <td className="text-slate-300">Daily Loss Limit</td>
                <td className="text-slate-500">₹20,000.00</td>
                <td className="text-slate-300">₹8,200.00</td>
                <td><Badge variant="success" size="xs">PASSED</Badge></td>
                <td className="text-emerald-400 text-[10px]">Order Dispatched</td>
              </tr>
              <tr className="border-b border-[#101622] hover:bg-[#121926]">
                <td className="text-slate-500 text-[10px]">14:44:59.104</td>
                <td className="text-slate-300">Drawdown Limit</td>
                <td className="text-slate-500">10.0%</td>
                <td className="text-slate-300">3.4%</td>
                <td><Badge variant="success" size="xs">PASSED</Badge></td>
                <td className="text-emerald-400 text-[10px]">Order Dispatched</td>
              </tr>
              <tr className="border-b border-[#101622] hover:bg-[#121926]">
                <td className="text-slate-500 text-[10px]">14:44:59.105</td>
                <td className="text-slate-300">Position Cap</td>
                <td className="text-slate-500">150 max</td>
                <td className="text-slate-300">100 open</td>
                <td><Badge variant="success" size="xs">PASSED</Badge></td>
                <td className="text-emerald-400 text-[10px]">Order Dispatched</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
