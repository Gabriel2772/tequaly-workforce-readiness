import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OperationsList } from "./operations-list";

describe("OperationsList", () => {
  it("marks an operation without eligibility as pending instead of critical", () => {
    render(
      <OperationsList
        operations={[{
          id: "operation-1",
          name: "Parada Sul",
          client_name: "Cliente",
          status: "planning",
          mobilization_deadline: "2030-01-10T08:00:00Z",
          severity: "unknown",
          analysis_status: "pending",
          readiness_percent: null,
          uncovered_position_count: 0,
        }]}
      />,
    );

    expect(screen.getByText("Pendente")).not.toBeNull();
    expect(screen.getByText("Análise pendente")).not.toBeNull();
    expect(screen.queryByText("Crítico")).toBeNull();
  });
});
