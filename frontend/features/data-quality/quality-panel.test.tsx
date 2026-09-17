import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { QualityPanel } from "./quality-panel";

describe("QualityPanel", () => {
  afterEach(cleanup);

  it("shows completeness and an action for every issue", () => {
    render(<QualityPanel overview={{
      active_employees: 100,
      complete_profiles: 92,
      completeness_percent: 92,
      source_mode: "synthetic_demo",
      issues: [{
        code: "incomplete_employee_profile",
        label: "Perfis ativos incompletos",
        count: 8,
        severity: "high",
        action: "Completar dados.",
      }],
    }} />);

    expect(screen.getByText("92%")).not.toBeNull();
    expect(screen.getByText("Perfis ativos incompletos")).not.toBeNull();
    expect(screen.getByText("Completar dados.")).not.toBeNull();
    expect(screen.getByText(/dados sintéticos/)).not.toBeNull();
  });
});
