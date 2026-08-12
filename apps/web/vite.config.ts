import path from 'node:path';
import tailwind from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const root = import.meta.dirname;

export default defineConfig({
  plugins: [react(), tailwind()],
  resolve: {
    alias: {
      // Consume the workspace package as TypeScript source (no build step).
      '@redcell/api-client': path.resolve(root, '../../packages/api-client/src/index.ts'),
      '@': path.resolve(root, 'src'),
    },
  },
  server: {
    port: 5183,
    // allow importing files from the monorepo root (the api-client package)
    fs: { allow: ['../..'] },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    // Unit tests only: stores, lib helpers, and the mock client. No backend.
    include: ['src/**/*.test.{ts,tsx}'],
  },
});
