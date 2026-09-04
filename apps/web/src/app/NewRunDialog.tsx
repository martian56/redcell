import { useEffect, useState } from 'react';
import type { AvailableModel } from '@redcell/api-client';
import { useUI } from '@/store/ui';
import { useAvailableModels, useCreateRun, useSettings } from '@/features/hooks';
import { Button } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { Field, SelectTrigger, TextInput } from '@/components/ui/fields';
import { Combobox } from '@/components/ui/Combobox';
import { toast } from '@/components/ui/toast';

export function NewRunDialog({
  open,
  onClose,
  sessionId,
}: {
  open: boolean;
  onClose: () => void;
  sessionId: string | null;
}) {
  const setActiveRun = useUI((s) => s.setActiveRun);
  const create = useCreateRun();
  const { data: settings } = useSettings();
  const { data: models } = useAvailableModels();

  const [name, setName] = useState('Full assessment');
  const [selected, setSelected] = useState<AvailableModel | null>(null);
  const [instruction, setInstruction] = useState('');

  useEffect(() => {
    if (!open || !models || models.length === 0) return;
    const def =
      models.find((m) => m.model === settings?.llm.model && m.provider === settings?.llm.provider) ??
      models.find((m) => m.model === settings?.llm.model) ??
      models[0];
    setSelected(def ?? null);
  }, [open, models, settings]);

  const noModels = models && models.length === 0;

  const submit = async () => {
    if (!sessionId || !name.trim() || !selected) return;
    try {
      const run = await create.mutateAsync({
        sessionId,
        name: name.trim(),
        model: selected.model,
        provider: selected.provider,
        instruction,
      });
      setActiveRun(run.id);
      onClose();
      toast('Run started', 'success');
    } catch {
      toast('Could not start the run', 'error');
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title="New run"
      footer={
        <>
          <Button onClick={onClose}>Cancel</Button>
          <Button variant="primary" disabled={create.isPending || !name.trim() || !selected} onClick={submit}>
            Start run
          </Button>
        </>
      }
    >
      <div className="grid gap-3.5">
        <Field label="Name">
          <TextInput value={name} onChange={(e) => setName(e.target.value)} />
        </Field>
        <Field label="Model" hint="Only models you have an API key for. Manage keys in Settings.">
          {noModels ? (
            <div className="rounded-[var(--radius)] border border-border2 bg-bg2 px-3 py-2 text-[11px]" style={{ color: 'var(--color-med)' }}>
              No models available. Add an API key for a provider in Settings.
            </div>
          ) : (
            <Combobox
              block
              items={models ?? []}
              current={selected ?? undefined}
              getKey={(m) => `${m.provider}:${m.model}`}
              getLabel={(m) => m.model}
              getSublabel={(m) => m.providerLabel}
              placeholder="Search models..."
              onSelect={setSelected}
              trigger={<SelectTrigger>{selected ? selected.model : 'select model'}</SelectTrigger>}
            />
          )}
        </Field>
        <Field label="Instruction" hint="Optional. Scope focus, exclusions, objectives.">
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            rows={3}
            placeholder="Focus on auth and injection. No destructive tests."
            className="textarea"
          />
        </Field>
      </div>
    </Dialog>
  );
}
