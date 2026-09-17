import type { EligibilityRun } from "@/lib/api";

import { StatusBadge } from "@/components/status-badge";

type EligibilitySummaryProps = { run: EligibilityRun };

export function EligibilitySummary({ run }: EligibilitySummaryProps) {
  const reasons = Array.from(
    new Map(
      run.results.flatMap((result) => result.reasons).map((reason) => [reason.code, reason]),
    ).values(),
  );

  return (
    <section className="planner-panel" aria-labelledby="eligibility-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Etapa 1</p>
          <h2 id="eligibility-title">Elegibilidade determinística</h2>
        </div>
        <span className="runtime-label">{run.runtime_ms.toLocaleString("pt-BR")} ms</span>
      </header>

      <div className="metric-grid" aria-label="Resumo da elegibilidade">
        <article className="metric-card">
          <StatusBadge tone="success">Elegível</StatusBadge>
          <strong>{run.eligible_count} elegíveis</strong>
          <span>Prontos sem ação adicional</span>
        </article>
        <article className="metric-card">
          <StatusBadge tone="warning">Treinável</StatusBadge>
          <strong>{run.trainable_count} treináveis</strong>
          <span>Prontos após capacitação viável</span>
        </article>
        <article className="metric-card">
          <StatusBadge tone="danger">Inelegível</StatusBadge>
          <strong>{run.ineligible_count} inelegíveis</strong>
          <span>Com impedimento operacional</span>
        </article>
        <article className="metric-card">
          <StatusBadge tone="info">Avaliados</StatusBadge>
          <strong>{run.evaluated_count}</strong>
          <span>de {run.candidate_count} candidatos</span>
        </article>
      </div>

      {reasons.length > 0 ? (
        <div className="reason-summary">
          <h3>Motivos identificados</h3>
          <ul>
            {reasons.map((reason) => (
              <li key={reason.code}>{reason.message}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
