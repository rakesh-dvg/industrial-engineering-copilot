import { useQuery } from "@tanstack/react-query";

import { fetchApiHealth, fetchRootHealth } from "../../api/health";

function statusClass(status: string): string {
  if (status === "ok") {
    return "status-ok";
  }
  if (status === "degraded") {
    return "status-degraded";
  }
  return "status-unavailable";
}

export function HealthStatus() {
  const rootHealth = useQuery({
    queryKey: ["health", "root"],
    queryFn: fetchRootHealth,
  });

  const apiHealth = useQuery({
    queryKey: ["health", "api"],
    queryFn: fetchApiHealth,
  });

  return (
    <section className="card" aria-live="polite">
      <h2>System Health</h2>
      {rootHealth.isLoading || apiHealth.isLoading ? <p>Checking services…</p> : null}
      {rootHealth.isError || apiHealth.isError ? (
        <p className="status-unavailable">
          Unable to reach the backend. Start the API server and refresh this page.
        </p>
      ) : null}
      {rootHealth.data && apiHealth.data ? (
        <>
          <p>
            Application status:{" "}
            <strong className={statusClass(apiHealth.data.status)}>{apiHealth.data.status}</strong>
          </p>
          <ul className="status-list">
            <li>
              <span>Service</span>
              <span>{rootHealth.data.service}</span>
            </li>
            <li>
              <span>Version</span>
              <span>{rootHealth.data.version}</span>
            </li>
            <li>
              <span>Environment</span>
              <span>{rootHealth.data.environment}</span>
            </li>
            <li>
              <span>Database</span>
              <span className={statusClass(apiHealth.data.dependencies.database.status)}>
                {apiHealth.data.dependencies.database.status}
              </span>
            </li>
          </ul>
        </>
      ) : null}
    </section>
  );
}
