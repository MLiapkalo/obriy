import { screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { components } from '../api/schema';
import { renderWithQueryClient } from '../test/render';
import { HealthStatus } from './HealthStatus';

type Readiness = components['schemas']['ReadinessResponse'];

function readiness(db: 'ok' | 'error'): Readiness {
  return {
    status: db === 'ok' ? 'ok' : 'degraded',
    checks: { db: { status: db, latency_ms: 1.2, detail: db === 'ok' ? null : 'ConnectionRefusedError' } },
  };
}

function respondWith(makeResponse: () => Response) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.resolve(makeResponse())),
  );
}

describe('HealthStatus', () => {
  it('shows API and DB ok on 200', async () => {
    respondWith(() => Response.json(readiness('ok'), { status: 200 }));

    renderWithQueryClient(<HealthStatus />);

    expect(await screen.findByText('API: ok · DB: ok')).toBeInTheDocument();
  });

  it('shows DB error on 503', async () => {
    respondWith(() => Response.json(readiness('error'), { status: 503 }));

    renderWithQueryClient(<HealthStatus />);

    expect(await screen.findByText('API: ok · DB: error')).toBeInTheDocument();
  });

  it('shows API error on 502', async () => {
    respondWith(() => new Response('Bad Gateway', { status: 502 }));

    renderWithQueryClient(<HealthStatus />);

    expect(await screen.findByText('API: Error')).toBeInTheDocument();
  });
});
