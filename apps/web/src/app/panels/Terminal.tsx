import { useEffect, useRef } from 'react';
import { Terminal as XTerm } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { apiClient, apiMode } from '@/lib/api';

// xterm.js terminal: streams output from shellIO, sends keystrokes to
// shells.write. Mock mode has no server echo, so echo locally.
export function Terminal({ shellId, prompt = 'operator@kali' }: { shellId: string; prompt?: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const host = ref.current;
    if (!host) return;

    const term = new XTerm({
      convertEol: true,
      cursorBlink: true,
      fontFamily: 'ui-monospace, "JetBrains Mono", Menlo, Consolas, "Liberation Mono", monospace',
      fontSize: 12.5,
      lineHeight: 1.25,
      theme: {
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
      },
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(host);
    try {
      fit.fit();
    } catch {
      /* container not sized yet */
    }

    // Server-driven shells send their own prompt; only the mock needs a local one.
    if (apiMode === 'mock') term.write(`\x1b[38;5;43m${prompt}\x1b[0m:~$ `);

    const ro = new ResizeObserver(() => {
      try {
        fit.fit();
      } catch {
        /* ignore */
      }
    });
    ro.observe(host);

    const unsub = apiClient.shellIO.subscribe(shellId, (chunk) => term.write(chunk));

    const onData = term.onData((data) => {
      void apiClient.shells.write(shellId, data);
      // The backend echoes keystrokes back, so a local echo would double them.
      // Only the mock needs one.
      if (apiMode !== 'mock') return;
      if (data === '\r') term.write(`\r\n\x1b[38;5;43m${prompt}\x1b[0m:~$ `);
      else if (data === '') term.write('\b \b');
      else term.write(data);
    });

    return () => {
      onData.dispose();
      unsub();
      ro.disconnect();
      term.dispose();
    };
  }, [shellId, prompt]);

  return <div ref={ref} className="h-full w-full bg-black p-1.5" />;
}
