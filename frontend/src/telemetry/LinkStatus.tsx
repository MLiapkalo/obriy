import { useStore } from 'zustand';
import { telemetryStore } from './store';

export function LinkStatus() {
  const status = useStore(telemetryStore, (state) => state.status);
  return <output data-status={status}>Link: {status}</output>;
}
