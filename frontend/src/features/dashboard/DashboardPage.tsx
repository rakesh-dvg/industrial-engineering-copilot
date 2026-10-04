import { HealthStatus } from "../../shared/components/HealthStatus";

export function DashboardPage() {
  return (
    <div>
      <section className="card">
        <h2>Welcome</h2>
        <p>
          Industrial Engineering Copilot helps application engineers transform customer RFQs and
          engineering requirements into structured technical requirements, evidence-backed product
          recommendations, and proposal drafts.
        </p>
        <p>This dashboard is the Phase 1 application shell. Workflow screens arrive in later phases.</p>
      </section>
      <div style={{ marginTop: "1rem" }}>
        <HealthStatus />
      </div>
    </div>
  );
}
