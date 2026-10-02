import React from 'react';
import Card from '../common/Card';
import StatusDot from '../common/StatusDot';
import { orderExecutionStats } from '../../data/ordersData';

export default function OrderMonitor() {
  const stats = orderExecutionStats;

  return (
    <Card
      title="ORDER & EXECUTION"
      subtitle="OMS ledger"
      headerAction={
        <div className="flex items-center gap-1 font-mono text-[9px] text-emerald-400">
          <StatusDot status="healthy" size="xs" />
          <span>CONNECTED</span>
        </div>
      }
    >
      <div className="font-mono text-[11px] space-y-1 select-none">
        {/* Broker Meta Strip */}
        <div className="bg-[#090d14] p-1.5 border border-[#1a2231] space-y-0.5 text-[10px]">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Broker:</span>
            <span className="text-slate-200 font-semibold">ZERODHA MOCK BROKER</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Protocol:</span>
            <span className="text-slate-400">REST v3 + WebSocket</span>
          </div>
        </div>

        {/* Counts */}
        <div className="grid grid-cols-2 gap-1 pt-0.5">
          <div className="bg-[#090d14] px-2 py-1 border border-[#1a2231] flex items-center justify-between">
            <span className="text-[10px] text-slate-500">Submitted:</span>
            <span className="font-semibold text-slate-200 tabular-nums">{stats.submitted}</span>
          </div>
          <div className="bg-[#090d14] px-2 py-1 border border-[#1a2231] flex items-center justify-between">
            <span className="text-[10px] text-slate-500">Filled:</span>
            <span className="font-semibold text-emerald-400 tabular-nums">{stats.filled}</span>
          </div>
          <div className="bg-[#090d14] px-2 py-1 border border-[#1a2231] flex items-center justify-between">
            <span className="text-[10px] text-slate-500">Cancelled:</span>
            <span className="font-semibold text-slate-300 tabular-nums">{stats.cancelled}</span>
          </div>
          <div className="bg-[#090d14] px-2 py-1 border border-[#1a2231] flex items-center justify-between">
            <span className="text-[10px] text-slate-500">Rejected:</span>
            <span className="font-semibold text-slate-300 tabular-nums">{stats.rejected}</span>
          </div>
        </div>

        <div className="flex items-center justify-between px-2 py-1 bg-[#090d14] border border-[#1a2231]">
          <span className="text-[10px] text-slate-500">Open Orders:</span>
          <span className="font-semibold text-slate-200 tabular-nums">{stats.openOrders}</span>
        </div>

        {/* Micro latency specs */}
        <div className="pt-1 border-t border-[#141b28] flex justify-between text-[9px] text-slate-500">
          <span>FILL LATENCY: {stats.avgFillLatencyMs}ms</span>
          <span className="text-emerald-400">DUCKDB SYNC: 100%</span>
        </div>
      </div>
    </Card>
  );
}
