import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OperationForm } from "./operation-form";


describe("OperationForm", () => {
  it("exposes operation identity, period and initial role demand", () => {
    render(
      <OperationForm
        roles={[
          {
            id: "f01b6782-c8f0-4b22-a754-0436f698f44d",
            name: "Soldador",
          },
        ]}
      />,
    );

    expect(screen.getByRole("textbox", { name: "Código" })).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "Nome da operação" })).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "Cliente" })).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "Base" })).not.toBeNull();
    expect(screen.getByRole("combobox", { name: "Cargo demandado" })).not.toBeNull();
    expect(screen.getByRole("spinbutton", { name: "Quantidade" })).not.toBeNull();
    expect(screen.getByRole("status")).not.toBeNull();
  });
});
