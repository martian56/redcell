import { useEffect, useRef, useState, type ComponentProps, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { getLeaves } from 'react-mosaic-component';
import { useUI } from '@/store/ui';
import { useWorkspace, PANEL_LABELS, SWAPPABLE } from '@/store/workspace';
import { Dropdown } from '@/components/ui/Dropdown';
import {
  useAvailableModels,
  useCreateRun,
  useRun,
  useRunControls,
  useSessions,
  useSettings,
} from '@/features/hooks';
import { fmtElapsed, fmtTokens } from '@/lib/format';
import { Button, StatusDot } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { Field, SelectTrigger, TextInput } from '@/components/ui/fields';
import { Combobox } from '@/components/ui/Combobox';
import { Icon } from '@/components/ui/Icon';
import { toast } from '@/components/ui/toast';
import { cn } from '@/lib/cn';
import type { AvailableModel, RunStatus, Session } from '@redcell/api-client';

const STATUS_TONE: Record<RunStatus, string> = {
  running: 'var(--color-live)',
  paused: 'var(--color-med)',
  queued: 'var(--color-faint)',
  completed: 'var(--color-live)',
  failed: 'var(--color-crit)',
  stopped: 'var(--color-crit)',
};

function useLiveSeconds(startISO?: string): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);
  if (!startISO) return 0;
  return Math.max(0, Math.floor((now - new Date(startISO).getTime()) / 1000));
}

function Chip({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex h-[27px] items-center gap-2 rounded-[var(--radius)] border border-border2 bg-panel px-2.5 font-mono text-xs text-muted">
      {children}
    </span>
  );
}

function Metric({ k, v, mono, clamp }: { k: string; v: string; mono?: boolean; clamp?: boolean }) {
  return (
    <div className={cn('flex min-w-0 flex-col leading-tight', clamp ? 'max-w-[130px]' : 'flex-none')}>
      <span className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">{k}</span>
      <span
        title={clamp ? v : undefined}
        className={cn(
          mono ? 'font-mono text-[13px] tabular-nums' : 'text-[13px] font-semibold',
          clamp && 'truncate',
        )}
      >
        {v}
      </span>
    </div>
  );
}

type IconName = ComponentProps<typeof Icon>['name'];

// Compact header action: icon button with a hover title.
function ActionIcon({
  icon,
  label,
  onClick,
  disabled,
  tone = 'default',
}: {
  icon: IconName;
  label: string;
  onClick?: () => void;
  disabled?: boolean;
  tone?: 'default' | 'danger';
}) {
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'grid h-8 w-8 flex-none place-items-center rounded-[var(--radius)] border transition disabled:opacity-40',
        tone === 'danger'
          ? 'border-transparent bg-accent-dim text-white hover:brightness-110'
          : 'border-border2 bg-panel text-muted hover:bg-elev hover:text-text',
      )}
    >
      <Icon name={icon} size={15} />
    </button>
  );
}

function List({ label, items, empty }: { label: string; items: string[]; empty: string }) {
  return (
    <div>
      <div className="mb-1 font-mono text-[10px] uppercase tracking-wider text-faint">{label}</div>
      {items.length ? (
        items.map((t) => (
          <div key={t} className="truncate font-mono text-xs text-text">
            {t}
          </div>
        ))
      ) : (
        <div className="text-[11px] text-faint">{empty}</div>
      )}
    </div>
  );
}

function ScopeChip({ session }: { session: Session | null }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [open]);

  const targets = session?.targets ?? [];
  const scope = session?.scope ?? [];
  const total = targets.length + scope.length;
  const primary = targets[0]?.replace(/^https?:\/\//, '') ?? scope[0];

  if (!primary) {
    return (
      <span className="inline-flex h-[27px] items-center gap-2 rounded-[var(--radius)] border border-dashed border-border2 px-2.5 font-mono text-xs text-faint">
        scope not set
      </span>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex h-[27px] items-center gap-2 rounded-[var(--radius)] border border-border2 bg-panel px-2.5 font-mono text-xs text-muted hover:bg-elev"
      >
        <Icon name="surface" size={13} className="text-faint" />
        <span className="max-w-[150px] truncate text-text">{primary}</span>
        {total > 1 ? (
          <span className="rounded-full bg-elev px-1.5 text-[10px] text-faint">+{total - 1}</span>
        ) : null}
        <Icon name="chevronDown" size={12} className="text-faint" />
      </button>
      {open ? (
        <div className="absolute left-0 top-[calc(100%+4px)] z-50 flex w-[300px] flex-col gap-3 rounded-[var(--radius)] border border-border2 bg-panel2 p-3 shadow-[0_16px_40px_rgba(0,0,0,0.55)]">
          <List label="Targets" items={targets} empty="none" />
          <List label="In scope" items={scope} empty="any (no scope set)" />
        </div>
      ) : null}
    </div>
  );
}

function NewRunDialog({
  open,
  onClose,
  sessionId,
}: {
  open: boolean;
  onClose: () => void;
  sessionId: string | null;
}) {
  const setActiveRun = useUI((s) => s.setActiveRun);
  const create = useCreateRun();
  const { data: settings } = useSettings();
  const { data: models } = useAvailableModels();

  const [name, setName] = useState('Full assessment');
  const [selected, setSelected] = useState<AvailableModel | null>(null);
  const [instruction, setInstruction] = useState('');

  // Default to the configured model when available.
  useEffect(() => {
    if (!open || !models || models.length === 0) return;
    const def =
      models.find((m) => m.model === settings?.llm.model && m.provider === settings?.llm.provider) ??
      models.find((m) => m.model === settings?.llm.model) ??
      models[0];
    setSelected(def ?? null);
  }, [open, models, settings]);

  const noModels = models && models.length === 0;

  const submit = async () => {
    if (!sessionId || !name.trim() || !selected) return;
    const run = await create.mutateAsync({
      sessionId,
      name: name.trim(),
      model: selected.model,
      provider: selected.provider,
      instruction,
    });
    setActiveRun(run.id);
    onClose();
    toast('Run started', 'success');
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="New run"
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            variant="primary"
            disabled={create.isPending || !name.trim() || !selected}
            onClick={submit}
          >
            Start run
          </Button>
        </>
      }
    >
      <div className="grid gap-3.5">
        <Field label="Name">
          <TextInput value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field
          label="Model"
          hint="Only models you have an API key for. Manage keys in Settings."
        >
          {noModels ? (
            <div
              className="rounded-[var(--radius)] border border-border2 bg-black px-3 py-2 text-[11px]"
              style={{ color: 'var(--color-med)' }}
            >
              No models available. Add an API key for a provider in Settings.
            </div>
          ) : (
            <Combobox
              block
              items={models ?? []}
              current={selected ?? undefined}
              getKey={(m) => `${m.provider}:${m.model}`}
              getLabel={(m) => m.model}
              getSublabel={(m) => m.providerLabel}
              placeholder="Search models..."
              onSelect={setSelected}
              trigger={<SelectTrigger>{selected ? selected.model : 'select model'}</SelectTrigger>}
            />
          )}
        </Field>
        <Field label="Instruction" hint="Optional. Scope focus, exclusions, objectives.">
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            rows={3}
            placeholder="Focus on auth and injection. No destructive tests."
            className="w-full rounded-[var(--radius)] border border-border2 bg-black px-3 py-2 text-[13px] text-text outline-none placeholder:text-faint focus:border-accent"
          />
        </Field>
      </div>
    </Dialog>
  );
}

export function SessionTopbar({ session }: { session: Session | null }) {
  const navigate = useNavigate();
  const runId = useUI((s) => s.activeRunId);
  const showPanel = useWorkspace((s) => s.showPanel);
  const reset = useWorkspace((s) => s.reset);
  const layout = useWorkspace((s) => s.layout);
  const addPanel = useWorkspace((s) => s.addPanel);
  const { data: run } = useRun(runId);

  const visible = new Set(layout ? getLeaves(layout) : []);
  const addable = SWAPPABLE.filter((id) => !visible.has(id));
  const { data: sessions } = useSessions();
  const controls = useRunControls();
  const elapsed = useLiveSeconds(run?.startedAt);
  const [newRun, setNewRun] = useState(false);

  const isRunning = run?.status === 'running';
  const canResume = !!run && ['paused', 'failed', 'stopped'].includes(run.status);
  const canStop = !!run && (run.status === 'running' || run.status === 'paused');
  const controlBusy =
    controls.pause.isPending || controls.resume.isPending || controls.stop.isPending;

  return (
    <header className="flex h-[52px] flex-none items-center gap-2 border-b border-border bg-bg2 px-3">
      <Button variant="ghost" className="flex-none" onClick={() => navigate('/sessions')}>
        <Icon name="chevronLeft" size={15} />
        Dashboard
      </Button>
      <div className="h-6 w-px flex-none bg-border" />

      {/* No overflow-hidden here so the session and scope dropdowns can open
          below the header without being clipped. */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <Combobox
          items={sessions ?? []}
          current={session ?? undefined}
          getKey={(s) => s.id}
          getLabel={(s) => s.name}
          getSublabel={(s) => s.client}
          onSelect={(s) => navigate(`/sessions/${s.id}`)}
          placeholder="Search sessions..."
          width={260}
          trigger={
            <div className="flex h-[27px] min-w-0 items-center gap-2 rounded-[var(--radius)] border border-border2 bg-panel px-2.5 hover:bg-elev">
              <StatusDot color="var(--color-live)" glow />
              <span className="max-w-[160px] truncate text-xs font-semibold text-text">
                {session?.name ?? 'Session'}
              </span>
              <Icon name="chevronDown" size={13} className="flex-none text-faint" />
            </div>
          }
        />

        <ScopeChip session={session} />

        {run ? (
          <span
            className="inline-flex h-[27px] flex-none items-center gap-2 rounded-[var(--radius)] px-2.5 font-mono text-[11px] font-bold uppercase tracking-[0.08em]"
            style={{
              color: STATUS_TONE[run.status],
              backgroundColor: `color-mix(in srgb, ${STATUS_TONE[run.status]} 12%, transparent)`,
            }}
          >
            <StatusDot color={STATUS_TONE[run.status]} glow={run.status === 'running'} />
            {run.status}
          </span>
        ) : null}

        {run ? (
          <div className="flex min-w-0 items-center gap-3 overflow-hidden">
            <Metric k="Phase" v={run.phase} />
            <Metric k="Elapsed" v={fmtElapsed(elapsed)} mono />
            <Metric k="Tokens" v={fmtTokens(run.tokens)} mono />
            <Metric k="Model" v={run.model} clamp />
          </div>
        ) : null}
      </div>

      {/* Actions: fixed width, always visible. */}
      <div className="flex flex-none items-center gap-1">
        <ActionIcon icon="steer" label="Steer" onClick={() => showPanel('chat')} />
        <ActionIcon
          icon={isRunning ? 'pause' : 'chevronRight'}
          label={isRunning ? 'Pause run' : 'Resume run'}
          disabled={isRunning ? controlBusy : !canResume || controlBusy}
          onClick={() => {
            if (!runId) return;
            if (isRunning) controls.pause.mutate(runId);
            else controls.resume.mutate(runId);
          }}
        />
        <ActionIcon
          icon="stop"
          label="Stop run"
          tone="danger"
          disabled={!canStop || controlBusy}
          onClick={() => runId && controls.stop.mutate(runId)}
        />
        <div className="mx-1 h-6 w-px bg-border" />
        <Button variant="primary" onClick={() => setNewRun(true)}>
          <Icon name="plus" size={14} />
          New run
        </Button>
        <Dropdown
          align="right"
          width={210}
          options={[
            ...addable.map((id) => ({ value: id, label: `Add ${PANEL_LABELS[id]}` })),
            { value: '__reset', label: 'Reset layout' },
          ]}
          onChange={(v) => {
            if (v === '__reset') reset();
            else addPanel(v);
          }}
          trigger={
            <span
              title="Layout & panels"
              className="grid h-8 w-8 place-items-center rounded-[var(--radius)] border border-border2 bg-panel text-muted transition hover:bg-elev hover:text-text"
            >
              <Icon name="sidebar" size={15} />
            </span>
          }
        />
      </div>

      <NewRunDialog open={newRun} onClose={() => setNewRun(false)} sessionId={session?.id ?? null} />
    </header>
  );
}
