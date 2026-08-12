// Vitest setup: jest-dom matchers, and a clean localStorage between tests so
// persisted zustand stores never leak state across cases.
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';

afterEach(() => {
  localStorage.clear();
});
