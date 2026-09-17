import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { getDashboardOverview } from "@/lib/api";

import Page from "./page";

vi.mock("@/lib/api", () => ({ getDashboardOverview: vi.fn() }));

describe("overview page", () => {
  it("exposes the operational overview and its live metrics", async () => {
    vi.mocked(getDashboardOverview).mockResolvedValue({
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
    });
    render(await Page());

    expect(
      screen.getByRole("heading", {
        level: 1,
        name: "Visão executiva de prontidão",
      }),
    ).not.toBeNull();
    expect(screen.getByText("82,5%")).not.toBeNull();
  });
});
