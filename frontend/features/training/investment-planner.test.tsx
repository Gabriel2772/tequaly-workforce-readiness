import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { InvestmentPlanner } from "./investment-planner";

describe("InvestmentPlanner", () => {
  it("shows configurable weights and the selected investment impact", () => {
    render(
      <InvestmentPlanner
        initialPlan={{
          horizon: "2027-03-31T23:59:59Z",
          budget_cents: 100_000,
          weights: { confirmed: 100, probable: 60, hypothetical: 30 },
          status: "OPTIMAL",
          actions: [
            {
              employee_id: "employee-1",
              employee_name: "Maria Souza",
              qualification_id: "qualification-1",
              qualification_name: "NR-35",
              training_catalog_id: "training-1",
              training_name: "Trabalho em altura",
              training_session_id: "session-1",
              completes_at: "2027-02-10T17:00:00Z",
              cost_cents: 50_000,
              coverage_gain: 160,
              unlocked_position_count: 2,
              benefited_operations: [
                {
                  operation_id: "operation-1",
                  operation_name: "Parada Sul",
                  weight: 100,
                  unlocked_position_count: 1,
                },
                {
                  operation_id: "operation-2",
                  operation_name: "Expansão Norte",
                  weight: 60,
                  unlocked_position_count: 1,
                },
              ],
            },
          ],
          total_cost_cents: 50_000,
          coverage_gain: 160,
          unlocked_position_count: 2,
          opportunity_count: 3,
          runtime_ms: 12,
        }}
      />,
    );

    expect(screen.getByLabelText("Peso: operações confirmadas")).not.toBeNull();
    expect(screen.getByLabelText("Peso: operações prováveis")).not.toBeNull();
    expect(screen.getByLabelText("Peso: operações hipotéticas")).not.toBeNull();
    expect(screen.getByRole("table", { name: "Investimentos preventivos selecionados" })).not.toBeNull();
    expect(screen.getByText("Maria Souza")).not.toBeNull();
    expect(screen.getByText("2 posições")).not.toBeNull();
    expect(screen.getByText(/Parada Sul/)).not.toBeNull();
    expect(screen.getByText("Ganho potencial ponderado")).not.toBeNull();
    expect(screen.getByText(/garante aloca.*simult/)).not.toBeNull();
    expect(screen.getAllByText("R$ 500,00")).toHaveLength(2);
  });
});
