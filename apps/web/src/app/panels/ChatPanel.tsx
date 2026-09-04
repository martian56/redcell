import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/cn';
import { useUI } from '@/store/ui';
import { useChat } from '@/features/hooks';
import { Button, Empty } from '@/components/ui/primitives';
import { Icon } from '@/components/ui/Icon';
import { Markdown } from '@/components/ui/Markdown';
import { Thinking } from '@/components/ui/Thinking';

export function ChatPanel() {
  const runId = useUI((s) => s.activeRunId);
  const { messages, send } = useChat(runId);
  const [text, setText] = useState('');
  const [pending, setPending] = useState(false);
  const scroller = useRef<HTMLDivElement>(null);

  // Autoscroll as messages appear.
  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages.length, pending]);

  // Clear the thinking indicator once the assistant replies.
  useEffect(() => {
    const last = messages[messages.length - 1];
    if (last && last.role === 'assistant') setPending(false);
  }, [messages]);
  useEffect(() => {
    if (!pending) return;
    const t = setTimeout(() => setPending(false), 120000);
    return () => clearTimeout(t);
  }, [pending]);

  if (!runId) return <Empty>No active run.</Empty>;

  const submit = (value?: string) => {
    const t = (value ?? text).trim();
    if (!t) return;
    if (value === undefined) setText('');
    setPending(true);
    void send(t);
  };

  // A question is "answered" once the operator has sent anything after it.
  const answeredBefore = (idx: number) => messages.slice(idx + 1).some((m) => m.role === 'operator');

  return (
    <div className="flex h-full flex-col">
      <div ref={scroller} className="flex min-h-0 flex-1 flex-col gap-2.5 overflow-auto p-3">
        {messages.length === 0 && !pending ? (
          <Empty>Steer the run. Tell the orchestrator to focus, exploit, escalate, or explain.</Empty>
        ) : (
          messages.map((m, i) => {
            const isQuestion = m.role === 'assistant' && !!m.options?.length;
            const answered = isQuestion && answeredBefore(i);
            return (
              <div
                key={m.id}
                className={cn(
                  'msg-in max-w-[85%] rounded-[var(--radius)] px-3 py-2 text-xs leading-relaxed',
                  m.role === 'operator'
                    ? 'self-end bg-accent-dim text-accent-ink'
                    : cn('self-start border bg-panel2 text-text', isQuestion ? 'border-accent' : 'border-border'),
                )}
              >
                {isQuestion ? (
                  <div className="mb-1 font-mono text-[9px] font-bold uppercase tracking-wider text-accent">
                    Agent asks
                  </div>
                ) : null}
                {m.role === 'operator' ? m.text : <Markdown>{m.text}</Markdown>}
                {m.options?.length ? (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.options.map((opt) => (
                      <button type="button"
                        key={opt}
                        disabled={answered}
                        onClick={() => submit(opt)}
                        className={cn(
                          'rounded-[var(--radius)] border px-2.5 py-1 text-[11px] font-semibold',
                          answered
                            ? 'cursor-default border-border bg-panel text-faint'
                            : 'border-border2 bg-panel text-muted hover:bg-elev hover:text-text',
                        )}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                ) : null}
              </div>
            );
          })
        )}
        {pending ? <Thinking /> : null}
      </div>
      <div className="flex flex-none items-center gap-2 border-t border-border bg-bg2 p-2">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') submit();
          }}
          placeholder="Tell the orchestrator what to do…"
          className="h-9 flex-1 rounded-[var(--radius)] border border-border2 bg-bg px-3 text-[13px] text-text outline-none transition-colors placeholder:text-faint focus:border-accent"
        />
        <Button variant="primary" onClick={() => submit()} disabled={!text.trim()}>
          <Icon name="steer" size={14} />
          Send
        </Button>
      </div>
    </div>
  );
}
