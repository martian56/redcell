import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/query';
import { ApiProvider } from '@/lib/api';
import { App } from '@/App';
import '@/styles/tokens.css';
import 'react-mosaic-component/react-mosaic-component.css';
import '@xterm/xterm/css/xterm.css';
import '@/styles/global.css';

const el = document.getElementById('root');
if (!el) throw new Error('#root not found');

createRoot(el).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ApiProvider>
        <App />
      </ApiProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
