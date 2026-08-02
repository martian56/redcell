import type { ReactNode } from 'react';

export function PageShell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex h-[52px] flex-none items-center gap-3 border-b border-border bg-bg2 px-5">
        <div className="flex flex-col leading-tight">
          <span className="text-[13px] font-bold">{title}</span>
          {subtitle ? <span className="text-[11px] text-faint">{subtitle}</span> : null}
        </div>
        {actions ? <div className="ml-auto flex items-center gap-2">{actions}</div> : null}
      </div>
      <div className="min-h-0 flex-1 overflow-auto">{children}</div>
    </div>
  );
}
