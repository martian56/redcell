import type { InputHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/cn';
import { Icon } from './Icon';

export function SelectTrigger({ children }: { children: ReactNode }) {
  return (
    <span className="flex h-9 w-full items-center justify-between rounded-[var(--radius)] border border-border2 bg-black px-3 font-mono text-[13px] text-text hover:border-faint">
      <span className="truncate">{children}</span>
      <Icon name="chevronDown" size={13} className="text-faint" />
    </span>
  );
}

export function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-faint">{label}</span>
      {children}
      {hint ? <span className="text-[11px] text-faint">{hint}</span> : null}
    </label>
  );
}

export function TextInput({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'h-9 w-full rounded-[var(--radius)] border border-border2 bg-black px-3 font-mono text-[13px] text-text outline-none placeholder:text-faint focus:border-accent',
        className,
      )}
      {...props}
    />
  );
}

export function Toggle({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label?: string;
}) {
  return (
    <button type="button" onClick={() => onChange(!checked)} className="flex items-center gap-2.5">
      <span
        className={cn(
          'relative h-5 w-9 flex-none rounded-full border transition',
          checked ? 'border-accent bg-accent-dim' : 'border-border2 bg-panel2',
        )}
      >
        <span
          className={cn(
            'absolute top-0.5 h-3.5 w-3.5 rounded-full transition-all',
            checked ? 'left-[18px] bg-accent' : 'left-0.5 bg-faint',
          )}
        />
      </span>
      {label ? <span className="text-xs text-muted">{label}</span> : null}
    </button>
  );
}

export function Segmented<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex rounded-[var(--radius)] border border-border2 bg-panel2 p-1">
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          onClick={() => onChange(o.value)}
          className={cn(
            'rounded-[4px] px-3 py-1.5 text-xs font-semibold transition',
            o.value === value ? 'bg-accent text-white' : 'text-muted hover:text-text',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}
