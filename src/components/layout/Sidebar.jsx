import React from 'react';
import {
  LayoutDashboard,
  PlaySquare,
  GitBranch,
  Sliders,
  ShieldAlert,
  ListOrdered,
  ScrollText,
  Network,
  Terminal
} from 'lucide-react';
import StatusDot from '../common/StatusDot';

export default function Sidebar({ activeTab, setActiveTab }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard, key: '1' },
    { id: 'backtest', label: 'Backtest', icon: PlaySquare, key: '2' },
    { id: 'walkforward', label: 'Walk Forward', icon: GitBranch, key: '3' },
    { id: 'strategy', label: 'Strategy', icon: Sliders, key: '4' },
    { id: 'risk', label: 'Risk', icon: ShieldAlert, key: '5' },
    { id: 'orders', label: 'Orders', icon: ListOrdered, key: '6' },
    { id: 'trades', label: 'Trades', icon: ScrollText, key: '7' },
    { id: 'architecture', label: 'Architecture', icon: Network, key: '8' },
    { id: 'logs', label: 'System Logs', icon: Terminal, key: '9' },
  ];

  return (
    <aside className="w-40 bg-[#070a0f] border-r border-[#1a2231] flex flex-col justify-between select-none shrink-0 h-[calc(100vh-32px)] sticky top-8 font-mono text-[11px]">
      {/* Navigation list */}
      <div className="py-1">
        <div className="px-2 py-1 border-b border-[#141b28] mb-1">
          <span className="text-[9px] uppercase tracking-widest text-slate-500 font-bold">
            TERMINAL VIEWS
          </span>
        </div>
        <nav className="space-y-px">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-2 py-1.5 transition-none text-left ${
                  isActive
                    ? 'bg-[#121926] text-sky-400 font-semibold border-l-2 border-sky-400 pl-1.5'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-[#0c1017] border-l-2 border-transparent'
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <Icon className={`w-3 h-3 shrink-0 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                  <span className="truncate tracking-tight">{item.label}</span>
                </div>
                <span className={`text-[9px] ${isActive ? 'text-sky-400' : 'text-slate-600'}`}>
                  {item.key}
                </span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Docked System Strip */}
      <div className="p-2 border-t border-[#1a2231] bg-[#05070b] text-[9px] space-y-1 text-slate-400">
        <div className="flex items-center justify-between">
          <span className="text-slate-500">EVENT LOOP</span>
          <span className="text-emerald-400 font-medium flex items-center gap-1">
            <StatusDot status="healthy" size="xs" /> 240Hz
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">DUCKDB</span>
          <span className="text-slate-300">5.5 MB</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-slate-500">MEMORY</span>
          <span className="text-slate-300">142 MB</span>
        </div>
        <div className="pt-1 border-t border-[#141b28] text-slate-500 text-[8px] text-center tracking-wider">
          PYTHON 3.12 • BACKTEST
        </div>
      </div>
    </aside>
  );
}
