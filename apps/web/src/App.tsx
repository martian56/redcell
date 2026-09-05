import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthGate } from '@/app/AuthGate';
import { DashboardShell } from '@/app/DashboardShell';
import { ConsolePage } from '@/app/ConsolePage';
import { OverviewPage } from '@/app/pages/OverviewPage';
import { SessionsPage } from '@/app/pages/SessionsPage';
import { NewSessionPage } from '@/app/pages/NewSessionPage';
import { FindingsPage } from '@/app/pages/FindingsPage';
import { ReportsPage } from '@/app/pages/ReportsPage';
import { ServersPage } from '@/app/pages/ServersPage';
import { ServerDetailPage } from '@/app/pages/ServerDetailPage';
import { ProxiesPage } from '@/app/pages/ProxiesPage';
import { ProxyDetailPage } from '@/app/pages/ProxyDetailPage';
import { SettingsPage } from '@/app/pages/SettingsPage';
import { NotificationsPage } from '@/app/pages/NotificationsPage';
import { Toaster } from '@/components/ui/toast';
import { LiveNotifier } from '@/app/LiveNotifier';

export function App() {
  return (
    <BrowserRouter>
      <AuthGate>
        <LiveNotifier />
        <Routes>
          <Route element={<DashboardShell />}>
            <Route path="/overview" element={<OverviewPage />} />
            <Route path="/sessions" element={<SessionsPage />} />
            <Route path="/sessions/new" element={<NewSessionPage />} />
            <Route path="/sessions/:id" element={<ConsolePage />} />
            <Route path="/findings" element={<FindingsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/servers" element={<ServersPage />} />
            <Route path="/servers/:id" element={<ServerDetailPage />} />
            <Route path="/proxies" element={<ProxiesPage />} />
            <Route path="/proxies/:id" element={<ProxyDetailPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/notifications" element={<NotificationsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </AuthGate>
      <Toaster />
    </BrowserRouter>
  );
}
