import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { useApi } from '@/lib/api';
import { useUI } from '@/store/ui';
import { useRun } from '@/features/hooks';
import { notifyToast } from '@/components/ui/toast';
import { browserNotify, requestNotifyPermission } from '@/lib/notify';
import type { ChatMessage, EventMsg, Notification } from '@redcell/api-client';

// Headless: bridges the active run's chat/event streams to in-app toasts and
// browser notifications. Mounted once at the app root.

function severityFromText(text: string): string | null {
  const m = text.match(/^\[(critical|high|medium|low|info)\]/i);
  return m && m[1] ? m[1].toLowerCase() : null;
}

export function LiveNotifier() {
  const api = useApi();
  const runId = useUI((s) => s.activeRunId);
  const sessionId = useUI((s) => s.activeSessionId);
  const { data: run } = useRun(runId);
  const navigate = useNavigate();
  const lastStatus = useRef<string | null>(null);

  const focusSession = () => {
    if (sessionId) navigate(`/sessions/${sessionId}`);
  };

  const qc = useQueryClient();

  // Ask for notification permission once (best effort; harmless if blocked).
  useEffect(() => {
    void requestNotifyPermission();
  }, []);

  useEffect(() => {
    const onNotif = (n: Notification) => {
      void qc.invalidateQueries({ queryKey: ['notifications'] });
      const tone = n.kind === 'run_failed' || n.kind === 'report_failed' ? 'critical' : 'success';
      notifyToast({
        title: n.title,
        body: n.body?.slice(0, 160),
        tone,
        onClick: () => {
          if (n.link) navigate(n.link.startsWith('/') ? n.link : `/${n.link}`);
        },
      });
    };
    return api.notifications.subscribe(onNotif);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!runId) return;
    const onChat = (m: ChatMessage) => {
      if (m.role !== 'assistant' || !m.options?.length) return; // only questions
      notifyToast({
        title: 'Agent is asking you a question',
        body: m.text.slice(0, 160),
        tone: 'critical',
        onClick: focusSession,
      });
      browserNotify('REDCELL: agent needs your input', {
        body: m.text.slice(0, 180),
        tag: `q-${runId}`,
        requireInteraction: true,
        onClick: focusSession,
      });
    };
    const onEvent = (e: EventMsg) => {
      const text = e.text || '';
      if (e.source === 'listener' && /reverse shell/i.test(text)) {
        notifyToast({ title: 'Reverse shell caught', body: text, tone: 'success', onClick: focusSession });
        browserNotify('REDCELL: reverse shell caught', { body: text, tag: `rs-${runId}`, onClick: focusSession });
      } else if (e.type === 'finding') {
        const sev = severityFromText(text);
        if (sev === 'critical' || sev === 'high') {
          notifyToast({
            title: `New ${sev} finding`,
            body: text.replace(/^\[[^\]]+\]\s*/, ''),
            tone: sev === 'critical' ? 'critical' : 'warning',
            onClick: focusSession,
          });
          browserNotify(`REDCELL: ${sev} finding`, { body: text, tag: `f-${e.id}`, onClick: focusSession });
        }
      }
    };
    const un1 = api.chat.subscribe(runId, onChat);
    const un2 = api.events.subscribe(runId, onEvent);
    return () => {
      un1();
      un2();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [api, runId, sessionId]);

  // Run status transitions -> completed / failed.
  useEffect(() => {
    const st = run?.status ?? null;
    const prev = lastStatus.current;
    if (st && prev && st !== prev && (st === 'completed' || st === 'failed')) {
      const good = st === 'completed';
      notifyToast({ title: good ? 'Run completed' : 'Run failed', tone: good ? 'success' : 'error', onClick: focusSession });
      browserNotify(good ? 'REDCELL: run completed' : 'REDCELL: run failed', {
        tag: `st-${runId}`,
        onClick: focusSession,
      });
    }
    lastStatus.current = st;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run?.status, runId]);

  return null;
}
