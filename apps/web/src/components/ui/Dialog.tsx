import { useEffect, type ReactNode } from 'react';
import { Icon } from './Icon';

export function Dialog({
  open,
  onClose,
  title,
  children,
  footer,
  width = 460,
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
  width?: number;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="rc-modal fixed inset-0 z-[90] grid place-items-center bg-[var(--overlay)] p-4"
      onMouseDown={onClose}
    >
      <div
        className="rc-modal-panel w-full overflow-hidden rounded-[var(--radius)] border border-border2 bg-panel shadow-[var(--shadow)]"
        style={{ maxWidth: width }}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-border px-4 py-3">
          <h2 className="text-sm font-bold">{title}</h2>
          <button type="button" className="ml-auto text-faint hover:text-text" onClick={onClose} aria-label="Close">
            <Icon name="close" size={16} />
          </button>
        </div>
        <div className="p-4">{children}</div>
        {footer ? (
          <div className="flex justify-end gap-2 border-t border-border px-4 py-3">{footer}</div>
        ) : null}
      </div>
    </div>
  );
}
