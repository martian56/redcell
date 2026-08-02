import { useNavigate } from 'react-router-dom';
import { useSessions } from '@/features/hooks';
import { Button } from '@/components/ui/primitives';
import { Icon } from '@/components/ui/Icon';
import { PageShell } from './PageShell';
import { SessionCard } from './parts';

export function SessionsPage() {
  const nav = useNavigate();
  const { data: sessions } = useSessions();

  return (
    <PageShell
      title="Sessions"
      subtitle="All red-team operations"
      actions={
        <Button variant="primary" onClick={() => nav('/sessions/new')}>
          <Icon name="plus" size={14} />
          New session
        </Button>
      }
    >
      <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4 p-5">
        {(sessions ?? []).map((s) => (
          <SessionCard key={s.id} s={s} onClick={() => nav(`/sessions/${s.id}`)} />
        ))}
      </div>
    </PageShell>
  );
}
