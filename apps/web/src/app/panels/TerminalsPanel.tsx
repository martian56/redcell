import { useEffect } from 'react';
import { cn } from '@/lib/cn';
import { useUI } from '@/store/ui';
import { useShellList, useOpenShell, useCloseShell } from '@/features/hooks';
import { useShells } from '@/store/shells';
import { disposeTerminal, reapTerminals } from '@/lib/terminals';
import { Terminal } from './Terminal';
import { Empty, Spinner, StatusDot } from '@/components/ui/primitives';
import { Icon } from '@/components/ui/Icon';
import type { ShellKind } from '@redcell/api-client';

const KIND_TONE: Record<ShellKind, string> = {
  reverse: 'var(--color-accent)',
  tool: 'var(--color-live)',
  interactive: 'var(--color-faint)',
};

export function TerminalsPanel() {
  const sid = useUI((s) => s.activeSessionId);
  const { data: shells, isLoading } = useShellList(sid);
  const active = useShells((s) => s.active);
  const setActive = useShells((s) => s.setActive);
  const openShell = useOpenShell(sid);
  const closeShell = useCloseShell(sid);

  useEffect(() => {
    if (!shells || shells.length === 0) return;
    const activeExists = active && shells.some((s) => s.id === active);
    if (!activeExists) {
      const first = shells.find((s) => s.status === 'running') ?? shells[0];
      if (first) setActive(first.id);
    }
  }, [shells, active, setActive]);

  useEffect(() => {
    if (!shells) return;
    reapTerminals(shells.map((s) => s.id));
  }, [shells]);

  const newTerminal = async () => {
    const shell = await openShell.mutateAsync(undefined);
    setActive(shell.id);
  };

  const closeTab = async (id: string) => {
    await closeShell.mutateAsync(id);
    disposeTerminal(id);
    if (active === id) setActive(null);
  };

  const tabBar = (
    <div className="flex flex-none items-center gap-1 overflow-x-auto border-b border-border bg-bg2 px-2 py-1.5">
      {(shells ?? []).map((s) => (
        <button
          key={s.id}
          onClick={() => setActive(s.id)}
          className={cn(
            'group flex flex-none items-center gap-2 rounded-[var(--radius)] border py-1.5 pl-3 pr-2 font-mono text-xs',
            s.id === active
              ? 'border-border2 bg-panel2 text-text'
              : 'border-transparent text-muted hover:bg-panel',
          )}
        >
          <StatusDot color={KIND_TONE[s.kind]} glow={s.status === 'running'} />
          {s.label}
          <span
            role="button"
            tabIndex={-1}
            title="Close terminal"
            onClick={(e) => {
              e.stopPropagation();
              void closeTab(s.id);
            }}
            className="rounded p-0.5 text-faint opacity-0 hover:text-accent hover:bg-panel group-hover:opacity-100"
          >
            <Icon name="close" size={12} />
          </span>
        </button>
      ))}
      <button
        onClick={() => void newTerminal()}
        disabled={!sid || openShell.isPending}
        title="New terminal"
        className="ml-1 flex flex-none items-center gap-1 rounded-[var(--radius)] border border-transparent px-2 py-1.5 font-mono text-xs text-muted hover:bg-panel hover:text-text disabled:opacity-40"
      >
        <Icon name="plus" size={13} />
        New
      </button>
    </div>
  );

  if (isLoading) return <div className="grid h-full place-items-center"><Spinner /></div>;

  const current = shells?.find((s) => s.id === active) ?? shells?.[0];

  return (
    <div className="flex h-full flex-col">
      {tabBar}
      <div className="min-h-0 flex-1">
        {current ? (
          <Terminal
            key={current.id}
            shellId={current.id}
            prompt={current.kind === 'reverse' ? 'root@target' : 'operator@kali'}
          />
        ) : (
          <Empty>No shells open. Start one with New, or the agent opens them during a run.</Empty>
        )}
      </div>
    </div>
  );
}
