import { useEffect } from 'react';
import { TelemetryClient } from './client';
import { telemetryStore } from './store';

const telemetryClient = new TelemetryClient('/api/ws/telemetry', telemetryStore);

export function useTelemetryConnection(): void {
  useEffect(() => {
    telemetryClient.start();
    return () => telemetryClient.stop();
  }, []);
}
