import type { OptimizationScenario } from "@/lib/api";
import { DataTable } from "@/components/data-table";

type AssignmentTableProps = { scenario: OptimizationScenario | null };

export function AssignmentTable({ scenario }: AssignmentTableProps) {
  if (!scenario || scenario.assignments.length === 0) {
    return (
      <section className="planner-panel" aria-labelledby="assignment-title">
        <h2 id="assignment-title">Equipe proposta</h2>
        <p className="empty-state">Nenhuma alocação disponível para exibir.</p>
      </section>
    );
  }

  return (
    <section className="planner-panel" aria-labelledby="assignment-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Resultado</p>
          <h2 id="assignment-title">Equipe proposta</h2>
        </div>
        <span className="runtime-label">{scenario.assignments.length} alocações</span>
      </header>
      <DataTable ariaLabel="Alocações do cenário">
          <thead>
            <tr><th>Colaborador</th><th>Demanda</th><th>Início</th><th>Fim</th><th>Custo incremental</th></tr>
          </thead>
          <tbody>
            {scenario.assignments.map((assignment) => (
              <tr key={`${assignment.employee_id}-${assignment.demand_id}`}>
                <td>{assignment.employee_id}</td>
                <td>{assignment.demand_id}</td>
                <td>{new Date(assignment.starts_at).toLocaleString("pt-BR")}</td>
                <td>{new Date(assignment.ends_at).toLocaleString("pt-BR")}</td>
                <td>{formatMoney(assignment.incremental_cost_cents)}</td>
              </tr>
            ))}
          </tbody>
      </DataTable>
    </section>
  );
}

function formatMoney(cents: number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    cents / 100,
  );
}
