import { useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useUI } from '@/store/ui';
import { useSession } from '@/features/hooks';
import { Spinner } from '@/components/ui/primitives';
import { Workspace } from './Workspace';

export function ConsolePage() {
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

  if (isLoading && !session) {
    return (
      <div className="grid h-full place-items-center">
        <Spinner />
      </div>
    );
  }
  return <Workspace />;
}
