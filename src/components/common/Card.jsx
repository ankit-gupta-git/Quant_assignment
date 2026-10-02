import React from 'react';

export default function Card({
  title,
  subtitle,
  headerAction,
  children,
  className = '',
  bodyClassName = 'p-2',
  noHeader = false,
  statusIndicator = null
}) {
  return (
    <div className={`bg-[#0c1017] border border-[#1a2231] flex flex-col ${className}`}>
      {!noHeader && (
        <div className="bg-[#090d14] px-2.5 py-1 border-b border-[#1a2231] flex items-center justify-between min-h-[26px]">
          <div className="flex items-center gap-1.5">
            {statusIndicator}
            <div className="flex items-baseline gap-2">
              <span className="text-[10px] font-mono font-bold tracking-wider text-slate-300 uppercase">
                {title}
              </span>
              {subtitle && (
                <span className="text-[9px] text-slate-500 font-mono tracking-tight hidden sm:inline">
                  [{subtitle}]
                </span>
              )}
            </div>
          </div>
          {headerAction && (
            <div className="flex items-center gap-1 text-[10px] font-mono">
              {headerAction}
            </div>
          )}
        </div>
      )}
      <div className={`flex-1 ${bodyClassName}`}>
        {children}
      </div>
    </div>
  );
}
