import { DecisionTimeline } from "@/features/decisions/decision-timeline";
import { CalibrationPanel } from "@/features/calibration/calibration-panel";
import { OutcomePanel } from "@/features/decisions/outcome-panel";
import { ScenarioSelection } from "@/features/decisions/scenario-selection";
import { getDecisionRun, listDecisionRuns } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function AuditPage() {
  const collection = await listDecisionRuns();
  const details = await Promise.all(collection.items.map((scenario) => getDecisionRun(scenario.id)));
  const supersededRunIds = new Set(
    details.flatMap((detail) =>
      detail.selection?.supersedes_decision_run_id
        ? [detail.selection.supersedes_decision_run_id]
        : [],
    ),
  );
  const selectedDetail = details.find(
    (detail) => detail.selection && !supersededRunIds.has(detail.run.id),
  ) ?? details[0] ?? null;
  return (
    <main className="workspace-page audit-page">
      <header className="page-header"><div><p className="eyebrow">Auditoria de decisão</p><h1>Escolha humana e histórico reproduzível</h1><p className="page-summary">Compare valores previstos, confirme a escolha e preserve quem decidiu, quando e por quê.</p></div></header>
      <ScenarioSelection scenarios={collection.items} selectedRunId={selectedDetail?.selection?.decision_run_id ?? null} />
      {selectedDetail?.selection ? (
        <OutcomePanel
          assignments={selectedDetail.outcome_context.assignments}
          decisionRunId={selectedDetail.run.id}
          initialOutcome={selectedDetail.outcome}
          trainingActions={selectedDetail.outcome_context.training_actions}
        />
      ) : (
        <section className="planner-panel"><h2>Resultado indisponível</h2><p className="empty-state">Selecione um cenário antes de registrar o resultado real.</p></section>
      )}
      <DecisionTimeline detail={selectedDetail} />
      <CalibrationPanel />
    </main>
  );
}
