import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.reject(new Error('fetch not mocked'))),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// Testing Library only auto-unmounts when test globals are enabled; we import them explicitly instead.
afterEach(cleanup);
