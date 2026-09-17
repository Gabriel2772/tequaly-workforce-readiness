import { InvestmentPlanner } from "@/features/training/investment-planner";
import { OperationTrainingPlan } from "@/features/training/operation-training-plan";
import { ApiError, getOperationTrainingPlan, listOperations } from "@/lib/api";
import type { OperationTrainingPlanView } from "@/lib/api";

export const dynamic = "force-dynamic";

type PageProps = { searchParams: Promise<{ operation?: string }> };

async function trainingPlan(operationId: string): Promise<OperationTrainingPlanView | null> {
  try {
    return await getOperationTrainingPlan(operationId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) return null;
    throw error;
  }
}

export default async function TrainingPage({ searchParams }: PageProps) {
  const parameters = await searchParams;
  const operations = await listOperations();
  const selectedId = parameters.operation ?? operations.items[0]?.id;
  const plan = selectedId ? await trainingPlan(selectedId) : null;
  return (
    <main className="workspace-page training-page">
      <header className="page-header training-page-header">
        <div><p className="eyebrow">Capacitações</p><h1>Preparar pessoas antes do prazo</h1><p className="page-summary">Ações executáveis por operação e priorização preventiva sob orçamento.</p></div>
        {selectedId ? <form className="operation-picker" method="get"><label htmlFor="operation">Operação</label><select defaultValue={selectedId} id="operation" name="operation">{operations.items.map((operation) => <option key={operation.id} value={operation.id}>{operation.code} — {operation.name}</option>)}</select><button type="submit">Carregar</button></form> : null}
      </header>
      {plan ? <OperationTrainingPlan plan={plan} /> : <section className="planner-panel"><h2>Plano ainda indisponível</h2><p className="empty-state">Execute a elegibilidade da operação no Planejador para materializar as lacunas treináveis.</p></section>}
      <InvestmentPlanner />
    </main>
  );
}
