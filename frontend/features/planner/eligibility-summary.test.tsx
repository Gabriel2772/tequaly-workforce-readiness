import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import type { EligibilityRun } from "@/lib/api";

import { EligibilitySummary } from "./eligibility-summary";

const run: EligibilityRun = {
  id: "run-1",
  operation_id: "operation-1",
  rules_version: "1.0.0",
  input_hash: "hash",
  status: "completed",
  started_at: "2026-09-01T10:00:00Z",
  finished_at: "2026-09-01T10:00:01Z",
  runtime_ms: 950,
  candidate_count: 12,
  evaluated_count: 12,
  eligible_count: 7,
  trainable_count: 3,
  ineligible_count: 2,
  results: [
    {
      employee_id: "employee-1",
      demand_id: "demand-1",
      classification: "INELIGIBLE",
      reasons: [
        {
          code: "unavailable_for_operation",
          message: "Disponibilidade não cobre a operação.",
          details: {},
        },
      ],
      gaps: [],
      required_training: [],
      ready_at: null,
    },
  ],
};

describe("EligibilitySummary", () => {
  it("announces every status with text and exposes reason details", () => {
    render(<EligibilitySummary run={run} />);

    expect(screen.getByText("7 elegíveis")).not.toBeNull();
    expect(screen.getByText("3 treináveis")).not.toBeNull();
    expect(screen.getByText("2 inelegíveis")).not.toBeNull();
    expect(screen.getByText("Disponibilidade não cobre a operação.")).not.toBeNull();
    expect(screen.getByText("950 ms")).not.toBeNull();
  });
});
