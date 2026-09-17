import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ImportWizard } from "./import-wizard";

const { previewImport } = vi.hoisted(() => ({ previewImport: vi.fn() }));
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh: vi.fn() }) }));
vi.mock("@/lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/api")>()),
  previewImport,
  commitImport: vi.fn(),
}));

describe("ImportWizard", () => {
  afterEach(cleanup);

  it("shows dry-run errors and never enables commit for an invalid preview", async () => {
    previewImport.mockResolvedValue({
      token: "batch-1",
      contract: "employees",
      contract_version: "1.0",
      filename: "invalid.csv",
      source_hash: "hash",
      mapping: { Matrícula: "employee_number", Nome: "name" },
      total_rows: 1,
      valid_rows: 0,
      invalid_rows: 1,
      errors: [{
        row: 2,
        code: "unknown_role",
        field: "role_code",
        message: "Cargo desconhecido.",
      }],
      sample_rows: [],
      expires_at: "2026-08-24T12:30:00Z",
    });
    render(<ImportWizard />);
    const file = new File(["conteúdo"], "invalid.csv", { type: "text/csv" });
    Object.defineProperty(file, "arrayBuffer", {
      value: async () => new Uint8Array([1, 2, 3]).buffer,
    });
    fireEvent.change(screen.getByLabelText("Arquivo"), { target: { files: [file] } });
    fireEvent.submit(screen.getByRole("button", { name: "Gerar preview" }).closest("form")!);

    await waitFor(() => expect(previewImport).toHaveBeenCalledOnce());
    expect(screen.getByRole("table", { name: "Inconsistências da importação" })).not.toBeNull();
    expect(screen.getByText("unknown_role")).not.toBeNull();
    expect(screen.queryByRole("button", { name: "Confirmar importação" })).toBeNull();
  });
});
