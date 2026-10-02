import React, { useState } from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import StatModule from '../common/StatModule';
import { tradesData } from '../../data/tradesData';
import { summaryMetrics } from '../../data/metricsData';
import { Filter, Search, Download } from 'lucide-react';

export default function TradesPage() {
  const [sideFilter, setSideFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const m = summaryMetrics;

  const filteredTrades = tradesData.filter((t) => {
    const matchesSide = sideFilter === 'ALL' || t.side === sideFilter;
    const matchesSearch =
      t.tradeId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.reason.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSide && matchesSearch;
  });

  const exportCsv = () => {
    const headers = [
      'timestamp',
      'trade_id',
      'symbol',
      'exchange',
      'side',
      'quantity',
      'entry_price',
      'exit_price',
      'gross_pnl',
      'charges',
      'net_pnl',
      'strategy_id',
      'reason',
      'running_pnl'
    ];
    const rows = tradesData.map((t) => [
      t.timestamp,
      t.tradeId,
      t.symbol,
      t.exchange,
      t.side,
      t.quantity,
      t.entryPrice,
      t.exitPrice,
      t.grossPnl,
      t.charges,
      t.netPnl,
      t.strategyId,
      t.reason,
      t.runningPnl
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'blotter_export.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Banner */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">TRADE BLOTTER & AUDIT LOG</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">data/blotter.csv audit trail</span>
        </div>
        <button
          onClick={exportCsv}
          className="flex items-center gap-1 px-2 py-0.5 bg-[#0e1624] hover:bg-[#152033] text-sky-300 border border-[#1a2231] text-[10px] transition-none"
        >
          <Download className="w-2.5 h-2.5" />
          <span>EXPORT CSV</span>
        </button>
      </div>

      {/* Summary Strip */}
      <div className="bg-[#090d14] border border-[#1a2231] grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 divide-x divide-y sm:divide-y-0 divide-[#1a2231]">
        <StatModule
          label="NET P&L"
          value={`+₹${m.netPnl.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          valueColor="text-emerald-400"
          subtext="Net of costs"
        />
        <StatModule
          label="GROSS P&L"
          value={`+₹${m.grossPnl.toFixed(2)}`}
          valueColor="text-slate-200"
          subtext="Raw alpha"
        />
        <StatModule
          label="TOTAL CHARGES"
          value={`₹${m.charges.toFixed(2)}`}
          valueColor="text-slate-200"
          subtext="NSE charges"
        />
        <StatModule
          label="ROUNDTRIPS"
          value={m.totalTrades}
          valueColor="text-slate-200"
          subtext="18 executed"
        />
        <StatModule
          label="WINS / LOSSES"
          value={`${m.winningTrades} / ${m.losingTrades}`}
          valueColor="text-emerald-400"
          subtext="38.9% Win Rate"
        />
        <StatModule
          label="PROFIT FACTOR"
          value={m.profitFactor.toFixed(2)}
          valueColor="text-emerald-400"
          subtext="Gross Win / Loss"
        />
      </div>

      {/* Full Blotter Table */}
      <Card
        title="ALL TRADE EXECUTIONS"
        subtitle="data/blotter.csv records"
        bodyClassName="p-0"
      >
        <div className="bg-[#090d14] px-2 py-1 border-b border-[#1a2231] flex flex-wrap items-center justify-between gap-1 text-[10px]">
          <div className="flex items-center gap-1">
            <span className="text-slate-500 mr-1 flex items-center gap-0.5">
              <Filter className="w-2.5 h-2.5" /> SIDE:
            </span>
            {['ALL', 'BUY', 'SELL'].map((side) => (
              <button
                key={side}
                onClick={() => setSideFilter(side)}
                className={`px-1.5 py-0.2 border transition-none ${
                  sideFilter === side
                    ? 'bg-[#152030] border-slate-600 text-sky-300 font-semibold'
                    : 'bg-transparent border-[#1a2231] text-slate-400 hover:text-slate-200'
                }`}
              >
                {side}
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
                <th>Execution Time</th>
                <th>Trade ID</th>
                <th>Symbol</th>
                <th>Side</th>
                <th>Type</th>
                <th className="text-right">Qty</th>
                <th className="text-right">Entry</th>
                <th className="text-right">Exit</th>
                <th className="text-right">Gross</th>
                <th className="text-right">Charges</th>
                <th className="text-right">Net P&L</th>
                <th className="text-right">Running Total</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.map((t) => {
                const isNetProfit = t.netPnl >= 0;
                const isRunningProfit = t.runningPnl >= 0;
                return (
                  <tr key={t.tradeId} className="border-b border-[#101622] hover:bg-[#121926]">
                    <td className="text-slate-500 text-[10px]">{t.timestamp}</td>
                    <td className="text-sky-300 font-medium text-[10px]">{t.tradeId}</td>
                    <td className="text-slate-200 font-semibold">{t.symbol}</td>
                    <td>
                      <Badge variant={t.side === 'BUY' ? 'buy' : 'sell'} size="xs">
                        {t.side}
                      </Badge>
                    </td>
                    <td className="text-slate-400 text-[10px]">{t.type}</td>
                    <td className="text-right text-slate-200">{t.quantity}</td>
                    <td className="text-right text-slate-300">₹{t.entryPrice.toFixed(2)}</td>
                    <td className="text-right text-slate-300">₹{t.exitPrice.toFixed(2)}</td>
                    <td className={`text-right text-[10px] ${t.grossPnl >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {t.grossPnl >= 0 ? '+' : ''}₹{t.grossPnl.toFixed(2)}
                    </td>
                    <td className="text-right text-slate-500 text-[10px]">₹{t.charges.toFixed(2)}</td>
                    <td className={`text-right font-semibold ${isNetProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {isNetProfit ? '+' : ''}₹{t.netPnl.toFixed(2)}
                    </td>
                    <td className={`text-right font-semibold ${isRunningProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {isRunningProfit ? '+' : ''}₹{t.runningPnl.toFixed(2)}
                    </td>
                    <td className="text-slate-400 text-[10px]">{t.reason}</td>
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
