import React, { useState } from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { ordersData, orderExecutionStats } from '../../data/ordersData';
import { Filter, Search } from 'lucide-react';

export default function OrdersPage() {
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredOrders = ordersData.filter((o) => {
    const matchesStatus = statusFilter === 'ALL' || o.status === statusFilter;
    const matchesSearch =
      o.orderId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.clientOrderId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.trigger.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Notice */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">ORDER MANAGEMENT SYSTEM (OMS)</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">Idempotent routing & broker ledger</span>
        </div>
        <div className="text-[10px] text-emerald-400">
          IDEMPOTENCY: ACTIVE
        </div>
      </div>

      {/* OMS Stats */}
      <div className="bg-[#090d14] border border-[#1a2231] grid grid-cols-2 sm:grid-cols-4 divide-x divide-y sm:divide-y-0 divide-[#1a2231]">
        <div className="p-2">
          <span className="text-[9px] text-slate-500 uppercase block">SUBMITTED</span>
          <span className="text-sm font-semibold text-slate-100 tabular-nums">{orderExecutionStats.submitted}</span>
        </div>
        <div className="p-2">
          <span className="text-[9px] text-slate-500 uppercase block">FILLED</span>
          <span className="text-sm font-semibold text-emerald-400 tabular-nums">{orderExecutionStats.filled}</span>
        </div>
        <div className="p-2">
          <span className="text-[9px] text-slate-500 uppercase block">AVG LATENCY</span>
          <span className="text-sm font-semibold text-sky-300 tabular-nums">{orderExecutionStats.avgFillLatencyMs} ms</span>
        </div>
        <div className="p-2">
          <span className="text-[9px] text-slate-500 uppercase block">DUCKDB SYNC</span>
          <span className="text-sm font-semibold text-emerald-400 tabular-nums">{orderExecutionStats.duckDbSyncRate}</span>
        </div>
      </div>

      {/* Main Order Table */}
      <Card
        title="ORDER BOOK"
        subtitle="Active & historical orders"
        bodyClassName="p-0"
      >
        <div className="bg-[#090d14] px-2 py-1 border-b border-[#1a2231] flex flex-wrap items-center justify-between gap-1 text-[10px]">
          <div className="flex items-center gap-1">
            <span className="text-slate-500 mr-1 flex items-center gap-0.5">
              <Filter className="w-2.5 h-2.5" /> STATUS:
            </span>
            {['ALL', 'FILLED', 'CANCELLED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-1.5 py-0.2 border transition-none ${
                  statusFilter === st
                    ? 'bg-[#152030] border-slate-600 text-sky-300 font-semibold'
                    : 'bg-transparent border-[#1a2231] text-slate-400 hover:text-slate-200'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          <div className="relative">
            <Search className="w-2.5 h-2.5 absolute left-1.5 top-1.5 text-slate-500" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search..."
              className="bg-[#06080e] border border-[#1a2231] text-slate-200 placeholder-slate-600 text-[10px] pl-5 pr-1.5 py-0.5 rounded-none focus:outline-none focus:border-sky-500 w-36 sm:w-48"
            />
          </div>
        </div>

        <div className="overflow-x-auto select-none">
          <table className="w-full text-left font-mono terminal-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Order ID</th>
                <th>Client Order ID</th>
                <th>Side</th>
                <th>Type</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Price</th>
                <th className="text-right">Filled</th>
                <th>Status</th>
                <th>Trigger</th>
                <th>Latency</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((o) => (
                <tr key={o.orderId} className="border-b border-[#101622] hover:bg-[#121926]">
                  <td className="text-slate-500 text-[10px]">{o.time.split(' ')[1]}</td>
                  <td className="text-sky-300 font-semibold text-[10px]">{o.orderId}</td>
                  <td className="text-slate-500 text-[9px] truncate max-w-[120px]" title={o.clientOrderId}>
                    {o.clientOrderId}
                  </td>
                  <td>
                    <Badge variant={o.side === 'BUY' ? 'buy' : 'sell'} size="xs">
                      {o.side}
                    </Badge>
                  </td>
                  <td className="text-slate-400 text-[10px]">{o.type}</td>
                  <td className="text-right text-slate-200">{o.qty}</td>
                  <td className="text-right text-slate-300">₹{o.price.toFixed(2)}</td>
                  <td className="text-right text-slate-300">
                    {o.filledPrice > 0 ? `₹${o.filledPrice.toFixed(2)}` : '—'}
                  </td>
                  <td>
                    <span className={`text-[9px] px-1 py-0.2 border ${
                      o.status === 'FILLED'
                        ? 'text-emerald-400 bg-emerald-950/80 border-emerald-800'
                        : 'text-amber-400 bg-amber-950/80 border-amber-800'
                    }`}>
                      {o.status}
                    </span>
                  </td>
                  <td className="text-slate-400 text-[10px]">{o.trigger}</td>
                  <td className="text-slate-500 text-[10px]">{o.latencyMs}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
