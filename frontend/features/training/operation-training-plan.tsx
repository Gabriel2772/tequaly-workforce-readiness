import { DataTable } from "@/components/data-table";
import { StatusBadge } from "@/components/status-badge";
import type { OperationTrainingPlanView } from "@/lib/api";

function money(cents: number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    cents / 100,
  );
}

function impactLabel(count: number): string {
  return count === 1 ? "1 posição liberada" : `${count} posições liberadas`;
}

export function OperationTrainingPlan({ plan }: { plan: OperationTrainingPlanView }) {
  return (
    <section className="planner-panel" aria-labelledby="training-plan-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Capacitação</p>
          <h2 id="training-plan-title">Plano de capacitação operacional</h2>
        </div>
        <span className="runtime-label">
          {money(plan.total_cost_cents)} · {Math.round(plan.total_duration_minutes / 60)} h
        </span>
      </header>

      {plan.actions.length > 0 ? (
        <DataTable ariaLabel="Capacitações propostas">
          <thead>
            <tr>
              <th scope="col">Pessoa</th>
              <th scope="col">Lacuna</th>
              <th scope="col">Curso e turma</th>
              <th scope="col">Conclusão</th>
              <th scope="col">Custo</th>
              <th scope="col">Impacto</th>
            </tr>
          </thead>
          <tbody>
            {plan.actions.map((action) => (
              <tr key={`${action.employee_id}-${action.qualification_id}`}>
                <td>{action.employee_name}</td>
                <td>{action.qualification_name}</td>
                <td>
                  {action.training_name}
                  <span className="cell-detail">{Math.round(action.duration_minutes / 60)} h</span>
                </td>
                <td>{new Date(action.completes_at).toLocaleString("pt-BR")}</td>
                <td>{money(action.cost_cents)}</td>
                <td><StatusBadge tone="success">{impactLabel(action.unlocked_position_count)}</StatusBadge></td>
              </tr>
            ))}
          </tbody>
        </DataTable>
      ) : (
        <p className="empty-state">Nenhuma ação de capacitação viável foi identificada.</p>
      )}

      {plan.blockers.length > 0 ? (
        <div className="training-blockers blocker-alert" role="alert">
          <strong>Gaps sem turma viável</strong>
          <ul>
            {plan.blockers.map((blocker) => (
              <li key={`${blocker.employee_id}-${blocker.qualification_id}`}>
                <b>{blocker.employee_name}</b> · {blocker.qualification_name}: {blocker.message}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
