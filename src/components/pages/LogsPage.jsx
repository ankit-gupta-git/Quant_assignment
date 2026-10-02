import React, { useState } from 'react';
import { terminalLogs } from '../../data/logsData';
import { Filter, Search, Copy, Check, Pause, Play } from 'lucide-react';

export default function LogsPage() {
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [showJson, setShowJson] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [copied, setCopied] = useState(false);

  const filteredLogs = terminalLogs.filter((log) => {
    const matchesLevel = levelFilter === 'ALL' || log.level === levelFilter;
    const matchesSearch =
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.event.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.module.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  const handleCopyLogs = () => {
    const text = filteredLogs
      .map((l) => (showJson ? l.rawJson : `${l.timestamp.split('.')[0]} ${l.level.padEnd(5)} ${l.message}`))
      .join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'INFO':
        return 'text-sky-400';
      case 'WARN':
        return 'text-amber-400 font-semibold';
      case 'ERROR':
        return 'text-rose-400 font-semibold';
      case 'DEBUG':
        return 'text-slate-500';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Banner */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">SYSTEM LOGS</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">Engine runtime stream (app/core/logger.py)</span>
        </div>
        <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
          <span className="w-1.5 h-1.5 bg-emerald-500 inline-block"></span>
          <span>STREAM ACTIVE</span>
        </div>
      </div>

      {/* Terminal Container */}
      <div className="bg-[#05070b] border border-[#1a2231] flex flex-col h-[calc(100vh-170px)] min-h-[460px]">
        {/* Terminal Header & Controls */}
        <div className="bg-[#080c13] px-2 py-1 border-b border-[#1a2231] flex flex-wrap items-center justify-between gap-1 text-[10px]">
          {/* Level Filter Buttons */}
          <div className="flex items-center gap-1">
            <span className="text-slate-500 mr-1 flex items-center gap-0.5">
              <Filter className="w-2.5 h-2.5" /> LEVEL:
            </span>
            {['ALL', 'INFO', 'WARN', 'DEBUG'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setLevelFilter(lvl)}
                className={`px-1.5 py-0.2 border transition-none ${
                  levelFilter === lvl
                    ? 'bg-[#152030] border-slate-600 text-sky-300 font-semibold'
                    : 'bg-transparent border-[#1a2231] text-slate-400 hover:text-slate-200'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>

          {/* Action Toggles: JSON view, Pause, Copy, Search */}
          <div className="flex items-center gap-1.5">
            <div className="relative">
              <Search className="w-2.5 h-2.5 absolute left-1.5 top-1.5 text-slate-500" />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search..."
                className="bg-[#06080e] border border-[#1a2231] text-slate-200 placeholder-slate-600 text-[10px] pl-5 pr-1.5 py-0.5 rounded-none focus:outline-none focus:border-sky-500 w-32 sm:w-44"
              />
            </div>

            <button
              onClick={() => setShowJson(!showJson)}
              className={`px-1.5 py-0.5 text-[9px] border transition-none ${
                showJson
                  ? 'bg-sky-950 text-sky-300 border-sky-800'
                  : 'bg-[#090d14] text-slate-400 border-[#1a2231] hover:text-slate-200'
              }`}
            >
              {showJson ? 'JSON' : 'TEXT'}
            </button>

            <button
              onClick={() => setIsPaused(!isPaused)}
              className="p-1 bg-[#090d14] hover:bg-[#121926] text-slate-300 border border-[#1a2231]"
              title={isPaused ? 'Resume' : 'Pause'}
            >
              {isPaused ? <Play className="w-2.5 h-2.5 text-emerald-400" /> : <Pause className="w-2.5 h-2.5 text-amber-400" />}
            </button>

            <button
              onClick={handleCopyLogs}
              className="flex items-center gap-1 px-1.5 py-0.5 bg-[#090d14] hover:bg-[#121926] text-slate-300 border border-[#1a2231] text-[9px]"
            >
              {copied ? <Check className="w-2.5 h-2.5 text-emerald-400" /> : <Copy className="w-2.5 h-2.5" />}
              <span>{copied ? 'COPIED' : 'COPY'}</span>
            </button>
          </div>
        </div>

        {/* Log Lines Canvas */}
        <div className="flex-1 p-2 overflow-y-auto space-y-0.5 font-mono text-[11px] leading-tight select-text">
          {filteredLogs.map((l) => (
            <div
              key={l.id}
              className="flex items-start gap-2 hover:bg-[#0c1018] px-1 py-0.5 group"
            >
              <span className="text-slate-500 text-[10px] tabular-nums shrink-0 select-none">
                {l.timestamp.split('.')[0]}
              </span>
              <span className={`text-[10px] uppercase font-bold shrink-0 ${getLevelColor(l.level)}`}>
                {l.level.padEnd(5)}
              </span>

              {showJson ? (
                <span className="text-emerald-400 text-[10px] break-all">
                  {l.rawJson}
                </span>
              ) : (
                <span className="text-slate-300 break-words flex-1">
                  {l.message}
                </span>
              )}
            </div>
          ))}

          {/* Terminal Prompt Indicator */}
          <div className="flex items-center gap-1 pt-1 text-slate-500 text-[10px]">
            <span className="text-emerald-500 font-bold">quant-engine:~$</span>
            <span className="w-1.5 h-3 bg-emerald-500 term-cursor inline-block"></span>
          </div>
        </div>

        {/* Terminal Footer */}
        <div className="bg-[#080c13] px-2 py-0.5 border-t border-[#1a2231] flex items-center justify-between text-[9px] text-slate-500">
          <span>{filteredLogs.length} events buffered</span>
          <span>Output format: structlog console / JSON</span>
        </div>
      </div>
    </div>
  );
}
