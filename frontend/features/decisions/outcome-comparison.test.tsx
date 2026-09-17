import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OutcomeComparison } from "./outcome-comparison";

describe("OutcomeComparison", () => {
  it("shows predicted actual absolute and percentage differences", () => {
    render(
      <OutcomeComparison
        outcome={{
          id: "outcome-1",
          decision_run_id: "run-1",
          recorded_by: "supervisor@example.com",
          recorded_at: "2026-10-02T10:00:00Z",
          comparison: {
            cost: {
              predicted_cents: 100_000,
              actual_cents: 125_000,
              variance_cents: 25_000,
              variance_percent: 25,
            },
            readiness: {
              predicted_at: "2026-10-01T08:00:00Z",
              actual_at: "2026-10-01T10:30:00Z",
              variance_minutes: 150,
              status: "delayed",
            },
            assignments: { substitution_count: 1 },
            training: {
              planned_count: 3,
              performed_count: 2,
              unperformed_count: 1,
              completion_percent: 66.67,
            },
          },
          substitutions: [],
        performed_training_action_ids: [],
        calibration_observations: [],
        }}
      />,
    );

    expect(screen.getByRole("table", { name: "Comparativo previsto e realizado" })).not.toBeNull();
    expect(screen.getByText("R$ 1.000,00")).not.toBeNull();
    expect(screen.getByText("R$ 1.250,00")).not.toBeNull();
    expect(screen.getByText("+R$ 250,00")).not.toBeNull();
    expect(screen.getByText("+25,00%")).not.toBeNull();
    expect(screen.getByText("+2 h 30 min")).not.toBeNull();
    expect(screen.getByText("66,67%")).not.toBeNull();
  });
});
