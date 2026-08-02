// Red pulsing "thinking" indicator shown while the assistant is working.
export function Thinking({ label = 'Thinking', className = '' }: { label?: string; className?: string }) {
  return (
    <div
      className={
        'thinking-bubble self-start flex items-center gap-2.5 rounded-[var(--radius)] border border-border bg-panel2 px-3 py-2 ' +
        className
      }
    >
      <span className="thinking" aria-hidden>
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </span>
      <span className="font-mono text-[9px] font-bold uppercase tracking-wider text-accent">{label}</span>
    </div>
  );
}
