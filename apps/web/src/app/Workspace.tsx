import { useContext } from 'react';
import {
  Mosaic,
  MosaicWindow,
  MosaicContext,
  MosaicWindowContext,
} from 'react-mosaic-component';
import { useWorkspace, PANEL_LABELS, SWAPPABLE, type PanelId } from '@/store/workspace';
import { Dropdown } from '@/components/ui/Dropdown';
import { Icon } from '@/components/ui/Icon';
import { Empty } from '@/components/ui/primitives';
import { PanelView } from './panels/PanelView';

function TileControls({ id }: { id: PanelId }) {
  const { mosaicActions } = useContext(MosaicContext);
  const { mosaicWindowActions } = useContext(MosaicWindowContext);
  const path = mosaicWindowActions.getPath();
  return (
    <div className="flex items-center gap-0.5 pr-1.5">
      <Dropdown
        align="right"
        width={170}
        value={id}
        options={SWAPPABLE.map((p) => ({ value: p, label: PANEL_LABELS[p] }))}
        onChange={(nid) => mosaicActions.replaceWith(path, nid)}
        trigger={
          <span className="grid h-6 w-6 place-items-center rounded-[4px] text-faint hover:bg-panel hover:text-text">
            <Icon name="chevronDown" size={13} />
          </span>
        }
      />
      <button
        title="Close panel"
        onClick={() => mosaicActions.remove(path)}
        className="grid h-6 w-6 place-items-center rounded-[4px] text-faint hover:bg-panel hover:text-text"
      >
        <Icon name="close" size={13} />
      </button>
    </div>
  );
}

export function Workspace() {
  const layout = useWorkspace((s) => s.layout);
  const setLayout = useWorkspace((s) => s.setLayout);

  return (
    <div className="relative h-full">
      {layout ? (
        <Mosaic<PanelId>
          className="mosaic-steel"
          value={layout}
          onChange={(n) => setLayout(n)}
          renderTile={(id, path) => (
            <MosaicWindow<PanelId>
              path={path}
              title={PANEL_LABELS[id]}
              toolbarControls={<TileControls id={id} />}
            >
              <PanelView id={id} />
            </MosaicWindow>
          )}
        />
      ) : (
        <Empty>All panels closed. Use "Add panel" in the header.</Empty>
      )}
    </div>
  );
}
