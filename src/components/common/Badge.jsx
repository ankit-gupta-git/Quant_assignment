import React from 'react';

export default function Badge({ children, variant = 'default', size = 'sm', className = '' }) {
  const variantStyles = {
    default: 'bg-[#101725] text-slate-300 border-slate-700/80',
    success: 'bg-[#081f18] text-emerald-400 border-emerald-800/80',
    danger: 'bg-[#220b0e] text-rose-400 border-rose-800/80',
    warning: 'bg-[#211606] text-amber-300 border-amber-800/80',
    info: 'bg-[#081829] text-sky-300 border-sky-800/80',
    neutral: 'bg-[#0c1017] text-slate-400 border-slate-800',
    buy: 'bg-[#081f18] text-emerald-300 border-emerald-700/80 font-semibold',
    sell: 'bg-[#220b0e] text-rose-300 border-rose-700/80 font-semibold',
  };

  const sizeStyles = {
    xs: 'text-[9px] px-1 py-0 leading-tight',
    sm: 'text-[10px] px-1.5 py-0.5 leading-tight',
    md: 'text-[11px] px-2 py-0.5 leading-normal'
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-mono uppercase tracking-wider border ${variantStyles[variant] || variantStyles.default} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </span>
  );
}
