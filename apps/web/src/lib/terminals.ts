import { FitAddon } from '@xterm/addon-fit';
import { Terminal as XTerm } from '@xterm/xterm';
import { apiClient, apiMode } from '@/lib/api';

export type TerminalEntry = {
  el: HTMLDivElement;
  term: XTerm;
  fit: FitAddon;
};

type InternalEntry = TerminalEntry & { teardown: () => void };

const registry = new Map<string, InternalEntry>();

const THEME = {
  background: '#000000',
  foreground: '#c6cdd8',
  cursor: '#ff3344',
  cursorAccent: '#000000',
  selectionBackground: 'rgba(255,51,68,0.30)',
  black: '#0b0e13',
  red: '#ff4d5e',
  green: '#31d0c0',
  yellow: '#ffcf4a',
  blue: '#5ab0ff',
  magenta: '#ff7ad9',
  cyan: '#5ee0d0',
  white: '#eef3fa',
  brightBlack: '#5f7286',
  brightRed: '#ff6b7a',
  brightGreen: '#4de0d0',
  brightYellow: '#ffd76a',
  brightBlue: '#7ac0ff',
  brightMagenta: '#ff9ae0',
  brightCyan: '#7ef0e2',
  brightWhite: '#ffffff',
};

export function acquireTerminal(shellId: string, prompt: string): TerminalEntry {
  const existing = registry.get(shellId);
  if (existing) return existing;

  const el = document.createElement('div');
  el.className = 'h-full w-full';

  const term = new XTerm({
    convertEol: true,
    cursorBlink: true,
    fontFamily: 'ui-monospace, "JetBrains Mono", Menlo, Consolas, "Liberation Mono", monospace',
    fontSize: 12.5,
    lineHeight: 1.25,
    theme: THEME,
  });
  const fit = new FitAddon();
  term.loadAddon(fit);
  term.open(el);

  if (apiMode === 'mock') term.write(`\x1b[38;5;43m${prompt}\x1b[0m:~$ `);

  const unsub = apiClient.shellIO.subscribe(shellId, (chunk) => term.write(chunk));

  const onData = term.onData((data) => {
    void apiClient.shells.write(shellId, data);
    if (apiMode !== 'mock') return;
    if (data === '\r') term.write(`\r\n\x1b[38;5;43m${prompt}\x1b[0m:~$ `);
    else if (data === '\x7f') term.write('\b \b');
    else term.write(data);
  });

  const entry: InternalEntry = {
    el,
    term,
    fit,
    teardown: () => {
      onData.dispose();
      unsub();
      term.dispose();
      el.remove();
    },
  };
  registry.set(shellId, entry);
  return entry;
}

export function disposeTerminal(shellId: string): void {
  const entry = registry.get(shellId);
  if (!entry) return;
  entry.teardown();
  registry.delete(shellId);
}

export function reapTerminals(keep: Iterable<string>): void {
  const alive = new Set(keep);
  for (const id of [...registry.keys()]) {
    if (!alive.has(id)) disposeTerminal(id);
  }
}
