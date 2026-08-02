import type { ReactNode } from 'react';
import { useUI } from '@/store/ui';
import { useAgentGraph, useFindings, useRunEvents } from '@/features/hooks';
import { Button, Empty, Pill, SeverityTag } from '@/components/ui/primitives';
import type { Agent, EventMsg, Finding } from '@redcell/api-client';

export function ContextPanel() {
  const engId = useUI((s) => s.activeSessionId);
  const runId = useUI((s) => s.activeRunId);
  const selection = useUI((s) => s.selection);
  const { data: findings } = useFindings(engId);
  const { data: graph } = useAgentGraph(runId);
  const events = useRunEvents(runId);

  if (selection?.type === 'agent' && graph) {
    const agent = graph.nodes.find((n) => n.id === selection.id);
    if (agent) {
      const recent = events.filter((e) => e.source === agent.name).slice(0, 8);
      return <AgentDetail agent={agent} recent={recent} />;
    }
  }

  const finding =
    (selection?.type === 'finding' && findings?.find((f) => f.id === selection.id)) ||
    findings?.find((f) => f.severity === 'critical') ||
    findings?.[0];

  if (!finding) return <Empty>Select a finding or an agent.</Empty>;
  return <FindingDetail finding={finding} />;
}

function Label({ children }: { children: ReactNode }) {
  return (
    <div className="mb-1.5 font-mono text-[10px] font-bold uppercase tracking-[0.14em] text-faint">
      {children}
    </div>
  );
}

function Code({ children }: { children: ReactNode }) {
  return (
    <pre className="overflow-x-auto whitespace-pre-wrap break-all rounded-[var(--radius)] border border-border bg-black px-3 py-2.5 font-mono text-[11.5px] leading-relaxed text-[#c9d1dc]">
      {children}
    </pre>
  );
}

function FindingDetail({ finding }: { finding: Finding }) {
  return (
    <div className="flex flex-col gap-3.5 p-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <SeverityTag sev={finding.severity} cvss={finding.cvss} />
        {finding.status === 'verified' ? <Pill tone="live">✓ verified</Pill> : <Pill>{finding.status}</Pill>}
        {finding.cwe ? <Pill>{finding.cwe}</Pill> : null}
      </div>
      <h2 className="text-sm font-bold leading-snug">{finding.title}</h2>
      <div className="font-mono text-[11px] text-muted">{finding.location}</div>
      {finding.evidenceRequest ? (
        <div>
          <Label>Evidence · request</Label>
          <Code>{finding.evidenceRequest}</Code>
        </div>
      ) : null}
      {finding.evidenceResponse ? (
        <div>
          <Label>Response</Label>
          <Code>{finding.evidenceResponse}</Code>
        </div>
      ) : null}
      {finding.remediation ? (
        <div>
          <Label>Remediation</Label>
          <p className="text-xs text-muted">{finding.remediation}</p>
        </div>
      ) : null}
      <div className="flex flex-wrap gap-2 pt-1">
        <Button variant="primary">Add to report</Button>
        <Button>Open in proxy</Button>
      </div>
    </div>
  );
}

function AgentDetail({ agent, recent }: { agent: Agent; recent: EventMsg[] }) {
  return (
    <div className="flex flex-col gap-3.5 p-3.5">
      <div className="flex items-center gap-2">
        <Pill>{agent.role}</Pill>
        <Pill tone="live">agent</Pill>
      </div>
      <h2 className="font-mono text-sm font-bold">{agent.name}</h2>
      <div>
        <Label>Status</Label>
        <p className="text-xs text-muted">
          {agent.status} · {agent.calls} tool calls
        </p>
      </div>
      <div>
        <Label>Current action</Label>
        <Code>{agent.action || '—'}</Code>
      </div>
      <div>
        <Label>Recent activity</Label>
        {recent.length ? (
          <div className="flex flex-col gap-1">
            {recent.map((e) => (
              <div key={e.id} className="flex gap-2 font-mono text-[11px] leading-relaxed">
                <span className="text-faint">{new Date(e.ts).toLocaleTimeString()}</span>
                <span className="min-w-0 flex-1 truncate text-muted" title={e.text}>
                  {e.text}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-faint">No activity streamed yet for this agent.</p>
        )}
      </div>
    </div>
  );
}
