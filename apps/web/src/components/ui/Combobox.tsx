import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { cn } from '@/lib/cn';
import { Icon } from './Icon';

// Searchable, paginated session picker.
export function Combobox<T>({
  items,
  current,
  getKey,
  getLabel,
  getSublabel,
  onSelect,
  trigger,
  placeholder = 'Search…',
  pageSize = 6,
  width = 280,
  block = false,
}: {
  items: T[];
  current?: T;
  getKey: (t: T) => string;
  getLabel: (t: T) => string;
  getSublabel?: (t: T) => string;
  onSelect: (t: T) => void;
  trigger: ReactNode;
  placeholder?: string;
  pageSize?: number;
  width?: number;
  block?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const [page, setPage] = useState(0);
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

  useEffect(() => {
    setPage(0);
  }, [q]);

  const filtered = useMemo(
    () =>
      items.filter((i) =>
        `${getLabel(i)} ${getSublabel?.(i) ?? ''}`.toLowerCase().includes(q.toLowerCase()),
      ),
    [items, q, getLabel, getSublabel],
  );
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const clampPage = Math.min(page, pages - 1);
  const pageItems = filtered.slice(clampPage * pageSize, clampPage * pageSize + pageSize);

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
          style={{ width: block ? '100%' : width }}
          className="absolute left-0 top-[calc(100%+4px)] z-50 rounded-[var(--radius)] border border-border2 bg-panel2 p-1.5 shadow-[0_16px_40px_rgba(0,0,0,0.55)]"
        >
          <div className="mb-1 flex items-center gap-2 rounded-[var(--radius)] border border-border2 bg-black px-2">
            <Icon name="search" size={13} className="text-faint" />
            <input
              autoFocus
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={placeholder}
              className="h-8 flex-1 bg-transparent text-[13px] text-text outline-none placeholder:text-faint"
            />
          </div>
          <div className="max-h-64 overflow-auto">
            {pageItems.length === 0 ? (
              <div className="px-2 py-3 text-center text-xs text-faint">No matches</div>
            ) : (
              pageItems.map((i) => {
                const active = current && getKey(current) === getKey(i);
                return (
                  <button
                    key={getKey(i)}
                    onClick={() => {
                      onSelect(i);
                      setOpen(false);
                    }}
                    className={cn(
                      'flex w-full flex-col rounded-[4px] px-2.5 py-1.5 text-left',
                      active ? 'bg-accent-dim' : 'hover:bg-elev',
                    )}
                  >
                    <span className={cn('text-xs', active ? 'text-accent-ink' : 'text-text')}>
                      {getLabel(i)}
                    </span>
                    {getSublabel ? <span className="text-[10px] text-faint">{getSublabel(i)}</span> : null}
                  </button>
                );
              })
            )}
          </div>
          {pages > 1 ? (
            <div className="mt-1 flex items-center justify-between border-t border-border px-1 pt-1.5">
              <button
                disabled={clampPage === 0}
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                className="grid h-6 w-6 place-items-center rounded text-faint hover:text-text disabled:opacity-40"
              >
                <Icon name="chevronLeft" size={14} />
              </button>
              <span className="font-mono text-[10px] text-faint">
                {clampPage + 1} / {pages}
              </span>
              <button
                disabled={clampPage >= pages - 1}
                onClick={() => setPage((p) => Math.min(pages - 1, p + 1))}
                className="grid h-6 w-6 place-items-center rounded text-faint hover:text-text disabled:opacity-40"
              >
                <Icon name="chevronRight" size={14} />
              </button>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
