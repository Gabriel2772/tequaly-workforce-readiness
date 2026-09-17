import type { DashboardOverviewView } from "@/lib/api";

const integer = (value: number) => new Intl.NumberFormat("pt-BR").format(value);
const percent = (value: number | null) => value === null ? "—" : `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(value)}%`;
const money = (cents: number) => new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);

export function ReadinessSummary({ overview }: { overview: DashboardOverviewView }) {
  const metrics = [
    { label: "Cobertura imediata", value: percent(overview.readiness_percent), detail: overview.readiness_percent === null ? "execute a elegibilidade das operações" : "vagas cobertas por pessoas elegíveis", tone: overview.readiness_percent === null ? "neutral" : overview.readiness_percent >= 90 ? "positive" : "attention" },
    { label: "Colaboradores ativos", value: integer(overview.active_employee_count), detail: "base disponível para análise", tone: "neutral" },
    { label: "Posições descobertas", value: integer(overview.uncovered_position_count), detail: "nas operações do horizonte", tone: overview.uncovered_position_count ? "danger" : "positive" },
    { label: "Operações em risco", value: integer(overview.risky_operation_count), detail: "com alerta alto ou crítico", tone: overview.risky_operation_count ? "danger" : "positive" },
    { label: "Qualificações a vencer", value: integer(overview.expiring_qualification_count), detail: "até o fim do horizonte", tone: overview.expiring_qualification_count ? "attention" : "positive" },
    { label: "Capacitação planejada", value: money(overview.planned_training_cost_cents), detail: "investimento já programado", tone: "neutral" },
  ];
  return (
    <section aria-labelledby="readiness-summary-title">
      <div className="section-heading">
        <div><p className="eyebrow">Pulso operacional</p><h2 id="readiness-summary-title">Prontidão no horizonte</h2></div>
        <p>Indicadores calculados para o horizonte de {overview.horizon_days} dias.</p>
      </div>
      <div className="dashboard-kpis">
        {metrics.map((metric) => (
          <article className={`dashboard-kpi dashboard-kpi-${metric.tone}`} key={metric.label}>
            <span>{metric.label}</span><strong>{metric.value}</strong><small>{metric.detail}</small>
          </article>
        ))}
      </div>
    </section>
  );
}
