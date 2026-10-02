import React from 'react';
import Card from '../common/Card';
import StatusDot from '../common/StatusDot';
import { systemHealthData } from '../../data/systemHealthData';

export default function SystemHealth() {
  const h = systemHealthData;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'STREAMING':
      case 'CONNECTED':
      case 'HEALTHY':
      case 'RUNNING':
        return 'text-emerald-400';
      default:
        return 'text-amber-400';
    }
  };

  return (
    <Card
      title="SYSTEM HEALTH"
      subtitle="Runtime monitoring"
      headerAction={
        <div className="flex items-center gap-1 font-mono text-[9px] text-slate-400">
          <span>HEARTBEAT:</span>
          <span className="text-slate-200 tabular-nums">09:32:14</span>
        </div>
      }
    >
      <div className="font-mono text-[11px] space-y-1 select-none">
        <div className="space-y-0.5">
          {h.subsystems.map((sub, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between px-2 py-0.5 bg-[#090d14] border border-[#1a2231] text-[10px]"
            >
              <div className="flex items-center gap-1.5">
                <StatusDot status={sub.state} size="xs" />
                <span className="text-slate-300">{sub.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] text-slate-500 tabular-nums">{sub.latencyMs}ms</span>
                <span className={`font-semibold ${getStatusBadge(sub.status)}`}>
                  {sub.status === 'STREAMING' ? 'Streaming' : sub.status === 'RUNNING' ? 'Running' : 'Healthy'}
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Runtime specs footer */}
        <div className="pt-1 border-t border-[#141b28] flex justify-between text-[9px] text-slate-500">
          <span>RSS: {h.telemetry.processMemoryMb}MB</span>
          <span>COROUTINES: {h.telemetry.activeTasks}</span>
          <span className="text-emerald-400">DRIFT: 0ms</span>
        </div>
      </div>
    </Card>
  );
}
