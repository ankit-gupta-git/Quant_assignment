import React, { useState } from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { tradesData } from '../../data/tradesData';
import { Filter, Search } from 'lucide-react';

export default function TradeBlotter({ limit = 10, showAllControls = true }) {
  const [filterSide, setFilterSide] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredTrades = tradesData.filter((t) => {
    const matchesSide = filterSide === 'ALL' || t.side === filterSide;
    const matchesSearch =
      t.tradeId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.reason.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSide && matchesSearch;
  });

  const displayedTrades = limit ? filteredTrades.slice(0, limit) : filteredTrades;

  return (
    <Card
      title="TRADE BLOTTER"
      subtitle="Execution ledger"
      headerAction={
        <div className="flex items-center gap-2">
          <Badge variant="neutral" size="xs">
            SIMULATION / BACKTEST DATA
          </Badge>
          <span className="text-[9px] text-slate-500">
            {displayedTrades.length} of {tradesData.length}
          </span>
        </div>
      }
      bodyClassName="p-0"
    >
      {/* Dense Controls Bar */}
      {showAllControls && (
        <div className="bg-[#090d14] px-2 py-1 border-b border-[#1a2231] flex flex-wrap items-center justify-between gap-1 text-[10px] font-mono">
          <div className="flex items-center gap-1">
            <span className="text-slate-500 mr-1 flex items-center gap-0.5">
              <Filter className="w-2.5 h-2.5" /> SIDE:
            </span>
            {['ALL', 'BUY', 'SELL'].map((side) => (
              <button
                key={side}
                onClick={() => setFilterSide(side)}
                className={`px-1.5 py-0.2 border transition-none ${
                  filterSide === side
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
              className="bg-[#06080e] border border-[#1a2231] text-slate-200 placeholder-slate-600 font-mono text-[10px] pl-5 pr-1.5 py-0.5 rounded-none focus:outline-none focus:border-sky-500 w-36 sm:w-48"
            />
          </div>
        </div>
      )}

      {/* Table Container */}
      <div className="overflow-x-auto select-none">
        <table className="w-full text-left font-mono terminal-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Order ID</th>
              <th>Symbol</th>
              <th>Side</th>
              <th>Type</th>
              <th className="text-right">Qty</th>
              <th className="text-right">Price</th>
              <th>Status</th>
              <th className="text-right">P&L</th>
            </tr>
          </thead>
          <tbody>
            {displayedTrades.map((trade) => {
              const isProfit = trade.netPnl >= 0;
              return (
                <tr key={trade.tradeId} className="border-b border-[#101622] hover:bg-[#121926]">
                  <td className="text-slate-400 text-[10px]">
                    {trade.timestamp.split(' ')[1] || trade.timestamp}
                  </td>
                  <td className="text-sky-300 font-medium text-[10px]">
                    {trade.tradeId.replace('TRD-', 'ORD-')}
                  </td>
                  <td className="text-slate-200 font-semibold">
                    {trade.symbol}
                  </td>
                  <td>
                    <Badge variant={trade.side === 'BUY' ? 'buy' : 'sell'} size="xs">
                      {trade.side}
                    </Badge>
                  </td>
                  <td className="text-slate-400 text-[10px]">
                    {trade.type}
                  </td>
                  <td className="text-right text-slate-200">
                    {trade.quantity}
                  </td>
                  <td className="text-right text-slate-300">
                    ₹{trade.entryPrice.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td>
                    <span className="text-[9px] text-emerald-400 font-semibold uppercase">
                      {trade.status}
                    </span>
                  </td>
                  <td className={`text-right font-semibold ${isProfit ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {isProfit ? '+' : ''}₹{trade.netPnl.toFixed(2)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Disclaimers & Blotter Footer */}
      <div className="bg-[#090d14] px-2 py-1 border-t border-[#1a2231] flex items-center justify-between text-[9px] font-mono text-slate-500">
        <span>SIMULATION / BACKTEST DATA • BROKER: ZERODHA MOCK BROKER</span>
        <span>NSE Statutory Costs & Anti-Lookahead Modeled</span>
      </div>
    </Card>
  );
}
