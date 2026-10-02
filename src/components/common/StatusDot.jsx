import React from 'react';

export default function StatusDot({ status = 'online', size = 'sm' }) {
  const colorMap = {
    online: 'bg-emerald-500',
    healthy: 'bg-emerald-500',
    sim: 'bg-sky-400',
    warning: 'bg-amber-400',
    danger: 'bg-rose-500',
    offline: 'bg-slate-600',
    standby: 'bg-slate-500'
  };

  const sizeMap = {
    xs: 'w-1.5 h-1.5',
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5'
  };

  return (
    <span className={`inline-block ${colorMap[status] || colorMap.online} ${sizeMap[size] || sizeMap.sm} shrink-0`} />
  );
}
