import type { ApiClient } from './client';
import { createHttpClient } from './http/httpClient';
import { createMockClient } from './mock/mockClient';

export type ApiMode = 'mock' | 'http';

export interface ApiConfig {
  mode: ApiMode;
  baseUrl?: string;
  wsUrl?: string;
}

/** Builds an ApiClient from config, either the HTTP or mock implementation. */
export function createApiClient(config: ApiConfig): ApiClient {
  if (config.mode === 'http') {
    if (!config.baseUrl || !config.wsUrl) {
      throw new Error('http api mode requires baseUrl and wsUrl');
    }
    return createHttpClient(config.baseUrl, config.wsUrl);
  }
  return createMockClient();
}
