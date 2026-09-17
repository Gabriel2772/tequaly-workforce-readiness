import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { OptimizationScenario } from "@/lib/api";

import { ScenarioComparison } from "./scenario-comparison";

function scenario(
  objective: OptimizationScenario["objective"],
  overrides: Partial<OptimizationScenario> = {},
): OptimizationScenario {
  return {
    id: objective,
    operation_id: "operation-1",
    objective,
    status: "OPTIMAL",
    solver_version: "9.14",
    rules_version: "1.0.0",
    input_snapshot_hash: "hash",
    runtime_ms: 120,
    metrics: {
      total_incremental_cost_cents: 125_000,
      team_ready_at_epoch_minutes: 29_800_000,
      internal_assignment_count: 4,
      qualified_assignment_count: 3,
      training_count: 1,
      training_minutes: 480,
    },
    assignments: [],
    training: [],
    blockers: [],
    created_by: "planner",
    created_at: "2026-09-01T10:00:00Z",
    ...overrides,
  };
}

describe("ScenarioComparison", () => {
  it("renders the three objectives as accessible tabs and comparable metrics", () => {
    render(
      <ScenarioComparison
        scenarios={[
          scenario("MIN_COST"),
          scenario("FASTEST_READY"),
          scenario("MAX_INTERNAL"),
        ]}
      />,
    );

    expect(screen.getByRole("tablist", { name: "Cenários de otimização" })).not.toBeNull();
    expect(screen.getByRole("tab", { name: "Menor custo" })).not.toBeNull();
    expect(screen.getByRole("tab", { name: "Mais rápido" })).not.toBeNull();
    expect(screen.getByRole("tab", { name: "Aproveitamento interno" })).not.toBeNull();
    expect(screen.getAllByText("R$ 1.250,00")).toHaveLength(3);
  });

  it("announces infeasibility blockers without relying on color", () => {
    render(
      <ScenarioComparison
        scenarios={[
          scenario("MIN_COST", {
            status: "INFEASIBLE",
            blockers: [
              {
                code: "insufficient_candidates",
                demand_id: "demand-1",
                required_headcount: 4,
                available_candidates: 2,
                uncovered_headcount: 2,
                blocking_requirement_ids: ["requirement-1"],
                affected_demand_ids: ["demand-1"],
              },
            ],
          }),
        ]}
      />,
    );

    expect(screen.getByRole("alert")).not.toBeNull();
    expect(screen.getByText(/2 vagas sem cobertura/)).not.toBeNull();
  });
});
