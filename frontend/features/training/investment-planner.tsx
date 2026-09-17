"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { DataTable } from "@/components/data-table";
import type { InvestmentPlanView } from "@/lib/api";
import { planTrainingInvestment } from "@/lib/api";

function money(cents: number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    cents / 100,
  );
}

function positionLabel(count: number): string {
  return count === 1 ? "1 posição" : `${count} posições`;
}

export function InvestmentPlanner({
  initialPlan = null,
}: {
  initialPlan?: InvestmentPlanView | null;
}) {
  const [plan, setPlan] = useState<InvestmentPlanView | null>(initialPlan);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    const data = new FormData(event.currentTarget);
    const horizon = String(data.get("horizon"));
    try {
      setPlan(
        await planTrainingInvestment({
          horizon: `${horizon}T23:59:59Z`,
          budget_cents: Math.round(Number(data.get("budget_reais")) * 100),
          weights: {
            confirmed: Number(data.get("weight_confirmed")),
            probable: Number(data.get("weight_probable")),
            hypothetical: Number(data.get("weight_hypothetical")),
          },
        }),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Não foi possível calcular o investimento.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="planner-panel investment-planner" aria-labelledby="investment-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Visão estratégica</p>
          <h2 id="investment-title">Investimento preventivo em qualificação</h2>
        </div>
        {plan ? <span className="runtime-label">{plan.status} · {plan.runtime_ms} ms</span> : null}
      </header>

      <form className="investment-controls" onSubmit={submit}>
        <label>
          Horizonte
          <input defaultValue={initialPlan?.horizon.slice(0, 10)} name="horizon" required type="date" />
        </label>
        <label>
          Orçamento (R$)
          <input defaultValue={initialPlan ? initialPlan.budget_cents / 100 : 10000} min="0" name="budget_reais" required step="0.01" type="number" />
        </label>
        <label>
          Peso: operações confirmadas
          <input defaultValue={initialPlan?.weights.confirmed ?? 100} min="0" name="weight_confirmed" required type="number" />
        </label>
        <label>
          Peso: operações prováveis
          <input defaultValue={initialPlan?.weights.probable ?? 60} min="0" name="weight_probable" required type="number" />
        </label>
        <label>
          Peso: operações hipotéticas
          <input defaultValue={initialPlan?.weights.hypothetical ?? 30} min="0" name="weight_hypothetical" required type="number" />
        </label>
        <button className="primary-action button-action" disabled={pending} type="submit">
          {pending ? "Otimizando…" : "Otimizar investimento"}
        </button>
        <p aria-live="polite" className="form-feedback form-feedback-error" role="status">{error}</p>
      </form>

      {plan ? (
        <>
          <div className="investment-summary" aria-label="Resumo do investimento">
            <div><span>Investimento</span><strong>{money(plan.total_cost_cents)}</strong></div>
            <div><span>Vagas liberadas</span><strong>{plan.unlocked_position_count}</strong></div>
            <div><span>Ganho potencial ponderado</span><strong>{plan.coverage_gain}</strong></div>
            <div><span>Oportunidades avaliadas</span><strong>{plan.opportunity_count}</strong></div>
          </div>
          <p className="metric-note">
            O ganho potencial pondera oportunidades futuras; não garante alocação simultânea
            da mesma pessoa em operações que ocorram no mesmo período.
          </p>
          {plan.actions.length > 0 ? (
            <DataTable ariaLabel="Investimentos preventivos selecionados">
              <thead><tr><th scope="col">Pessoa</th><th scope="col">Qualificação</th><th scope="col">Conclusão</th><th scope="col">Custo</th><th scope="col">Impacto</th><th scope="col">Operações beneficiadas</th></tr></thead>
              <tbody>
                {plan.actions.map((action) => (
                  <tr key={`${action.employee_id}-${action.training_session_id}`}>
                    <td>{action.employee_name}</td>
                    <td>{action.qualification_name}<span className="cell-detail">{action.training_name}</span></td>
                    <td>{new Date(action.completes_at).toLocaleDateString("pt-BR")}</td>
                    <td>{money(action.cost_cents)}</td>
                    <td>{positionLabel(action.unlocked_position_count)}<span className="cell-detail">ganho {action.coverage_gain}</span></td>
                    <td>{action.benefited_operations.map((operation) => `${operation.operation_name} (peso ${operation.weight})`).join(" · ")}</td>
                  </tr>
                ))}
              </tbody>
            </DataTable>
          ) : <p className="empty-state">Nenhuma capacitação conhecida aumenta a cobertura dentro do horizonte e orçamento informados.</p>}
        </>
      ) : <p className="empty-state">Informe horizonte, orçamento e pesos para comparar as oportunidades de capacitação.</p>}
    </section>
  );
}
