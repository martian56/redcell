import { useRef } from 'react';
import { useUI } from '@/store/ui';
import { useApi } from '@/lib/api';
import { useDeleteFile, useFiles, useUploadFile } from '@/features/hooks';
import { timeAgo } from '@/lib/format';
import { Button, Empty, Spinner } from '@/components/ui/primitives';
import { toast } from '@/components/ui/toast';

function formatBytes(n: number): string {
  if (!n) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB'];
  const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
  return `${(n / 1024 ** i).toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

export function FilesPanel() {
  const sessionId = useUI((s) => s.activeSessionId);
  const api = useApi();
  const { data, isLoading } = useFiles(sessionId);
  const upload = useUploadFile(sessionId ?? '');
  const remove = useDeleteFile(sessionId ?? '');
  const fileRef = useRef<HTMLInputElement>(null);

  if (!sessionId) return <Empty>No active session.</Empty>;

  const onPick = async (files: FileList | null) => {
    if (!files?.length) return;
    for (const file of Array.from(files)) {
      try {
        await upload.mutateAsync({ file, kind: 'assessment' });
      } catch {
        toast(`Could not upload ${file.name}`, 'error');
      }
    }
    if (fileRef.current) fileRef.current.value = '';
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-none items-center gap-2 border-b border-border bg-bg2 px-3 py-2">
        <span className="font-mono text-[10px] uppercase tracking-wider text-faint">Files</span>
        <input
          ref={fileRef}
          type="file"
          multiple
          className="hidden"
          onChange={(e) => void onPick(e.target.files)}
        />
        <Button
          variant="subtle"
          className="ml-auto h-6 flex-none px-2 text-[11px]"
          disabled={upload.isPending}
          onClick={() => fileRef.current?.click()}
        >
          {upload.isPending ? 'Uploading…' : 'Upload'}
        </Button>
      </div>
      {isLoading ? (
        <div className="grid flex-1 place-items-center">
          <Spinner />
        </div>
      ) : !data || data.length === 0 ? (
        <Empty>No files staged. Upload the app binary, source, or evidence.</Empty>
      ) : (
        <div className="min-h-0 flex-1 overflow-auto">
          {data.map((f) => (
            <div key={f.id} className="flex items-center gap-2 border-b border-border px-3 py-2 hover:bg-panel2">
              <div className="min-w-0 flex-1">
                <a
                  href={api.files.downloadUrl(f.id)}
                  className="block truncate font-mono text-xs text-text hover:text-accent-ink"
                  title={f.filename}
                >
                  {f.filename}
                </a>
                <div className="mt-0.5 flex items-center gap-2 font-mono text-[10px] text-faint">
                  <span className="uppercase">{f.kind}</span>
                  <span>·</span>
                  <span>{formatBytes(f.size)}</span>
                  <span>·</span>
                  <span>{timeAgo(f.createdAt)}</span>
                </div>
              </div>
              <button
                type="button"
                className="tiletb-btn"
                title="Delete file"
                onClick={() => remove.mutate(f.id)}
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
