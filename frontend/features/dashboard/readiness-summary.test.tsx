import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { DashboardOverviewView } from "@/lib/api";

import { ReadinessSummary } from "./readiness-summary";

const overview: DashboardOverviewView = {
  generated_at: "2030-01-01T08:00:00Z",
  horizon_days: 180,
  active_employee_count: 1500,
  readiness_percent: 82.5,
  expiring_qualification_count: 34,
  risky_operation_count: 3,
  uncovered_position_count: 12,
  planned_training_cost_cents: 325_000,
  upcoming_operations: [],
  risk_alerts: [],
  expiring_qualifications: [],
};

describe("ReadinessSummary", () => {
  it("shows source-backed workforce readiness KPIs", () => {
    render(<ReadinessSummary overview={overview} />);

    expect(screen.getByText("1.500")).not.toBeNull();
    expect(screen.getByText("82,5%")).not.toBeNull();
    expect(screen.getByText("34")).not.toBeNull();
    expect(screen.getByText("12")).not.toBeNull();
    expect(screen.getByText("R$ 3.250,00")).not.toBeNull();
    expect(screen.getByText(/horizonte de 180 dias/)).not.toBeNull();
  });
});
