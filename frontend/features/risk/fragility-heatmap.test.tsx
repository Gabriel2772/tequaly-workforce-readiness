import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { FragilityReportView } from "@/lib/api";

import { FragilityHeatmap } from "./fragility-heatmap";

const report: FragilityReportView = {
  generated_at: "2026-08-12T12:00:00Z",
  horizon_days: 180,
  operation_count: 1,
  summary: { low: 0, medium: 0, high: 1, critical: 0 },
  cells: [
    {
      operation_id: "operation-1",
      operation_name: "Parada Sul",
      operation_status: "confirmed",
      mobilization_deadline: "2026-10-01T00:00:00Z",
      demand_id: "demand-1",
      role_id: "role-1",
      role_name: "Soldador",
      shift_code: "day",
      requirement_ids: ["requirement-1"],
      requirement_names: ["NR-35"],
      metric: {
        required_count: 2,
        eligible_count: 2,
        trainable_count: 1,
        expiring_count: 0,
        allocated_count: 0,
        missing_session_count: 0,
        coverage_ratio: 1,
        redundancy: 0,
        single_point_of_failure: true,
      },
      risk: {
        severity: "high",
        reason_codes: ["single_point_of_failure"],
        explanations: [
          {
            code: "single_point_of_failure",
            message: "A cobertura é exata.",
            threshold: 1,
            observed: 0,
          },
        ],
      },
    },
  ],
};

describe("FragilityHeatmap", () => {
  it("exposes numeric and textual risk status without relying on color", () => {
    render(<FragilityHeatmap report={report} />);

    expect(screen.getByRole("table", { name: "Mapa de fragilidade por operação e cargo" })).not.toBeNull();
    expect(
      screen.getByRole("button", {
        name: "Parada Sul, Soldador: risco alto, cobertura 2 de 2, redundância 0",
      }),
    ).not.toBeNull();
    expect(screen.getAllByText("2 / 2")).toHaveLength(2);
    expect(screen.getByText("Alto")).not.toBeNull();
    expect(screen.getByRole("region", { name: "Detalhe da fragilidade" }).textContent).toContain(
      "A cobertura é exata.",
    );
  });
});
