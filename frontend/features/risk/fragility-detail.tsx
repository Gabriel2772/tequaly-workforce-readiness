import type { FragilityReportView } from "@/lib/api";

type Cell = FragilityReportView["cells"][number];

export function FragilityDetail({ cell }: { cell: Cell | null }) {
  if (!cell) {
    return <aside aria-label="Detalhe da fragilidade" className="fragility-detail" role="region"><p className="empty-state">Selecione uma célula para inspecionar as causas.</p></aside>;
  }
  return (
    <aside aria-labelledby="fragility-detail-title" className="fragility-detail" role="region">
      <header>
        <p className="eyebrow">Explicação</p>
        <h2 id="fragility-detail-title">Detalhe da fragilidade</h2>
        <p>{cell.operation_name} · {cell.role_name} · turno {cell.shift_code}</p>
      </header>
      <dl className="fragility-metrics">
        <div><dt>Cobertura</dt><dd>{cell.metric.eligible_count} / {cell.metric.required_count}</dd></div>
        <div><dt>Redundância</dt><dd>{cell.metric.redundancy}</dd></div>
        <div><dt>Treináveis</dt><dd>{cell.metric.trainable_count}</dd></div>
        <div><dt>Vencimentos</dt><dd>{cell.metric.expiring_count}</dd></div>
        <div><dt>Alocações concorrentes</dt><dd>{cell.metric.allocated_count}</dd></div>
        <div><dt>Sem turma viável</dt><dd>{cell.metric.missing_session_count}</dd></div>
      </dl>
      {cell.requirement_names.length ? <p className="detail-requirements"><strong>Requisitos:</strong> {cell.requirement_names.join(" · ")}</p> : null}
      {cell.risk.explanations.length ? (
        <ul className="risk-explanations">
          {cell.risk.explanations.map((explanation) => (
            <li key={explanation.code}>
              <strong>{explanation.message}</strong>
              <span>Limiar: {explanation.threshold} · observado: {explanation.observed}</span>
            </li>
          ))}
        </ul>
      ) : <p className="empty-state">Nenhuma regra de alerta foi acionada.</p>}
    </aside>
  );
}
