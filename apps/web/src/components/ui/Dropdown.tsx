import { useEffect, useRef, useState, type ReactNode } from 'react';
import { cn } from '@/lib/cn';

export interface DropdownOption<T extends string> {
  value: T;
  label: ReactNode;
}

export function Select<T extends string>({
  value,
  options,
  onChange,
  placeholder = 'Select…',
  className,
}: {
  value: T | '';
  options: DropdownOption<T>[];
  onChange: (value: T) => void;
  placeholder?: ReactNode;
  className?: string;
}) {
  const current = options.find((o) => o.value === value);
  return (
    <Dropdown
      block
      value={value || undefined}
      options={options}
      onChange={onChange}
      trigger={
        <span className={cn('selectn flex items-center text-left', className)}>
          <span className={cn('min-w-0 flex-1 truncate', current ? '' : 'text-faint')}>
            {current ? current.label : placeholder}
          </span>
        </span>
      }
    />
  );
}

// Custom (non-native) dropdown matching the Steel theme.
export function Dropdown<T extends string>({
  value,
  options,
  onChange,
  trigger,
  align = 'left',
  width = 190,
  block = false,
}: {
  value?: T;
  options: DropdownOption<T>[];
  onChange: (value: T) => void;
  trigger: ReactNode;
  align?: 'left' | 'right';
  width?: number;
  block?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDown);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className={cn('relative', block && 'w-full')}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={cn('flex items-center', block && 'w-full')}
      >
        {trigger}
      </button>
      {open ? (
        <div
          role="listbox"
          style={block ? { left: 0, right: 0 } : { width, [align]: 0 }}
          className="absolute top-[calc(100%+4px)] z-50 max-h-72 overflow-auto rounded-[var(--radius)] border border-border2 bg-panel2 p-1 shadow-[var(--shadow)]"
        >
          {options.map((o) => (
            <button type="button"
              key={o.value}

              onClick={() => {
                onChange(o.value);
                setOpen(false);
              }}
              className={cn(
                'flex w-full items-center gap-2 rounded-[4px] px-2.5 py-1.5 text-left text-xs',
                o.value === value ? 'bg-accent-dim text-accent-ink' : 'text-muted hover:bg-elev hover:text-text',
              )}
            >
              {o.label}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
