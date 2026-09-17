import { AssignmentTable } from "@/features/planner/assignment-table";
import { EligibilitySummary } from "@/features/planner/eligibility-summary";
import { PlannerControls } from "@/features/planner/planner-controls";
import { ScenarioComparison } from "@/features/planner/scenario-comparison";
import { OperationTrainingPlan } from "@/features/training/operation-training-plan";
import { InvestmentPlanner } from "@/features/training/investment-planner";
import { ApiError, getLatestEligibility, getOperation, getOperationTrainingPlan, listOperations, listScenarios } from "@/lib/api";
import type { EligibilityRun, OperationTrainingPlanView } from "@/lib/api";

export const dynamic = "force-dynamic";

type PageProps = { searchParams: Promise<{ operation?: string }> };

async function latestEligibility(operationId: string): Promise<EligibilityRun | null> {
  try { return await getLatestEligibility(operationId); }
  catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

async function trainingPlan(operationId: string): Promise<OperationTrainingPlanView | null> {
  try { return await getOperationTrainingPlan(operationId); }
  catch (error) {
    if (error instanceof ApiError && error.status === 409) return null;
    throw error;
  }
}

export default async function PlannerPage({ searchParams }: PageProps) {
  const parameters = await searchParams;
  const operations = await listOperations();
  const selectedId = parameters.operation ?? operations.items[0]?.id;

  if (!selectedId) {
    return (
      <main className="workspace-page">
        <header className="page-header"><div><p className="eyebrow">Planejador de equipe</p><h1>Nenhuma operação cadastrada</h1></div></header>
        <p className="empty-state">Cadastre uma operação com demanda para iniciar o planejamento.</p>
      </main>
    );
  }

  const [operation, eligibility, scenarioCollection, operationTrainingPlan] = await Promise.all([
    getOperation(selectedId), latestEligibility(selectedId), listScenarios(selectedId), trainingPlan(selectedId),
  ]);
  const scenarios = scenarioCollection.items;

  return (
    <main className="workspace-page planner-page">
      <header className="page-header planner-page-header">
        <div>
          <p className="eyebrow">Planejador de equipe</p>
          <h1>{operation.name}</h1>
          <p className="page-summary">{operation.client_name} · {operation.base_location} · {operation.demands.reduce((sum, demand) => sum + demand.quantity, 0)} posições</p>
        </div>
        <form className="operation-picker" method="get">
          <label htmlFor="operation">Operação ativa</label>
          <select defaultValue={selectedId} id="operation" name="operation">
            {operations.items.map((item) => <option key={item.id} value={item.id}>{item.code} — {item.name}</option>)}
          </select>
          <button type="submit">Carregar</button>
        </form>
      </header>

      <PlannerControls operationId={selectedId} canOptimize={eligibility !== null} />
      {eligibility ? <EligibilitySummary run={eligibility} /> : (
        <section className="planner-panel"><h2>Elegibilidade ainda não calculada</h2><p className="empty-state">Use “Recalcular elegibilidade” para classificar os candidatos desta operação.</p></section>
      )}
      <ScenarioComparison scenarios={scenarios} />
      {operationTrainingPlan ? <OperationTrainingPlan plan={operationTrainingPlan} /> : null}
      <InvestmentPlanner />
      <AssignmentTable scenario={scenarios[0] ?? null} />
    </main>
  );
}
