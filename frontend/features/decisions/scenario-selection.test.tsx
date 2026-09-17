import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { OptimizationScenario } from "@/lib/api";

import { ScenarioSelection } from "./scenario-selection";

const { refresh, selectScenario } = vi.hoisted(() => ({
  refresh: vi.fn(),
  selectScenario: vi.fn(),
}));

vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  selectScenario,
}));

const scenario: OptimizationScenario = {
  id: "run-1",
  operation_id: "operation-1",
  objective: "MIN_COST",
  status: "OPTIMAL",
  solver_version: "9.15",
  rules_version: "1.0.0",
  input_snapshot_hash: "hash",
  runtime_ms: 12,
  metrics: {
    total_incremental_cost_cents: 125_000,
    training_count: 1,
    internal_assignment_count: 4,
  },
  assignments: [],
  training: [],
  blockers: [],
  created_by: "planner@example.com",
  created_at: "2026-08-12T12:00:00Z",
};

describe("ScenarioSelection", () => {
  afterEach(cleanup);

  beforeEach(() => {
    vi.clearAllMocks();
    selectScenario.mockResolvedValue({
      decision_run_id: scenario.id,
      idempotent: false,
    });
  });

  it("shows predicted metrics, human note and explicit confirmation", () => {
    render(<ScenarioSelection scenarios={[scenario]} selectedRunId={null} />);

    expect(screen.getByText("R$ 1.250,00")).not.toBeNull();
    expect(screen.getByText("1 treinamento")).not.toBeNull();
    expect(screen.getByLabelText("Justificativa da escolha")).not.toBeNull();
    expect(screen.getByLabelText("Confirmo que revisei as métricas previstas")).not.toBeNull();
    expect(
      (screen.getByRole("button", { name: "Selecionar cenário" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it("refreshes the audit detail after a scenario is selected", async () => {
    render(<ScenarioSelection scenarios={[scenario]} selectedRunId={null} />);

    fireEvent.click(screen.getByLabelText("Confirmo que revisei as métricas previstas"));
    fireEvent.click(screen.getByRole("button", { name: "Selecionar cenário" }));

    await waitFor(() => expect(selectScenario).toHaveBeenCalledWith("run-1", ""));
    expect(refresh).toHaveBeenCalledOnce();
  });
});
