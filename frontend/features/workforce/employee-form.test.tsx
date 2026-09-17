import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EmployeeForm } from "./employee-form";


describe("EmployeeForm", () => {
  it("provides required fields and a live server-feedback region", () => {
    render(<EmployeeForm roles={[]} onSubmit={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "Matrícula" }).hasAttribute("required")).toBe(true);
    expect(screen.getByRole("textbox", { name: "Nome" }).hasAttribute("required")).toBe(true);
    expect(screen.getByRole("status")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Salvar colaborador" })).not.toBeNull();
  });
});
