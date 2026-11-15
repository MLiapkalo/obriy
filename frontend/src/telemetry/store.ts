import type { components } from '../api/schema';
import { createStore, type StoreApi } from 'zustand/vanilla';

export type Telemetry = components['schemas']['Telemetry'];

export type LinkStatus = 'connecting' | 'live' | 'stale' | 'lost';

export type TelemetryState = {
  status: LinkStatus;
  telemetry: Telemetry | null;
};

export function createTelemetryStore(): StoreApi<TelemetryState> {
  return createStore<TelemetryState>(() => ({
    status: 'connecting',
    telemetry: null,
  }));
}

export const telemetryStore = createTelemetryStore();
