import { useState } from 'react';
import { PANEL_LABELS, SWAPPABLE, type PanelId } from '@/store/workspace';
import { PanelView } from './panels/PanelView';

export function MobileWorkspace() {
  const [active, setActive] = useState<PanelId>('agents');
  return (
    <div className="mws">
      <div className="mws-tabs" role="tablist" aria-label="Panels">
        {SWAPPABLE.map((p) => (
          <button
            key={p}
            type="button"
            role="tab"
            aria-selected={p === active}
            className={`mws-tab${p === active ? ' on' : ''}`}
            onClick={() => setActive(p)}
          >
            {PANEL_LABELS[p]}
          </button>
        ))}
      </div>
      <div className="mws-body">
        <PanelView id={active} />
      </div>
    </div>
  );
}
