import { createContext, useContext, type ReactNode } from 'react';
import { createApiClient, type ApiClient, type ApiMode } from '@redcell/api-client';

const mode: ApiMode = (import.meta.env.VITE_API_MODE ?? 'mock') as ApiMode;

// Single switch point; callers only see the ApiClient interface.
export const apiClient: ApiClient = createApiClient({
  mode,
  baseUrl: import.meta.env.VITE_API_BASE_URL,
  wsUrl: import.meta.env.VITE_WS_URL,
});

export const apiMode = mode;

// Direct download URL for a stored file. Anchor navigation carries the auth
// cookie and follows the presigned-URL redirect.
const apiBase = (import.meta.env.VITE_API_BASE_URL ?? '/api/v1') as string;
export function fileDownloadUrl(fileId: string): string {
  return `${apiBase}/files/${fileId}`;
}

const ApiContext = createContext<ApiClient>(apiClient);

export function ApiProvider({ children }: { children: ReactNode }) {
  return <ApiContext.Provider value={apiClient}>{children}</ApiContext.Provider>;
}

export function useApi(): ApiClient {
  return useContext(ApiContext);
}
