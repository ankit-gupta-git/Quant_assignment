import React, { useState, useEffect } from 'react';
import { 
  Radio, 
  Terminal, 
  Github
} from 'lucide-react';
import StatusDot from '../common/StatusDot';

export default function TopBar() {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const istHours = (now.getUTCHours() + 5 + Math.floor((now.getUTCMinutes() + 30) / 60)) % 24;
      const istMinutes = (now.getUTCMinutes() + 30) % 60;
      const istSecs = now.getUTCSeconds();
      const pad = (n) => String(n).padStart(2, '0');
      setTimeStr(`${pad(istHours)}:${pad(istMinutes)}:${pad(istSecs)} IST`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-8 bg-[#070a0f] border-b border-[#1a2231] text-slate-300 flex items-center justify-between px-2 text-[11px] font-mono select-none sticky top-0 z-40">
      {/* Brand & Market Identity */}
      <div className="flex items-center h-full">
        {/* Terminal Identifier */}
        <div className="flex items-center gap-1.5 px-2 h-full border-r border-[#1a2231]">
          <span className="font-bold text-slate-100 tracking-wider">
            QUANT ENGINE
          </span>
          <span className="text-[9px] text-slate-500">
            [v2.4.0]
          </span>
        </div>

        {/* Status */}
        <div className="flex items-center gap-1.5 px-2 h-full border-r border-[#1a2231] text-sky-400">
          <StatusDot status="sim" size="xs" />
          <span className="text-[10px] font-semibold">SIMULATION</span>
        </div>

        {/* Market Instrument & Quote */}
        <div className="flex items-center gap-1.5 px-2 h-full border-r border-[#1a2231] text-slate-400">
          <span className="text-slate-500">MKT:</span>
          <span className="text-slate-200 font-semibold">NIFTY</span>
          <span className="text-[9px] text-slate-500">NSE</span>
          <span className="text-emerald-400 font-semibold tabular-nums pl-1">24,850.25</span>
          <span className="text-emerald-500 text-[10px] tabular-nums">+0.58%</span>
        </div>

        {/* Environment */}
        <div className="hidden md:flex items-center gap-1.5 px-2 h-full border-r border-[#1a2231] text-slate-400">
          <span className="text-slate-500">ENV:</span>
          <span className="text-amber-300 font-medium">BACKTEST</span>
        </div>

        {/* Broker Tag */}
        <div className="hidden lg:flex items-center gap-1.5 px-2 h-full border-r border-[#1a2231] text-slate-400">
          <span className="text-slate-500">BROKER:</span>
          <span className="text-slate-300">ZERODHA MOCK</span>
          <StatusDot status="healthy" size="xs" />
        </div>
      </div>

      {/* Right Strip: Disclaimers, Clock, GitHub */}
      <div className="flex items-center h-full">
        {/* Simulation Warning */}
        <div className="hidden xl:flex items-center px-2 h-full border-l border-[#1a2231] text-[9px] text-slate-400">
          SIMULATION ENVIRONMENT • NO LIVE ORDERS
        </div>

        {/* Time Stamp */}
        <div className="flex items-center gap-1.5 px-2 h-full border-l border-[#1a2231] text-slate-300">
          <span className="text-slate-500 text-[9px]">TIME:</span>
          <span className="tabular-nums font-semibold text-slate-200">{timeStr || '15:30:00 IST'}</span>
        </div>

        {/* GitHub Link */}
        <a
          href="https://github.com/ankit-gupta-git/Quant_assignment"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 px-2 h-full border-l border-[#1a2231] hover:bg-[#121926] text-slate-400 hover:text-slate-200 transition-colors"
          title="GitHub Repository: ankit-gupta-git/Quant_assignment"
        >
          <Github className="w-3 h-3" />
          <span className="hidden sm:inline text-[10px]">SRC</span>
        </a>
      </div>
    </header>
  );
}
