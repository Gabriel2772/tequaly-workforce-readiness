import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import type { DashboardOverviewView } from "@/lib/api";

const tones = { unknown: "neutral", low: "success", medium: "warning", high: "danger", critical: "danger" } as const;
const labels = { unknown: "Pendente", low: "Baixo", medium: "Médio", high: "Alto", critical: "Crítico" };

export function OperationsList({ operations }: { operations: DashboardOverviewView["upcoming_operations"] }) {
  return (
    <section className="dashboard-panel" aria-labelledby="upcoming-operations-title">
      <header className="dashboard-panel-header"><div><p className="eyebrow">Mobilizações futuras</p><h2 id="upcoming-operations-title">Operações prioritárias</h2></div><Link className="quiet-link" href="/operacoes">Ver todas</Link></header>
      {operations.length ? <div className="operation-stack">{operations.slice(0, 7).map((operation) => (
        <Link className="operation-row" href={`/operacoes/${operation.id}`} key={operation.id}>
          <div className="operation-date"><strong>{new Date(operation.mobilization_deadline).toLocaleDateString("pt-BR", { day: "2-digit" })}</strong><span>{new Date(operation.mobilization_deadline).toLocaleDateString("pt-BR", { month: "short" }).replace(".", "")}</span></div>
          <div className="operation-copy"><strong>{operation.name}</strong><span>{operation.client_name} · {operation.status}</span></div>
          {operation.readiness_percent === null ? <div className="coverage-meter coverage-meter-pending"><span /><small>Análise pendente</small></div> : <div className="coverage-meter" aria-label={`${operation.readiness_percent}% de cobertura`}><span><i style={{ width: `${Math.min(operation.readiness_percent, 100)}%` }} /></span><small>{operation.readiness_percent.toLocaleString("pt-BR")}% coberta</small></div>}
          <StatusBadge tone={tones[operation.severity]}>{labels[operation.severity]}</StatusBadge>
        </Link>
      ))}</div> : <p className="empty-state dashboard-empty">Nenhuma operação prevista neste horizonte.</p>}
    </section>
  );
}
