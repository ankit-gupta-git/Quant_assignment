import React from 'react';
import MetricStrip from '../dashboard/MetricStrip';
import EquityChart from '../dashboard/EquityChart';
import StrategyState from '../dashboard/StrategyState';
import RiskMonitor from '../dashboard/RiskMonitor';
import MacroRegime from '../dashboard/MacroRegime';
import OrderMonitor from '../dashboard/OrderMonitor';
import SystemHealth from '../dashboard/SystemHealth';
import TradeBlotter from '../dashboard/TradeBlotter';

export default function OverviewPage() {
  return (
    <div className="space-y-2 pb-4">
      {/* 1. Top Summary Strip */}
      <MetricStrip />

      {/* 2. Main Equity Chart */}
      <EquityChart />

      {/* 3. Secondary Data Area (Strategy State + Risk Monitor) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
        <StrategyState />
        <RiskMonitor />
      </div>

      {/* 4. Operational Monitoring Strip */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
        <MacroRegime />
        <OrderMonitor />
        <SystemHealth />
      </div>

      {/* 5. Trade Blotter Table */}
      <TradeBlotter limit={10} showAllControls={true} />
    </div>
  );
}
