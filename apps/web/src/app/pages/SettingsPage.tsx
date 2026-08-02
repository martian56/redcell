import { useEffect, useState, type ReactNode } from 'react';
import {
  useProviderKeys,
  useProviders,
  useRemoveProviderKey,
  useSaveSettings,
  useSetProviderKey,
  useSettings,
} from '@/features/hooks';
import { Button, Spinner } from '@/components/ui/primitives';
import { Combobox } from '@/components/ui/Combobox';
import { Field, SelectTrigger, Segmented, TextInput, Toggle } from '@/components/ui/fields';
import { toast } from '@/components/ui/toast';
import { PageShell } from './PageShell';
import type { Settings } from '@redcell/api-client';

function Card({ title, desc, children }: { title: string; desc?: string; children: ReactNode }) {
  return (
    <section className="rounded-[var(--radius)] border border-border bg-panel">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-[13px] font-bold">{title}</h3>
        {desc ? <p className="mt-0.5 text-[11px] text-faint">{desc}</p> : null}
      </div>
      <div className="grid gap-4 p-4">{children}</div>
    </section>
  );
}

export function SettingsPage() {
  const { data: initial } = useSettings();
  const { data: providers } = useProviders();
  const { data: keys } = useProviderKeys();
  const setKey = useSetProviderKey();
  const removeKey = useRemoveProviderKey();
  const save = useSaveSettings();
  const [draft, setDraft] = useState<Settings | null>(null);
  const [keyInput, setKeyInput] = useState('');

  useEffect(() => {
    if (initial && !draft) setDraft(structuredClone(initial));
  }, [initial, draft]);

  if (!draft || !providers) {
    return (
      <PageShell title="Settings">
        <div className="grid h-40 place-items-center">
          <Spinner />
        </div>
      </PageShell>
    );
  }

  const provider = providers.find((p) => p.id === draft.llm.provider);
  const setLLM = (p: Partial<Settings['llm']>) =>
    setDraft((d) => (d ? { ...d, llm: { ...d.llm, ...p } } : d));
  const setExec = (p: Partial<Settings['execution']>) =>
    setDraft((d) => (d ? { ...d, execution: { ...d.execution, ...p } } : d));
  const setScope = (p: Partial<Settings['scope']>) =>
    setDraft((d) => (d ? { ...d, scope: { ...d.scope, ...p } } : d));
  const setReport = (p: Partial<Settings['report']>) =>
    setDraft((d) => (d ? { ...d, report: { ...d.report, ...p } } : d));

  const onLogo = (file: File | undefined) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => setReport({ logoDataUrl: String(reader.result) });
    reader.readAsDataURL(file);
  };

  const onSave = async () => {
    await save.mutateAsync(draft);
    toast('Settings saved', 'success');
  };

  // Fixed-endpoint providers need no base URL; only a custom OpenAI-compatible
  // endpoint or a local Ollama do.
  const showBase = draft.llm.provider === 'custom' || draft.llm.provider === 'ollama';

  const keyedIds = new Set((keys ?? []).filter((k) => k.hasKey).map((k) => k.providerId));
  const currentHasKey = provider ? keyedIds.has(provider.id) : false;
  const keyStatus = (id: string, needsKey: boolean) =>
    keyedIds.has(id) ? 'key set' : needsKey ? 'no key' : 'no key needed';

  const saveKey = async () => {
    if (!provider || !keyInput.trim()) return;
    await setKey.mutateAsync({
      providerId: provider.id,
      apiKey: keyInput.trim(),
      apiBase: draft.llm.apiBase || null,
    });
    setKeyInput('');
    toast(`Key saved for ${provider.label}`, 'success');
  };
  const clearKey = async () => {
    if (!provider) return;
    await removeKey.mutateAsync(provider.id);
    toast(`Key removed for ${provider.label}`, 'success');
  };

  return (
    <PageShell
      title="Settings"
      subtitle="AI provider, local execution image, and scope"
      actions={
        <Button variant="primary" disabled={save.isPending} onClick={onSave}>
          {save.isPending ? <Spinner /> : 'Save changes'}
        </Button>
      }
    >
      <div className="mx-auto grid max-w-[760px] gap-4 p-5">
        <Card title="AI provider" desc="Provider-agnostic. Any provider, a custom endpoint, or a local model.">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Provider">
              <Combobox
                block
                items={providers}
                current={provider}
                getKey={(p) => p.id}
                getLabel={(p) => p.label}
                getSublabel={(p) => keyStatus(p.id, p.needsKey)}
                placeholder="Search providers..."
                onSelect={(p) => {
                  setLLM({ provider: p.id, model: p.models[0] ?? '' });
                  setKeyInput('');
                }}
                trigger={<SelectTrigger>{provider?.label ?? draft.llm.provider}</SelectTrigger>}
              />
            </Field>
            <Field label="Model">
              {provider && provider.models.length > 0 ? (
                <Combobox
                  block
                  items={provider.models}
                  current={draft.llm.model}
                  getKey={(m) => m}
                  getLabel={(m) => m}
                  placeholder="Search models..."
                  onSelect={(m) => setLLM({ model: m })}
                  trigger={<SelectTrigger>{draft.llm.model || 'select model'}</SelectTrigger>}
                />
              ) : (
                <TextInput
                  value={draft.llm.model}
                  placeholder="model id"
                  onChange={(e) => setLLM({ model: e.target.value })}
                />
              )}
            </Field>
          </div>
          {provider?.needsKey ? (
            <Field
              label="API key"
              hint={
                currentHasKey
                  ? `A key is saved for ${provider.label}. Every ${provider.label} model is available across the app. Enter a new key to replace it.`
                  : `Add a key for ${provider.label} to use its models anywhere. Encrypted at rest, never exposed to the browser.`
              }
            >
              <div className="flex items-center gap-2">
                <TextInput
                  type="password"
                  value={keyInput}
                  placeholder={currentHasKey ? 'key set · enter to replace' : 'sk-...'}
                  onChange={(e) => setKeyInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && keyInput.trim()) void saveKey();
                  }}
                />
                <Button
                  variant="primary"
                  disabled={!keyInput.trim() || setKey.isPending}
                  onClick={saveKey}
                >
                  Save key
                </Button>
                {currentHasKey ? (
                  <Button variant="danger" disabled={removeKey.isPending} onClick={clearKey}>
                    Remove
                  </Button>
                ) : null}
              </div>
            </Field>
          ) : null}
          {showBase ? (
            <Field label="API base URL" hint="OpenAI-compatible endpoint (custom gateway or a local Ollama host).">
              <TextInput
                value={draft.llm.apiBase ?? ''}
                placeholder="https://..."
                onChange={(e) => setLLM({ apiBase: e.target.value })}
              />
            </Field>
          ) : null}
          <Field label="Reasoning effort">
            <Segmented
              value={draft.llm.reasoningEffort}
              options={[
                { value: 'low', label: 'Low' },
                { value: 'medium', label: 'Medium' },
                { value: 'high', label: 'High' },
                { value: 'xhigh', label: 'xHigh' },
              ]}
              onChange={(v) => setLLM({ reasoningEffort: v })}
            />
          </Field>
        </Card>

        <Card
          title="Local execution image"
          desc="Kali image for runs on this host. Remote runs use the server picked per session."
        >
          <Field label="Container image">
            <TextInput
              value={draft.execution.dockerImage}
              onChange={(e) => setExec({ dockerImage: e.target.value })}
            />
          </Field>
        </Card>

        <Card title="Scope and rate" desc="Deterministic guardrails enforced at the tool layer.">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted">Allow private / loopback targets</span>
            <Toggle
              checked={draft.scope.allowPrivateTargets}
              onChange={(v) => setScope({ allowPrivateTargets: v })}
            />
          </div>
          <Field label="Max requests per second">
            <TextInput
              type="number"
              value={String(draft.scope.requestsPerSecond)}
              onChange={(e) => setScope({ requestsPerSecond: Number(e.target.value) || 0 })}
              className="w-32"
            />
          </Field>
        </Card>

        <Card title="Report branding" desc="Cover page and headers of generated reports. Client name comes from the session.">
          <div className="grid grid-cols-2 gap-4">
            <Field label="Company / team name">
              <TextInput
                value={draft.report.companyName}
                placeholder="REDCELL"
                onChange={(e) => setReport({ companyName: e.target.value })}
              />
            </Field>
            <Field label="Classification">
              <TextInput
                value={draft.report.classification}
                placeholder="CONFIDENTIAL"
                onChange={(e) => setReport({ classification: e.target.value })}
              />
            </Field>
          </div>
          <Field label="Prepared by / contact" hint="Shown on the report cover.">
            <TextInput
              value={draft.report.contact ?? ''}
              placeholder="Security Team, security@company.com"
              onChange={(e) => setReport({ contact: e.target.value })}
            />
          </Field>
          <Field label="Logo" hint="PNG or JPG, shown on the cover page.">
            <div className="flex items-center gap-3">
              {draft.report.logoDataUrl ? (
                <img src={draft.report.logoDataUrl} alt="logo" className="h-10 rounded border border-border2 bg-white p-1" />
              ) : null}
              <input
                type="file"
                accept="image/png,image/jpeg"
                onChange={(e) => onLogo(e.target.files?.[0])}
                className="text-xs text-muted file:mr-2 file:rounded-[var(--radius)] file:border file:border-border2 file:bg-panel file:px-2.5 file:py-1 file:text-xs file:text-text hover:file:bg-elev"
              />
              {draft.report.logoDataUrl ? (
                <button onClick={() => setReport({ logoDataUrl: undefined })} className="text-[11px] text-faint hover:text-crit">
                  Remove
                </button>
              ) : null}
            </div>
          </Field>
        </Card>

      </div>
    </PageShell>
  );
}
