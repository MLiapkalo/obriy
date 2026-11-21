import { HealthStatus } from './health/HealthStatus';
import { LinkStatus } from './telemetry/LinkStatus';
import { useTelemetryConnection } from './telemetry/useTelemetryConnection';

function App() {
  useTelemetryConnection();

  return (
    <main>
      <h1>Obriy</h1>
      <HealthStatus />
      <br />
      <LinkStatus />
    </main>
  );
}

export default App;
