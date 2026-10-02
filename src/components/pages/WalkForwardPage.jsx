import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import StatModule from '../common/StatModule';
import { walkForwardConfig, walkForwardWindows } from '../../data/walkForwardData';

export default function WalkForwardPage() {
  const cfg = walkForwardConfig;

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Strip */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">WALK-FORWARD CROSS-VALIDATION MATRIX</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">Rolling out-of-sample parameter stability</span>
        </div>
        <div className="text-[10px] text-slate-400">
          STABILITY: 87.5%
        </div>
      </div>

      {/* Configuration Summary Strip */}
      <div className="bg-[#090d14] border border-[#1a2231] grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-x divide-y sm:divide-y-0 divide-[#1a2231]">
        <StatModule
          label="TRAIN WINDOW"
          value="100 bars"
          valueColor="text-sky-300"
          subtext="In-Sample"
        />
        <StatModule
          label="OOS WINDOW"
          value="50 bars"
          valueColor="text-emerald-400"
          subtext="Out-of-Sample"
        />
        <StatModule
          label="STEP"
          value="50 bars"
          valueColor="text-slate-200"
          subtext="Window shift"
        />
        <StatModule
          label="TOTAL P&L"
          value={`+₹${cfg.totalNetPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          valueColor="text-emerald-400"
          subtext="Aggregate test returns"
        />
        <StatModule
          label="AVG WIN RATE"
          value={`${cfg.avgWinRatePct.toFixed(1)}%`}
          valueColor="text-emerald-400"
          subtext="On active slices"
        />
        <StatModule
          label="AVG MAX DD"
          value={`${cfg.avgMaxDrawdownPct.toFixed(2)}%`}
          valueColor="text-slate-200"
          subtext="Slice average"
        />
      </div>

      {/* Visual Window Partitioning Architecture */}
      <Card
        title="ROLLING WINDOW PARTITIONS"
        subtitle="Train (100b) vs OOS Test (50b)"
      >
        <div className="space-y-1 text-[10px]">
          <div className="space-y-1">
            {walkForwardWindows.map((w) => (
              <div key={w.window} className="flex items-center gap-2">
                <span className="w-16 text-slate-500 font-semibold">{w.windowId}:</span>
                <div className="flex-1 bg-[#05070b] border border-[#1a2231] h-4 flex items-center p-px relative">
                  <div
                    className="h-full bg-[#0d2238] border border-[#1a385c] flex items-center justify-center text-[8px] text-sky-300 font-medium"
                    style={{
                      marginLeft: `${(w.window * 6)}%`,
                      width: '32%'
                    }}
                  >
                    Train (100b)
                  </div>
                  <div
                    className="h-full bg-[#0c2e21] border border-[#144d37] flex items-center justify-center text-[8px] text-emerald-300 font-medium"
                    style={{ width: '16%' }}
                  >
                    OOS (50b)
                  </div>
                </div>
                <div className="w-20 text-right">
                  <span className={`tabular-nums ${w.pnl > 0 ? 'text-emerald-400 font-semibold' : 'text-slate-500'}`}>
                    {w.pnl > 0 ? `+₹${w.pnl.toFixed(0)}` : '₹0'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Per-Window Breakdown Table */}
      <Card
        title="ROLLING WINDOW RESULTS"
        subtitle="Out-of-sample evaluation"
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto select-none">
          <table className="w-full text-left font-mono terminal-table">
            <thead>
              <tr>
                <th>Window</th>
                <th>Train Period</th>
                <th>Test Period (OOS)</th>
                <th className="text-right">Trades</th>
                <th className="text-right">Sharpe</th>
                <th className="text-right">P&L</th>
                <th className="text-right">Drawdown</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {walkForwardWindows.map((w) => (
                <tr key={w.window} className="border-b border-[#101622] hover:bg-[#121926]">
                  <td className="text-sky-300 font-semibold">{w.windowId}</td>
                  <td className="text-slate-500 text-[10px]">{w.trainStart} → {w.trainEnd}</td>
                  <td className="text-slate-300 text-[10px]">{w.testStart} → {w.testEnd}</td>
                  <td className="text-right text-slate-300">{w.trades}</td>
                  <td className={`text-right ${w.sharpe < 0 ? 'text-amber-400' : 'text-slate-400'}`}>
                    {w.sharpe.toFixed(2)}
                  </td>
                  <td className={`text-right font-semibold ${w.pnl > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {w.pnl > 0 ? '+' : ''}₹{w.pnl.toFixed(2)}
                  </td>
                  <td className="text-right text-slate-400">
                    {w.drawdownPct.toFixed(2)}%
                  </td>
                  <td>
                    <Badge variant="success" size="xs">
                      COMPLETE
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
