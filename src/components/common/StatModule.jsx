import React from 'react';

export default function StatModule({
  label,
  value,
  subtext,
  valueColor = 'text-slate-100',
  isMonospace = true,
  trend = null,
  badge = null,
  className = ''
}) {
  return (
    <div className={`flex flex-col justify-center px-3 py-1.5 bg-[#090d14] border-r border-[#1a2231] last:border-r-0 ${className}`}>
      <div className="flex items-center justify-between gap-1 mb-0.5">
        <span className="text-[9px] uppercase font-mono font-medium text-slate-500 tracking-wider">
          {label}
        </span>
        {badge}
      </div>
      <div className="flex items-baseline gap-1">
        <span
          className={`text-sm font-semibold leading-none tabular-nums ${isMonospace ? 'font-mono' : ''} ${valueColor}`}
        >
          {value}
        </span>
        {trend && (
          <span className={`text-[9px] font-mono leading-none ${trend === 'up' ? 'text-emerald-400' : 'text-rose-400'}`}>
            {trend === 'up' ? '▲' : '▼'}
          </span>
        )}
      </div>
      {subtext && (
        <span className="text-[9px] text-slate-500 font-mono tracking-tight mt-0.5 truncate leading-tight">
          {subtext}
        </span>
      )}
    </div>
  );
}
