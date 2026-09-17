import Link from "next/link";
import { StatusBadge } from "@/components/status-badge";
import type { DashboardOverviewView } from "@/lib/api";

export function RiskAlerts({ overview }: { overview: DashboardOverviewView }) {
  return <div className="dashboard-side-stack">
    <section className="dashboard-panel" aria-labelledby="risk-alerts-title">
      <header className="dashboard-panel-header"><div><p className="eyebrow">Ação recomendada</p><h2 id="risk-alerts-title">Gargalos de cobertura</h2></div><Link className="quiet-link" href="/risco-e-cobertura">Abrir mapa</Link></header>
      {overview.risk_alerts.length ? <ul className="alert-list">{overview.risk_alerts.slice(0, 5).map((alert) => <li key={alert.demand_id}>
        <div><StatusBadge tone="danger">{alert.severity === "critical" ? "Crítico" : "Alto"}</StatusBadge><span>{alert.eligible_count}/{alert.required_count} elegíveis</span></div>
        <strong>{alert.role_name}</strong><p>{alert.operation_name} · turno {alert.shift_code}</p><small>{alert.explanation}</small>
      </li>)}</ul> : <p className="empty-state dashboard-empty">Nenhum gargalo alto ou crítico identificado.</p>}
    </section>
    <section className="dashboard-panel" aria-labelledby="expiry-title">
      <header className="dashboard-panel-header"><div><p className="eyebrow">Validade documental</p><h2 id="expiry-title">Próximos vencimentos</h2></div><Link className="quiet-link" href="/qualificacoes">Catálogo</Link></header>
      {overview.expiring_qualifications.length ? <ul className="expiry-list">{overview.expiring_qualifications.slice(0, 5).map((expiry) => <li key={`${expiry.employee_id}-${expiry.qualification_id}`}><div><strong>{expiry.employee_name}</strong><span>{expiry.qualification_name}</span></div><time dateTime={expiry.expires_on}>{expiry.days_remaining} {expiry.days_remaining === 1 ? "dia" : "dias"}</time></li>)}</ul> : <p className="empty-state dashboard-empty">Sem vencimentos no horizonte selecionado.</p>}
    </section>
  </div>;
}
