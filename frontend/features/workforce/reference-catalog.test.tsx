import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReferenceCatalog } from "./reference-catalog";


describe("ReferenceCatalog", () => {
  it("offers an accessible qualification creation form beside the catalog", () => {
    render(<ReferenceCatalog qualifications={[]} />);

    expect(screen.getByRole("heading", { name: "Nova qualificação" })).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "Código" })).not.toBeNull();
    expect(screen.getByRole("textbox", { name: "Nome" })).not.toBeNull();
    expect(screen.getByRole("button", { name: "Salvar qualificação" })).not.toBeNull();
  });
});
