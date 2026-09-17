import { OperationsList } from "@/features/dashboard/operations-list";
import { ReadinessSummary } from "@/features/dashboard/readiness-summary";
import { RiskAlerts } from "@/features/dashboard/risk-alerts";
import { getDashboardOverview } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Page() {
  const overview = await getDashboardOverview(180);
  return (
    <main className="workspace-page dashboard-page">
      <header className="dashboard-hero">
        <div>
          <p className="eyebrow">Tequaly Workforce Readiness</p>
          <h1>Visão executiva de prontidão</h1>
          <p>Antecipe lacunas de qualificação, cobertura e capacitação antes que elas afetem a mobilização.</p>
        </div>
        <div className="dashboard-context" aria-label="Contexto dos dados">
          <span><i /> Dados simulados</span>
          <strong>Atualizado {new Date(overview.generated_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}</strong>
        </div>
      </header>
      <ReadinessSummary overview={overview} />
      <div className="dashboard-grid">
        <OperationsList operations={overview.upcoming_operations} />
        <RiskAlerts overview={overview} />
      </div>
    </main>
  );
}
