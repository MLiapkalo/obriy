import { useHealth } from './useHealth';

export function HealthStatus() {
  const health = useHealth();

  if (health.isPending) return <output>API: ...</output>;
  if (health.isError) return <output>API: Error</output>;

  return <output>API: ok · DB: {health.data.checks.db.status}</output>;
}
