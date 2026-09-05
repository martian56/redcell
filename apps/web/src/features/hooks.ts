import { useEffect, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/lib/api';
import type { ChatMessage, FindingStatus, Settings } from '@redcell/api-client';

export function useSessions() {
  const api = useApi();
  return useQuery({ queryKey: ['sessions'], queryFn: () => api.sessions.list() });
}

export function useMe() {
  const api = useApi();
  return useQuery({ queryKey: ['auth', 'me'], queryFn: () => api.auth.me(), staleTime: 60_000 });
}

export function useSession(id: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['session', id],
    queryFn: () => api.sessions.get(id as string),
    enabled: !!id,
  });
}

export function useCreateSession() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof api.sessions.create>[0]) => api.sessions.create(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sessions'] }),
  });
}

export function useRuns(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['runs', sessionId],
    queryFn: () => api.runs.list(sessionId as string),
    enabled: !!sessionId,
  });
}

export function useRun(id: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['run', id],
    queryFn: () => api.runs.get(id as string),
    enabled: !!id,
    refetchInterval: 4000,
  });
}

// Panels poll while open to track a live run without a per-entity websocket.
const LIVE = 2500;

export function useAgentGraph(runId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['agents', runId],
    queryFn: () => api.agents.graph(runId as string),
    enabled: !!runId,
    refetchInterval: LIVE,
  });
}

export function useFindings(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['findings', sessionId],
    queryFn: () => api.findings.list(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: LIVE,
  });
}

export function useShellList(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['shells', sessionId],
    queryFn: () => api.shells.list(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: LIVE,
  });
}

export function useOpenShell(sessionId: string | null) {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (label?: string) =>
      api.shells.open(sessionId as string, { kind: 'interactive', label: label || 'operator' }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shells', sessionId] }),
  });
}

export function useCloseShell(sessionId: string | null) {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.shells.close(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['shells', sessionId] }),
  });
}

export function useListeners(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['listeners', sessionId],
    queryFn: () => api.listeners.list(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: LIVE,
  });
}

export function useProxy(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['proxy', sessionId],
    queryFn: () => api.proxy.history(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: LIVE,
  });
}

export function useAttackSurface(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['hosts', sessionId],
    queryFn: () => api.attackSurface.hosts(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: LIVE,
  });
}

export function useLoot(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['loot', sessionId],
    queryFn: () => api.loot.list(sessionId as string),
    enabled: !!sessionId,
    refetchInterval: LIVE,
  });
}

export function useSetFindingStatus() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: FindingStatus }) =>
      api.findings.setStatus(id, status),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['findings'] }),
  });
}

export function useMergeFindings() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ primaryId, duplicateIds }: { primaryId: string; duplicateIds: string[] }) =>
      api.findings.merge(primaryId, duplicateIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['findings'] }),
  });
}

export function useCreateRun() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      ...input
    }: {
      sessionId: string;
      name: string;
      model: string;
      provider?: string;
      instruction?: string;
    }) => api.runs.create(sessionId, input),
    onSuccess: (_run, vars) => qc.invalidateQueries({ queryKey: ['runs', vars.sessionId] }),
  });
}

export function useRunControls() {
  const api = useApi();
  const qc = useQueryClient();
  const invalidate = (r: { id: string }) => qc.invalidateQueries({ queryKey: ['run', r.id] });
  const pause = useMutation({ mutationFn: (id: string) => api.runs.pause(id), onSuccess: invalidate });
  const resume = useMutation({ mutationFn: (id: string) => api.runs.resume(id), onSuccess: invalidate });
  const stop = useMutation({ mutationFn: (id: string) => api.runs.stop(id), onSuccess: invalidate });
  return { pause, resume, stop };
}

export function useSettings() {
  const api = useApi();
  return useQuery({ queryKey: ['settings'], queryFn: () => api.settings.get() });
}

export function useProviders() {
  const api = useApi();
  return useQuery({ queryKey: ['providers'], queryFn: () => api.settings.providers() });
}

export function useProviderKeys() {
  const api = useApi();
  return useQuery({ queryKey: ['provider-keys'], queryFn: () => api.settings.providerKeys() });
}

export function useAvailableModels() {
  const api = useApi();
  return useQuery({ queryKey: ['available-models'], queryFn: () => api.settings.availableModels() });
}

export function useSetProviderKey() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof api.settings.setProviderKey>[0]) =>
      api.settings.setProviderKey(input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['provider-keys'] });
      qc.invalidateQueries({ queryKey: ['available-models'] });
    },
  });
}

export function useRemoveProviderKey() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (providerId: string) => api.settings.removeProviderKey(providerId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['provider-keys'] });
      qc.invalidateQueries({ queryKey: ['available-models'] });
    },
  });
}

export function useSaveSettings() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (next: Settings) => api.settings.save(next),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['settings'] }),
  });
}

export function useServers() {
  const api = useApi();
  return useQuery({ queryKey: ['servers'], queryFn: () => api.servers.list() });
}

export function useServer(id: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['server', id],
    queryFn: () => api.servers.get(id as string),
    enabled: !!id,
  });
}

export function useCreateServer() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof api.servers.create>[0]) => api.servers.create(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['servers'] }),
  });
}

export function useUpdateServer() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Parameters<typeof api.servers.update>[1] }) =>
      api.servers.update(id, input),
    onSuccess: (_r, { id }) => {
      qc.invalidateQueries({ queryKey: ['servers'] });
      qc.invalidateQueries({ queryKey: ['server', id] });
    },
  });
}

export function useTestServer() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.servers.test(id),
    onSuccess: (_r, id) => {
      qc.invalidateQueries({ queryKey: ['servers'] });
      qc.invalidateQueries({ queryKey: ['server', id] });
    },
  });
}

export function useRemoveServer() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.servers.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['servers'] }),
  });
}

export function useProxies() {
  const api = useApi();
  return useQuery({ queryKey: ['proxies'], queryFn: () => api.proxies.list() });
}

export function useProxyById(id: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['proxy-item', id],
    queryFn: () => api.proxies.get(id as string),
    enabled: !!id,
  });
}

export function useCreateProxy() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof api.proxies.create>[0]) => api.proxies.create(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['proxies'] }),
  });
}

export function useUpdateProxy() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Parameters<typeof api.proxies.update>[1] }) =>
      api.proxies.update(id, input),
    onSuccess: (_r, { id }) => {
      qc.invalidateQueries({ queryKey: ['proxies'] });
      qc.invalidateQueries({ queryKey: ['proxy-item', id] });
    },
  });
}

export function useTestProxy() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.proxies.test(id),
    onSuccess: (_r, id) => {
      qc.invalidateQueries({ queryKey: ['proxies'] });
      qc.invalidateQueries({ queryKey: ['proxy-item', id] });
    },
  });
}

export function useRemoveProxy() {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.proxies.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['proxies'] }),
  });
}

export function useReports(sessionId: string | null) {
  const api = useApi();
  return useQuery({
    queryKey: ['reports', sessionId],
    queryFn: () => api.reports.list(sessionId as string),
    enabled: !!sessionId,
    // Poll until a generating report flips to ready.
    refetchInterval: (q) =>
      (q.state.data ?? []).some((r) => r.status === 'generating') ? 2000 : false,
  });
}

export function useCreateReport(sessionId: string | null) {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: Parameters<typeof api.reports.create>[1]) =>
      api.reports.create(sessionId as string, input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports', sessionId] }),
  });
}

export function useDeleteReport(sessionId: string | null) {
  const api = useApi();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.reports.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['reports', sessionId] }),
  });
}

/** Chat/steer history with live assistant replies. */
export function useChat(runId: string | null) {
  const api = useApi();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  useEffect(() => {
    let active = true;
    setMessages([]);
    if (!runId) return;
    api.chat.history(runId).then((h) => {
      if (active) setMessages(h);
    });
    // Dedupe by id: the operator's own message echoes back over the socket,
    // and StrictMode can double-fire.
    const add = (m: ChatMessage) =>
      setMessages((prev) => (prev.some((x) => x.id === m.id) ? prev : [...prev, m]));
    const unsub = api.chat.subscribe(runId, add);
    return () => {
      active = false;
      unsub();
    };
  }, [api, runId]);

  const send = async (text: string) => {
    if (!runId || !text.trim()) return;
    const msg = await api.chat.send(runId, text.trim());
    setMessages((prev) => (prev.some((x) => x.id === msg.id) ? prev : [...prev, msg]));
  };

  return { messages, send };
}

/** Run event stream, newest first, capped. Loads durable history on mount, then merges live events. */
export function useRunEvents(runId: string | null, max = 60) {
  const api = useApi();
  const [events, setEvents] = useState<import('@redcell/api-client').EventMsg[]>([]);
  useEffect(() => {
    let active = true;
    setEvents([]);
    if (!runId) return;
    // Subscribe first so no live event is lost while history loads.
    const unsub = api.events.subscribe(runId, (e) => {
      setEvents((prev) => (prev.some((x) => x.id === e.id) ? prev : [e, ...prev].slice(0, max)));
    });
    api.events
      .history(runId, { limit: max })
      .then((h) => {
        if (!active) return;
        setEvents((live) => {
          const seen = new Set(live.map((e) => e.id));
          return [...live, ...h.filter((e) => !seen.has(e.id))].slice(0, max);
        });
      })
      .catch(() => {});
    return () => {
      active = false;
      unsub();
    };
  }, [api, runId, max]);
  return events;
}

export function useVersion() {
  const api = useApi();
  return useQuery({
    queryKey: ['system', 'version'],
    queryFn: () => api.system.version(),
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

export function useSelfUpdate() {
  const api = useApi();
  return useMutation({ mutationFn: () => api.system.update() });
}
