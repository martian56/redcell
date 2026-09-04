import { useEffect, useState } from 'react';
import type { ProviderCatalogEntry, Settings } from '@redcell/api-client';
import {
  useProviderKeys,
  useProviders,
  useRemoveProviderKey,
  useSaveSettings,
  useSetProviderKey,
  useSettings,
} from '@/features/hooks';
import { Spinner } from '@/components/ui/primitives';
import { Dialog } from '@/components/ui/Dialog';
import { toast } from '@/components/ui/toast';

type Tab = 'providers' | 'execution' | 'scope' | 'branding';

const TABS: { id: Tab; label: string }[] = [
  { id: 'providers', label: 'Providers & keys' },
  { id: 'execution', label: 'Execution' },
  { id: 'scope', label: 'Scope guardrails' },
  { id: 'branding', label: 'Report branding' },
];

export function SettingsPage() {
  const { data: initial } = useSettings();
  const { data: providers } = useProviders();
  const { data: keys } = useProviderKeys();
  const setKey = useSetProviderKey();
  const removeKey = useRemoveProviderKey();
  const save = useSaveSettings();

  const [tab, setTab] = useState<Tab>('providers');
  const [draft, setDraft] = useState<Settings | null>(null);
  const [keyFor, setKeyFor] = useState<ProviderCatalogEntry | null>(null);
  const [keyInput, setKeyInput] = useState('');

  useEffect(() => {
    if (initial && !draft) setDraft(structuredClone(initial));
  }, [initial, draft]);

  if (!draft || !providers) {
    return (
      <div className="wrap">
        <div className="grid h-40 place-items-center">
          <Spinner />
        </div>
      </div>
    );
  }

  const setLLM = (p: Partial<Settings['llm']>) => setDraft((d) => (d ? { ...d, llm: { ...d.llm, ...p } } : d));
  const setExec = (p: Partial<Settings['execution']>) =>
    setDraft((d) => (d ? { ...d, execution: { ...d.execution, ...p } } : d));
  const setScope = (p: Partial<Settings['scope']>) => setDraft((d) => (d ? { ...d, scope: { ...d.scope, ...p } } : d));
  const setReport = (p: Partial<Settings['report']>) =>
    setDraft((d) => (d ? { ...d, report: { ...d.report, ...p } } : d));

  const onSave = async () => {
    try {
      await save.mutateAsync(draft);
      toast('Settings saved', 'success');
    } catch {
      toast('Could not save settings', 'error');
    }
  };

  const keyedIds = new Set((keys ?? []).filter((k) => k.hasKey).map((k) => k.providerId));
  const provider = providers.find((p) => p.id === draft.llm.provider);
  const models = provider?.models ?? [];

  const saveKey = async () => {
    if (!keyFor || !keyInput.trim()) return;
    const apiBase = (keys ?? []).find((k) => k.providerId === keyFor.id)?.apiBase ?? null;
    try {
      await setKey.mutateAsync({ providerId: keyFor.id, apiKey: keyInput.trim(), apiBase });
      setKeyFor(null);
      setKeyInput('');
      toast(`Key saved for ${keyFor.label}`, 'success');
    } catch {
      toast(`Could not save the key for ${keyFor.label}`, 'error');
    }
  };

  return (
    <div className="wrap">
      <div className="settings">
        <div className="subnav">
          {TABS.map((t) => (
            <button key={t.id} className={tab === t.id ? 'on' : ''} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </div>
        <div>
          {tab === 'providers' && (
            <>
              <div className="card">
                <div className="card-h">
                  <h3>Default model</h3>
                  <span className="cs">· used for new runs</span>
                </div>
                <div className="card-b">
                  <div className="grid2">
                    <div className="field">
                      <span className="label">Provider</span>
                      <select
                        className="selectn"
                        value={draft.llm.provider}
                        onChange={(e) => {
                          const p = providers.find((x) => x.id === e.target.value);
                          setLLM({ provider: e.target.value, model: p?.models[0] ?? draft.llm.model });
                        }}
                      >
                        {providers.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="field">
                      <span className="label">Model</span>
                      {models.length > 0 ? (
                        <select className="selectn" value={draft.llm.model} onChange={(e) => setLLM({ model: e.target.value })}>
                          {models.map((m) => (
                            <option key={m} value={m}>
                              {m}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input className="input mono" value={draft.llm.model} onChange={(e) => setLLM({ model: e.target.value })} />
                      )}
                    </div>
                  </div>
                  <div className="field" style={{ margin: 0 }}>
                    <span className="label">Reasoning effort</span>
                    <div className="seg" style={{ width: 'fit-content' }}>
                      {(['low', 'medium', 'high', 'xhigh'] as const).map((v) => (
                        <button key={v} className={draft.llm.reasoningEffort === v ? 'on' : ''} onClick={() => setLLM({ reasoningEffort: v })}>
                          {v === 'xhigh' ? 'xHigh' : v[0]!.toUpperCase() + v.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>
                  <button className="btn pri" style={{ marginTop: 14 }} disabled={save.isPending} onClick={onSave}>
                    Save
                  </button>
                </div>
              </div>
              <div className="card" style={{ marginTop: 16 }}>
                <div className="card-h">
                  <h3>Model providers</h3>
                  <span className="cs">· keys encrypted at rest</span>
                </div>
                <div className="card-b">
                  {providers.map((p) => {
                    const has = keyedIds.has(p.id);
                    return (
                      <div className="prow" key={p.id}>
                        <span className="plogo">{p.label[0]}</span>
                        <div style={{ flex: 1 }}>
                          <div className="pn">{p.label}</div>
                          <div className="pm">{p.models.slice(0, 4).join(', ') || 'no key needed'}</div>
                        </div>
                        {has ? (
                          <span className="badge ok">
                            <span className="hd ok" />
                            Key set
                          </span>
                        ) : p.needsKey ? (
                          <span className="badge off">
                            <span className="hd un" />
                            No key
                          </span>
                        ) : (
                          <span className="badge off">Keyless</span>
                        )}
                        {p.needsKey && (
                          <button
                            className="btn sm"
                            onClick={() => {
                              setKeyFor(p);
                              setKeyInput('');
                            }}
                          >
                            {has ? 'Replace' : 'Add key'}
                          </button>
                        )}
                        {has && (
                          <button
                            className="btn sm danger"
                            disabled={removeKey.isPending}
                            onClick={() =>
                              void removeKey
                                .mutateAsync(p.id)
                                .then(() => toast(`Key removed for ${p.label}`, 'success'))
                                .catch(() => toast(`Could not remove the key for ${p.label}`, 'error'))
                            }
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {tab === 'execution' && (
            <div className="card">
              <div className="card-h">
                <h3>Execution</h3>
              </div>
              <div className="card-b">
                <div className="field">
                  <span className="label">Kali image</span>
                  <input className="input mono" value={draft.execution.dockerImage} onChange={(e) => setExec({ dockerImage: e.target.value })} />
                </div>
                <button className="btn pri" disabled={save.isPending} onClick={onSave}>
                  Save
                </button>
              </div>
            </div>
          )}

          {tab === 'scope' && (
            <div className="card">
              <div className="card-h">
                <h3>Scope guardrails</h3>
                <span className="cs">· enforced before every command</span>
              </div>
              <div className="card-b">
                <div className="formrow">
                  <div>
                    <div className="ft">Allow private / loopback targets</div>
                    <div className="fd">Permit tool commands against RFC1918 and loopback hosts.</div>
                  </div>
                  <button
                    className={`toggle${draft.scope.allowPrivateTargets ? ' on' : ''}`}
                    onClick={() => setScope({ allowPrivateTargets: !draft.scope.allowPrivateTargets })}
                  >
                    <i />
                  </button>
                </div>
                <div className="field" style={{ marginTop: 14 }}>
                  <span className="label">Max requests per second</span>
                  <input
                    className="input"
                    type="number"
                    style={{ width: 140 }}
                    value={String(draft.scope.requestsPerSecond)}
                    onChange={(e) => setScope({ requestsPerSecond: Number(e.target.value) || 0 })}
                  />
                </div>
                <button className="btn pri" disabled={save.isPending} onClick={onSave}>
                  Save
                </button>
              </div>
            </div>
          )}

          {tab === 'branding' && (
            <div className="card">
              <div className="card-h">
                <h3>Report branding</h3>
              </div>
              <div className="card-b">
                <div className="grid2">
                  <div className="field">
                    <span className="label">Company / team name</span>
                    <input className="input" value={draft.report.companyName} placeholder="REDCELL" onChange={(e) => setReport({ companyName: e.target.value })} />
                  </div>
                  <div className="field">
                    <span className="label">Classification</span>
                    <input className="input" value={draft.report.classification} placeholder="CONFIDENTIAL" onChange={(e) => setReport({ classification: e.target.value })} />
                  </div>
                </div>
                <div className="field">
                  <span className="label">
                    Prepared by / contact <span className="opt">— shown on the cover</span>
                  </span>
                  <input
                    className="input"
                    value={draft.report.contact ?? ''}
                    placeholder="Security Team, security@company.com"
                    onChange={(e) => setReport({ contact: e.target.value })}
                  />
                </div>
                <button className="btn pri" disabled={save.isPending} onClick={onSave}>
                  Save branding
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <Dialog
        open={!!keyFor}
        onClose={() => setKeyFor(null)}
        title={keyFor ? `${keyFor.label} API key` : 'API key'}
        footer={
          <>
            <button className="btn" onClick={() => setKeyFor(null)}>
              Cancel
            </button>
            <button className="btn pri" disabled={!keyInput.trim() || setKey.isPending} onClick={saveKey}>
              Save key
            </button>
          </>
        }
      >
        <div className="field" style={{ margin: 0 }}>
          <span className="label">API key</span>
          <input
            className="input mono"
            type="password"
            autoFocus
            value={keyInput}
            placeholder="sk-..."
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && keyInput.trim() && void saveKey()}
          />
        </div>
      </Dialog>
    </div>
  );
}
