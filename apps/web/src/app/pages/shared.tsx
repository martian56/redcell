import { useEffect, useRef, useState, type KeyboardEvent } from 'react';
import type { Session, Severity } from '@redcell/api-client';
import { sevVar, timeAgo } from '@/lib/format';

export function onActivate(fn: () => void) {
  return (e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fn();
    }
  };
}

export function sevBar(counts: Record<Severity, number>) {
  const bars = (['critical', 'high', 'medium', 'low'] as Severity[])
    .filter((s) => counts[s] > 0)
    .map((s) => (
      <i key={s} style={{ width: `${Math.min(counts[s] * 6 + 2, 44)}px`, background: sevVar(s) }} />
    ));
  return bars.length ? bars : <span className="z">·</span>;
}

export function SessionRow({ s, onOpen }: { s: Session; onOpen: () => void }) {
  const dot = s.status === 'active' ? 'live' : 'done';
  return (
    <tr className="row" tabIndex={0} onClick={onOpen} onKeyDown={onActivate(onOpen)}>
      <td>
        <div className="name">
          <span className={`sd ${dot}`} />
          <span>
            <span className="nn">{s.name}</span> <span className="cl">/ {s.client}</span>
          </span>
        </div>
      </td>
      <td data-label="Type">
        <span className="kind" style={{ textTransform: 'capitalize' }}>
          {s.kind}
        </span>
      </td>
      <td data-label="Status">
        <span className={`status${s.status === 'active' ? ' live' : ''}`} style={{ textTransform: 'capitalize' }}>
          {s.status}
        </span>
      </td>
      <td data-label="Findings">
        <div className="sevbar">{sevBar(s.severityCounts)}</div>
      </td>
      <td className="meta mono" data-label="Targets">
        {s.targets.length || '—'}
      </td>
      <td data-label="Model">
        <span className="model">{s.model ?? '—'}</span>
      </td>
      <td className="tright meta" data-label="Last active">
        {timeAgo(s.createdAt)}
      </td>
    </tr>
  );
}

interface Opt {
  value: string;
  label: string;
}

export function FilterMenu({
  prefix,
  value,
  options,
  onChange,
  icon,
}: {
  prefix: string;
  value: string;
  options: Opt[];
  onChange: (v: string) => void;
  icon?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, []);
  const active = options.find((o) => o.value === value);
  return (
    <span className="menu-wrap" ref={ref}>
      <button type="button" className="chip" onClick={() => setOpen((v) => !v)}>
        {icon && (
          <svg viewBox="0 0 24 24">
            <path d="M4 6h16M7 12h10M10 18h4" />
          </svg>
        )}
        <span>
          {prefix}
          {active?.label ?? 'All'}
        </span>
        <svg className="caret" viewBox="0 0 24 24">
          <path d="M8 10l4 4 4-4" />
        </svg>
      </button>
      <div className="menu" style={{ display: open ? 'block' : 'none' }}>
        {options.map((o) => (
          <button type="button"
            key={o.value}
            className={`menu-item${o.value === value ? ' sel' : ''}`}
            onClick={() => {
              onChange(o.value);
              setOpen(false);
            }}
          >
            {o.label}
            <span className="ck">✓</span>
          </button>
        ))}
      </div>
    </span>
  );
}
