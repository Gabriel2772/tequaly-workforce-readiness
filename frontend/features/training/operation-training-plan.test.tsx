import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OperationTrainingPlan } from "./operation-training-plan";

describe("OperationTrainingPlan", () => {
  it("shows scheduled impact and announces blockers with text", () => {
    render(
      <OperationTrainingPlan
        plan={{
          operation_id: "operation-1",
          decision_run_id: null,
          mobilization_deadline: "2026-09-20T00:00:00Z",
          total_cost_cents: 35_000,
          total_duration_minutes: 360,
          unlocked_position_count: 1,
          actions: [
            {
              employee_id: "employee-1",
              employee_name: "Pessoa Treinável",
              qualification_id: "qualification-1",
              qualification_name: "NR-35",
              training_catalog_id: "training-1",
              training_name: "Trabalho em altura",
              training_session_id: "session-1",
              starts_at: "2026-09-09T09:00:00Z",
              completes_at: "2026-09-09T15:00:00Z",
              cost_cents: 35_000,
              duration_minutes: 360,
              affected_demand_ids: ["demand-1"],
              unlocked_position_count: 1,
            },
          ],
          blockers: [
            {
              employee_id: "employee-2",
              employee_name: "Pessoa sem turma",
              qualification_id: "qualification-2",
              qualification_name: "NR-10",
              code: "no_session_before_deadline",
              message: "Nenhuma turma com vaga termina antes da mobilização.",
              deadline: "2026-09-20T00:00:00Z",
              affected_demand_ids: ["demand-2"],
            },
          ],
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "Plano de capacitação operacional" })).not.toBeNull();
    expect(screen.getByRole("table", { name: "Capacitações propostas" })).not.toBeNull();
    expect(screen.getByText("Pessoa Treinável")).not.toBeNull();
    expect(screen.getByText("NR-35")).not.toBeNull();
    expect(screen.getByText("Trabalho em altura")).not.toBeNull();
    expect(screen.getByText("R$ 350,00")).not.toBeNull();
    expect(screen.getByText("1 posição liberada")).not.toBeNull();
    const alert = screen.getByRole("alert");
    expect(alert).not.toBeNull();
    expect(alert.textContent).toContain("Nenhuma turma com vaga termina antes da mobilização.");
  });
});
