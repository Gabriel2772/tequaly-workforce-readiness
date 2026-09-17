import { DataTable } from "@/components/data-table";
import type { DecisionOutcomeView } from "@/lib/api";

function money(cents: number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    cents / 100,
  );
}

function signedMoney(cents: number): string {
  return `${cents > 0 ? "+" : ""}${money(cents)}`;
}

function percent(value: number | null, signed = false): string {
  if (value === null) return "Não aplicável";
  return `${signed && value > 0 ? "+" : ""}${value.toLocaleString("pt-BR", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}%`;
}

function duration(minutes: number): string {
  const sign = minutes > 0 ? "+" : minutes < 0 ? "-" : "";
  const absolute = Math.abs(minutes);
  const hours = Math.floor(absolute / 60);
  const remainder = absolute % 60;
  if (!hours) return `${sign}${remainder} min`;
  if (!remainder) return `${sign}${hours} h`;
  return `${sign}${hours} h ${remainder} min`;
}

export function OutcomeComparison({ outcome }: { outcome: DecisionOutcomeView }) {
  const { comparison } = outcome;
  return (
    <section className="planner-panel" aria-labelledby="outcome-comparison-title">
      <header className="panel-header">
        <div><p className="eyebrow">Resultado registrado</p><h2 id="outcome-comparison-title">Previsto versus realizado</h2></div>
        <span className="runtime-label">por {outcome.recorded_by}</span>
      </header>
      <DataTable ariaLabel="Comparativo previsto e realizado">
        <thead><tr><th scope="col">Indicador</th><th scope="col">Previsto</th><th scope="col">Realizado</th><th scope="col">Diferença</th><th scope="col">Variação</th></tr></thead>
        <tbody>
          <tr><th scope="row">Custo</th><td>{money(comparison.cost.predicted_cents)}</td><td>{money(comparison.cost.actual_cents)}</td><td>{signedMoney(comparison.cost.variance_cents)}</td><td>{percent(comparison.cost.variance_percent, true)}</td></tr>
          <tr><th scope="row">Prontidão</th><td>{new Date(comparison.readiness.predicted_at).toLocaleString("pt-BR")}</td><td>{new Date(comparison.readiness.actual_at).toLocaleString("pt-BR")}</td><td>{duration(comparison.readiness.variance_minutes)}</td><td>{comparison.readiness.status === "delayed" ? "Atraso" : comparison.readiness.status === "advanced" ? "Antecipado" : "No prazo"}</td></tr>
          <tr><th scope="row">Treinamentos</th><td>{comparison.training.planned_count}</td><td>{comparison.training.performed_count}</td><td>{comparison.training.unperformed_count} não realizado(s)</td><td>{percent(comparison.training.completion_percent)}</td></tr>
          <tr><th scope="row">Substituições</th><td>0</td><td>{comparison.assignments.substitution_count}</td><td>{comparison.assignments.substitution_count}</td><td>Não aplicável</td></tr>
        </tbody>
      </DataTable>
    </section>
  );
}
