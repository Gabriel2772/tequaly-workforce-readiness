"use client";

import { useActionState } from "react";
import type { PlannerActionState } from "@/app/planner-actions";
import { optimizeOperationAction, runEligibilityAction } from "@/app/planner-actions";
import type { OptimizationScenario } from "@/lib/api";

const initialState: PlannerActionState = { status: "idle", message: "" };
const objectives: Array<{ value: OptimizationScenario["objective"]; label: string }> = [
  { value: "MIN_COST", label: "Menor custo" },
  { value: "FASTEST_READY", label: "Mais rápido" },
  { value: "MAX_INTERNAL", label: "Aproveitamento interno" },
];

export function PlannerControls({ operationId, canOptimize }: { operationId: string; canOptimize: boolean }) {
  const [eligibilityState, eligibilityAction, eligibilityPending] = useActionState(runEligibilityAction, initialState);
  const [optimizationState, optimizationAction, optimizationPending] = useActionState(optimizeOperationAction, initialState);
  return (
    <section className="planner-toolbar" aria-label="Ações de planejamento">
      <form action={eligibilityAction}>
        <input name="operation_id" type="hidden" value={operationId} />
        <button className="secondary-action" disabled={eligibilityPending} type="submit">{eligibilityPending ? "Avaliando…" : "Recalcular elegibilidade"}</button>
        <p aria-live="polite" className={`form-feedback form-feedback-${eligibilityState.status}`} role="status">{eligibilityState.message}</p>
      </form>
      <form action={optimizationAction}>
        <input name="operation_id" type="hidden" value={operationId} />
        <label>Objetivo<select name="objective" defaultValue="MIN_COST">{objectives.map((objective) => <option key={objective.value} value={objective.value}>{objective.label}</option>)}</select></label>
        <button className="primary-action button-action" disabled={!canOptimize || optimizationPending} type="submit">{optimizationPending ? "Calculando…" : "Gerar cenário"}</button>
        <p aria-live="polite" className={`form-feedback form-feedback-${optimizationState.status}`} role="status">{optimizationState.message || (!canOptimize ? "Calcule a elegibilidade antes de otimizar." : "")}</p>
      </form>
    </section>
  );
}
