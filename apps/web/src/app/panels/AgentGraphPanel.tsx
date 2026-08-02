import { useEffect, useMemo, useRef, useState, type PointerEvent as ReactPointerEvent } from 'react';
import { cn } from '@/lib/cn';
import { useUI } from '@/store/ui';
import { useGraph } from '@/store/graph';
import { useWorkspace } from '@/store/workspace';
import { useAgentGraph } from '@/features/hooks';
import { Empty, Spinner, StatusDot } from '@/components/ui/primitives';
import type { AgentEdge, AgentStatus, Agent } from '@redcell/api-client';

const TONE: Record<AgentStatus, string> = {
  running: 'var(--color-accent)',
  waiting: 'var(--color-med)',
  done: 'var(--color-live)',
  idle: 'var(--color-faint)',
  failed: 'var(--color-crit)',
};

const NW = 182;
const NH = 70;

type Pt = { x: number; y: number };

function defaultLayout(nodes: Agent[], edges: AgentEdge[]): Map<string, Pt> {
  const parent = new Map<string, string>();
  edges.forEach((e) => parent.set(e.to, e.from));
  const depthOf = (id: string): number => {
    let d = 0;
    let cur = id;
    const seen = new Set<string>();
    while (parent.has(cur) && !seen.has(cur)) {
      seen.add(cur);
      cur = parent.get(cur) as string;
      d += 1;
    }
    return d;
  };
  const columns = new Map<number, string[]>();
  nodes.forEach((n) => {
    const d = depthOf(n.id);
    const arr = columns.get(d) ?? [];
    arr.push(n.id);
    columns.set(d, arr);
  });
  const pos = new Map<string, Pt>();
  columns.forEach((ids, d) => ids.forEach((id, i) => pos.set(id, { x: 16 + d * 210, y: 14 + i * 96 })));
  return pos;
}

export function AgentGraphPanel() {
  const runId = useUI((s) => s.activeRunId);
  const selection = useUI((s) => s.selection);
  const select = useUI((s) => s.select);
  const stored = useGraph((s) => s.positions);
  const setPos = useGraph((s) => s.setPos);
  const showPanel = useWorkspace((s) => s.showPanel);
  const { data, isLoading } = useAgentGraph(runId);

  const defaults = useMemo(
    () => (data ? defaultLayout(data.nodes, data.edges) : new Map<string, Pt>()),
    [data],
  );

  const containerRef = useRef<HTMLDivElement>(null);
  const [live, setLive] = useState<Record<string, Pt>>({});
  const drag = useRef<{ id: string; offX: number; offY: number; x: number; y: number; moved: boolean } | null>(
    null,
  );

  const keyFor = (id: string) => `${runId}:${id}`;
  const posOf = (id: string): Pt => live[id] ?? stored[keyFor(id)] ?? defaults.get(id) ?? { x: 16, y: 16 };

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      const d = drag.current;
      const el = containerRef.current;
      if (!d || !el) return;
      const rect = el.getBoundingClientRect();
      const x = Math.max(0, e.clientX - rect.left - d.offX);
      const y = Math.max(0, e.clientY - rect.top - d.offY);
      d.x = x;
      d.y = y;
      d.moved = true;
      setLive((l) => ({ ...l, [d.id]: { x, y } }));
    };
    const onUp = () => {
      const d = drag.current;
      if (!d) return;
      if (d.moved) {
        setPos(keyFor(d.id), { x: d.x, y: d.y });
        setLive((l) => {
          const next = { ...l };
          delete next[d.id];
          return next;
        });
      } else {
        // A click (not a drag) selects the agent and opens the Context panel.
        select({ type: 'agent', id: d.id });
        showPanel('context');
      }
      drag.current = null;
    };
    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };
  }, [setPos, select, showPanel, runId]);

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;
  if (!data || data.nodes.length === 0) return <Empty>No active run.</Empty>;

  let maxX = 0;
  let maxY = 0;
  data.nodes.forEach((n) => {
    const p = posOf(n.id);
    maxX = Math.max(maxX, p.x + NW);
    maxY = Math.max(maxY, p.y + NH);
  });

  const startDrag = (e: ReactPointerEvent, id: string) => {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const p = posOf(id);
    drag.current = { id, offX: e.clientX - rect.left - p.x, offY: e.clientY - rect.top - p.y, x: p.x, y: p.y, moved: false };
  };

  return (
    <div className="h-full overflow-auto p-3">
      <div
        ref={containerRef}
        className="relative"
        style={{ width: maxX + 16, height: maxY + 16, minWidth: '100%', minHeight: '100%' }}
      >
        <svg className="absolute inset-0" width={maxX + 16} height={maxY + 16} style={{ overflow: 'visible' }}>
          {data.edges.map((e, i) => {
            const a = posOf(e.from);
            const b = posOf(e.to);
            const x1 = a.x + NW;
            const y1 = a.y + NH / 2;
            const x2 = b.x;
            const y2 = b.y + NH / 2;
            const mx = (x1 + x2) / 2;
            return (
              <path
                key={i}
                d={`M${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`}
                stroke="var(--color-border2)"
                fill="none"
                strokeWidth={1.5}
              />
            );
          })}
        </svg>
        {data.nodes.map((n) => {
          const p = posOf(n.id);
          const sel = selection?.type === 'agent' && selection.id === n.id;
          const dragging = !!live[n.id];
          return (
            <div
              key={n.id}
              onPointerDown={(e) => startDrag(e, n.id)}
              className={cn(
                'absolute cursor-grab touch-none select-none rounded-[var(--radius)] border bg-panel2 p-2.5 text-left active:cursor-grabbing',
                sel ? 'border-accent' : 'border-border2',
              )}
              style={{
                left: p.x,
                top: p.y,
                width: NW,
                zIndex: dragging ? 20 : 1,
                boxShadow: sel ? '0 0 0 1px var(--color-accent), 0 8px 24px rgba(255,51,68,0.22)' : undefined,
              }}
            >
              <div className="flex items-center gap-2">
                <StatusDot color={TONE[n.status]} glow={n.status === 'running'} />
                <span className="font-mono text-xs font-bold">{n.name}</span>
                <span className="ml-auto font-mono text-[9px] uppercase tracking-wider text-faint">
                  {n.role}
                </span>
              </div>
              <div className="mt-1.5 truncate text-[11px] text-muted">{n.action}</div>
              <div className="mt-1.5 flex gap-3 font-mono text-[10px] text-faint">
                <span>calls {n.calls}</span>
                <span style={{ color: TONE[n.status] }}>{n.status}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
