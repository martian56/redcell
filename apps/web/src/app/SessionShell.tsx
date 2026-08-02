import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useUI } from '@/store/ui';
import { useSession } from '@/features/hooks';
import { Spinner } from '@/components/ui/primitives';
import { SessionTopbar } from './SessionTopbar';
import { Workspace } from './Workspace';

export function SessionShell() {
  const { id } = useParams();
  const setActiveSession = useUI((s) => s.setActiveSession);
  const setActiveRun = useUI((s) => s.setActiveRun);
  const { data: session, isLoading } = useSession(id ?? null);

  useEffect(() => {
    setActiveSession(id ?? null);
  }, [id, setActiveSession]);

  useEffect(() => {
    if (session) setActiveRun(session.activeRunId ?? null);
  }, [session, setActiveRun]);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden">
      <SessionTopbar session={session ?? null} />
      <div className="min-h-0 flex-1">
        {isLoading && !session ? (
          <div className="grid h-full place-items-center"><Spinner /></div>
        ) : (
          <Workspace />
        )}
      </div>
    </div>
  );
}
