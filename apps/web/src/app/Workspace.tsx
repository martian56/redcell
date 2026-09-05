import { useContext } from 'react';
import {
  Mosaic,
  MosaicContext,
  MosaicWindow,
  type MosaicBranch,
} from 'react-mosaic-component';
import { PANEL_LABELS, SWAPPABLE, useWorkspace, usedPanels, type PanelId, type TileId } from '@/store/workspace';
import { Dropdown } from '@/components/ui/Dropdown';
import { Icon } from '@/components/ui/Icon';
import { Empty } from '@/components/ui/primitives';
import { useIsMobile } from '@/lib/useIsMobile';
import { PanelView } from './panels/PanelView';
import { MobileWorkspace } from './MobileWorkspace';

function TileToolbar({ tileId, path }: { tileId: TileId; path: MosaicBranch[] }) {
  const { mosaicActions } = useContext(MosaicContext);
  const tiles = useWorkspace((s) => s.tiles);
  const setActive = useWorkspace((s) => s.setActive);
  const closeTab = useWorkspace((s) => s.closeTab);
  const addTab = useWorkspace((s) => s.addTab);
  const tile = tiles[tileId];
  if (!tile) return <div className="tiletb" />;

  const addable = SWAPPABLE.filter((id) => !usedPanels(tiles).has(id));
  const closeTile = () => mosaicActions.remove(path);

  return (
    <div className="tiletb">
      <div className="ptabs">
        {tile.panels.map((p) => (
          <span key={p} className={`ptab${p === tile.active ? ' on' : ''}`}>
            <button type="button"

              className="ptab-label"
              onMouseDown={(e) => e.stopPropagation()}
              onClick={() => setActive(tileId, p)}
            >
              {PANEL_LABELS[p]}
            </button>
            <button type="button"

              className="tabx"
              aria-label={`Close ${PANEL_LABELS[p]}`}
              onMouseDown={(e) => e.stopPropagation()}
              onClick={(e) => {
                e.stopPropagation();
                if (tile.panels.length > 1) closeTab(tileId, p);
                else closeTile();
              }}
            >
              <Icon name="close" size={11} />
            </button>
          </span>
        ))}
      </div>
      <div className="tiletb-ctl" onMouseDown={(e) => e.stopPropagation()}>
        {addable.length > 0 && (
          <Dropdown
            align="right"
            width={190}
            options={addable.map((id) => ({ value: id, label: `Add ${PANEL_LABELS[id]}` }))}
            onChange={(v) => addTab(tileId, v as PanelId)}
            trigger={
              <span className="tiletb-btn" title="Add a tab to this panel">
                <Icon name="plus" size={13} />
              </span>
            }
          />
        )}
        <button type="button" className="tiletb-btn" title="Close panel" onClick={closeTile}>
          <Icon name="close" size={13} />
        </button>
      </div>
    </div>
  );
}

export function Workspace() {
  const isMobile = useIsMobile();
  const layout = useWorkspace((s) => s.layout);
  const tiles = useWorkspace((s) => s.tiles);
  const setLayout = useWorkspace((s) => s.setLayout);

  if (isMobile) return <MobileWorkspace />;

  return (
    <div className="relative h-full">
      {layout ? (
        <Mosaic<TileId>
          className="mosaic-steel"
          value={layout}
          onChange={(n) => setLayout(n)}
          renderTile={(tileId, path) => {
            const tile = tiles[tileId];
            const active = tile?.active ?? 'agents';
            return (
              <MosaicWindow<TileId>
                path={path}
                title={PANEL_LABELS[active]}
                renderToolbar={() => (
                  <div style={{ display: 'flex', width: '100%', height: '100%' }}>
                    <TileToolbar tileId={tileId} path={path} />
                  </div>
                )}
              >
                <PanelView id={active} />
              </MosaicWindow>
            );
          }}
        />
      ) : (
        <Empty>All panels closed. Use "Add panel" in the header.</Empty>
      )}
    </div>
  );
}
