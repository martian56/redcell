import type { PanelId } from '@/store/workspace';
import { AgentGraphPanel } from './AgentGraphPanel';
import { LiveFeedPanel } from './LiveFeedPanel';
import { FindingsPanel } from './FindingsPanel';
import { ContextPanel } from './ContextPanel';
import { TerminalsPanel } from './TerminalsPanel';
import { ListenersPanel } from './ListenersPanel';
import { ProxyPanel } from './ProxyPanel';
import { ChatPanel } from './ChatPanel';
import { AttackSurfacePanel } from './AttackSurfacePanel';
import { LootPanel } from './LootPanel';
import { ReportsPanel } from './ReportsPanel';

export function PanelView({ id }: { id: PanelId }) {
  switch (id) {
    case 'agents':
      return <AgentGraphPanel />;
    case 'feed':
      return <LiveFeedPanel />;
    case 'findings':
      return <FindingsPanel />;
    case 'terminals':
      return <TerminalsPanel />;
    case 'context':
      return <ContextPanel />;
    case 'listeners':
      return <ListenersPanel />;
    case 'proxy':
      return <ProxyPanel />;
    case 'chat':
      return <ChatPanel />;
    case 'surface':
      return <AttackSurfacePanel />;
    case 'loot':
      return <LootPanel />;
    case 'reports':
      return <ReportsPanel />;
    default:
      return null;
  }
}
