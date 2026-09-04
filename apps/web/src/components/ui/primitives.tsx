import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';
import { sevShort, sevVar } from '@/lib/format';
import type { Severity } from '@redcell/api-client';

type Variant = 'default' | 'primary' | 'ghost' | 'danger' | 'subtle';

const variants: Record<Variant, string> = {
  default: 'bg-panel border border-border2 text-text hover:bg-elev',
  primary: 'bg-accent text-white border border-transparent hover:brightness-110',
  ghost: 'bg-transparent border border-transparent text-muted hover:text-text hover:bg-panel',
  danger: 'bg-accent-dim text-white border border-transparent hover:brightness-110',
  subtle: 'bg-elev border border-transparent text-text hover:brightness-110',
};

export function Button({
  variant = 'default',
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button type="button"
      className={cn(
        'inline-flex select-none items-center gap-2 rounded-[var(--radius)] px-3 h-8 text-xs font-semibold transition disabled:opacity-50',
        variants[variant],
        className,
      )}
      {...props}
    />
  );
}

export function IconButton({
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button type="button"
      className={cn(
        'grid h-7 w-7 place-items-center rounded-[var(--radius)] text-faint transition hover:bg-panel hover:text-text',
        className,
      )}
      {...props}
    />
  );
}

export function Pill({
  children,
  tone = 'muted',
  className,
}: {
  children: ReactNode;
  tone?: 'muted' | 'accent' | 'live';
  className?: string;
}) {
  const tones = {
    muted: 'text-muted border-border2',
    accent: 'text-accent-ink border-transparent bg-accent-dim',
    live: 'text-live border-transparent',
  } as const;
  const style =
    tone === 'live' ? { backgroundColor: 'color-mix(in srgb, var(--color-live) 15%, transparent)' } : undefined;
  return (
    <span
      style={style}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[10.5px] font-bold',
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function StatusDot({ color, glow, className }: { color: string; glow?: boolean; className?: string }) {
  return (
    <span
      className={cn('inline-block h-2 w-2 rounded-full', className)}
      style={{ backgroundColor: color, boxShadow: glow ? `0 0 8px ${color}` : undefined }}
    />
  );
}

export function SeverityTag({ sev, cvss }: { sev: Severity; cvss?: number }) {
  const filled = sev === 'critical';
  const color = sevVar(sev);
  return (
    <span
      className="inline-flex items-center rounded-[4px] px-2 py-0.5 font-mono text-[10.5px] font-extrabold"
      style={
        filled
          ? { backgroundColor: color, color: '#fff' }
          : { color, backgroundColor: `color-mix(in srgb, ${color} 16%, transparent)` }
      }
    >
      {sevShort(sev)}
      {cvss !== undefined ? ` ${cvss.toFixed(1)}` : ''}
    </span>
  );
}

export function PanelHeader({
  title,
  right,
  className,
}: {
  title: ReactNode;
  right?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex h-9 flex-none items-center gap-2 border-b border-border bg-bg2 px-3',
        className,
      )}
    >
      <h3 className="font-mono text-[10.5px] font-bold uppercase tracking-[0.14em] text-muted">
        {title}
      </h3>
      {right ? <div className="ml-auto flex items-center gap-2">{right}</div> : null}
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'inline-block h-4 w-4 animate-spin rounded-full border-2 border-border2 border-t-accent',
        className,
      )}
    />
  );
}

export function Empty({ children, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className="grid h-full place-items-center p-6 text-center font-mono text-xs text-faint"
      {...props}
    >
      {children}
    </div>
  );
}
