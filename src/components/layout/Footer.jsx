import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-[#05070b] border-t border-[#1a2231] text-slate-500 text-[10px] font-mono py-1 px-3 flex flex-col sm:flex-row items-center justify-between gap-1 select-none">
      <div className="flex items-center gap-2">
        <span className="font-semibold text-slate-400">
          QUANT ENGINE
        </span>
        <span className="text-slate-600">/</span>
        <span>Python 3.12 • Event-Driven Backtesting & Risk Engine</span>
        <span className="text-slate-600 hidden md:inline">/</span>
        <span className="text-slate-500 hidden md:inline">DuckDB ACID Persistence</span>
      </div>

      <div className="flex items-center gap-3 text-[9px]">
        <span className="text-amber-400">
          [SIMULATION ENVIRONMENT • NO LIVE ORDERS]
        </span>
        <span className="text-slate-500">
          Broker: Zerodha Mock Broker
        </span>
        <a
          href="https://github.com/ankit-gupta-git/Quant_assignment"
          target="_blank"
          rel="noopener noreferrer"
          className="text-slate-400 hover:text-slate-200 transition-colors"
        >
          GitHub Repository
        </a>
      </div>
    </footer>
  );
}
