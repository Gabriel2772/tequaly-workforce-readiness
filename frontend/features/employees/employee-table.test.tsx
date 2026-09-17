import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EmployeeTable } from "./employee-table";


describe("EmployeeTable", () => {
  it("renders accessible headers, textual status and profile links", () => {
    render(
      <EmployeeTable
        employees={[
          {
            id: "82bc6ac6-0e8c-489f-a2dc-eace73035679",
            employee_number: "SYN-00001",
            name: "Colaborador Sintético 00001",
            role_name: "Soldador",
            base_location: "Curitiba",
            seniority_level: "pleno",
            active: true,
            updated_at: "2026-08-10T12:00:00Z",
          },
        ]}
      />,
    );

    expect(screen.getByRole("table", { name: "Colaboradores" })).not.toBeNull();
    expect(screen.getByRole("columnheader", { name: "Colaborador" })).not.toBeNull();
    expect(screen.getByText("Ativo")).not.toBeNull();
    expect(
      screen.getByRole("link", { name: "Abrir perfil de Colaborador Sintético 00001" }),
    ).not.toBeNull();
  });
});
