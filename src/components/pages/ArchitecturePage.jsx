import React, { useState } from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { architectureLayers } from '../../data/architectureData';
import { ArrowDown, Code } from 'lucide-react';

export default function ArchitecturePage() {
  const [selectedComponent, setSelectedComponent] = useState(architectureLayers[0].components[0]);

  return (
    <div className="space-y-2 pb-4 select-none font-mono">
      {/* Top Banner */}
      <div className="bg-[#090d14] border border-[#1a2231] px-2.5 py-1.5 flex items-center justify-between text-[11px]">
        <div className="flex items-center gap-2">
          <span className="font-bold text-slate-200">SYSTEM ARCHITECTURE SPECIFICATION</span>
          <span className="text-slate-500 hidden sm:inline">•</span>
          <span className="text-slate-400 hidden sm:inline">Clean Architecture pipeline with zero domain external dependencies</span>
        </div>
        <div className="text-[10px] text-slate-400">
          PYTHON 3.12 • EVENT-DRIVEN
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-2">
        {/* Left 2-cols: Engineering Architecture Diagram */}
        <div className="lg:col-span-2 space-y-1.5">
          {architectureLayers.map((layer, index) => (
            <div key={layer.id} className="space-y-1">
              {/* Layer Panel */}
              <div className="bg-[#0c1017] border border-[#1a2231] p-2">
                <div className="flex items-center justify-between pb-1 mb-1.5 border-b border-[#141b28]">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[9px] bg-[#141b28] text-sky-400 px-1 font-bold border border-[#1a2231]">
                      {layer.step}
                    </span>
                    <span className="text-[11px] font-bold text-slate-200">
                      {layer.name}
                    </span>
                  </div>
                  <span className="text-[9px] text-slate-500 hidden sm:inline">
                    [{layer.subtitle}]
                  </span>
                </div>

                {/* Subcomponents Chips Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-1">
                  {layer.components.map((comp) => {
                    const isSelected = selectedComponent?.name === comp.name;
                    return (
                      <button
                        key={comp.name}
                        onClick={() => setSelectedComponent(comp)}
                        className={`text-left p-1.5 border transition-none ${
                          isSelected
                            ? 'bg-[#152033] border-sky-500 text-sky-300'
                            : 'bg-[#080b11] border-[#1a2231] text-slate-300 hover:border-slate-600 hover:bg-[#0c1018]'
                        }`}
                      >
                        <div className="text-[11px] font-semibold text-slate-200 truncate flex items-center justify-between">
                          <span>{comp.name}</span>
                          {isSelected && <span className="text-[9px] text-sky-400 font-normal">●</span>}
                        </div>
                        <div className="text-[9px] text-slate-500 truncate mt-0.5">
                          {comp.module}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Data Flow Connector Arrow (unless last layer) */}
              {index < architectureLayers.length - 1 && (
                <div className="flex justify-center items-center py-0 text-slate-600">
                  <ArrowDown className="w-3 h-3" />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Right 1-col: Interactive Component Inspector */}
        <div className="lg:col-span-1">
          <div className="sticky top-10 space-y-2">
            <Card
              title="COMPONENT CONTRACT"
              subtitle="Module specification"
            >
              {selectedComponent ? (
                <div className="space-y-2 text-[11px]">
                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block">Component:</span>
                    <span className="text-xs font-semibold text-slate-100">{selectedComponent.name}</span>
                  </div>

                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block">Python Module:</span>
                    <span className="text-[10px] text-sky-400 font-semibold bg-[#07090e] p-1 border border-[#1a2231] block break-all">
                      {selectedComponent.module}
                    </span>
                  </div>

                  <div>
                    <span className="text-[9px] text-slate-500 uppercase block mb-0.5">Role & Contract:</span>
                    <p className="text-slate-300 text-[11px] leading-relaxed bg-[#07090e] p-2 border border-[#1a2231]">
                      {selectedComponent.role}
                    </p>
                  </div>

                  <div className="pt-1.5 border-t border-[#141b28] space-y-1 text-[10px]">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Anti-Lookahead:</span>
                      <span className="text-emerald-400 font-semibold">ENFORCED</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">DuckDB Persistence:</span>
                      <span className="text-emerald-400 font-semibold">SYNCHRONOUS ACID</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Automated Tests:</span>
                      <span className="text-slate-300">pytest unit suite</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-slate-500 text-xs">Select any component on the left to inspect its contract.</div>
              )}
            </Card>

            {/* Architecture Principles Reference */}
            <Card
              title="ENGINEERING RULES"
              subtitle="System guarantees"
            >
              <div className="space-y-1 text-[10px] text-slate-400">
                <div className="p-1 bg-[#07090e] border border-[#1a2231]">
                  1. Domain models (Candle, Tick, Signal) have ZERO external dependencies.
                </div>
                <div className="p-1 bg-[#07090e] border border-[#1a2231]">
                  2. Strategies run unchanged in Backtest, Walkforward, or Live Simulation.
                </div>
                <div className="p-1 bg-[#07090e] border border-[#1a2231]">
                  3. Broker decoupled via abstract BrokerBase interface.
                </div>
                <div className="p-1 bg-[#07090e] border border-[#1a2231]">
                  4. ACID order lifecycle persistence with DuckDB.
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
