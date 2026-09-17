import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OutcomeForm } from "./outcome-form";

describe("OutcomeForm", () => {
  it("collects actual values substitutions and performed training", () => {
    render(
      <OutcomeForm
        assignments={[
          {
            id: "assignment-1",
            employee_id: "employee-1",
            employee_name: "Pessoa planejada",
            role_demand_id: "demand-1",
          },
        ]}
        decisionRunId="run-1"
        onRecorded={() => undefined}
        trainingActions={[
          {
            id: "training-1",
            employee_id: "employee-1",
            employee_name: "Pessoa planejada",
            training_catalog_id: "catalog-1",
            training_name: "NR-35",
          },
        ]}
      />,
    );

    expect(screen.getByLabelText("Custo realizado (R$)")).not.toBeNull();
    expect(screen.getByLabelText("Prontidão real")).not.toBeNull();
    expect(screen.getByLabelText("Substituto de Pessoa planejada (UUID)")).not.toBeNull();
    expect(screen.getByLabelText("NR-35 realizado por Pessoa planejada")).not.toBeNull();
    expect(screen.getByLabelText("Parâmetro de calibração")).not.toBeNull();
    expect(screen.getByLabelText("Categoria da observação")).not.toBeNull();
    expect(screen.getByLabelText("Valor observado")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Registrar resultado" })).not.toBeNull();
  });
});
