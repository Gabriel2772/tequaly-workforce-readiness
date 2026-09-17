import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { applyCalibrationSuggestion, createCalibrationSuggestion } from "@/lib/api";
import type { CalibrationSuggestionView } from "@/lib/api";

import { CalibrationPanel } from "./calibration-panel";

vi.mock("@/lib/api", () => ({
  applyCalibrationSuggestion: vi.fn(),
  createCalibrationSuggestion: vi.fn(),
}));

const suggestion: CalibrationSuggestionView = {
  id: "suggestion-1",
  parameter_name: "training_cost_cents",
  category: "seguranca",
  current_value: "30000",
  proposed_value: "32000",
  sample_size: 8,
  confidence_basis: "median_iqr",
  interquartile_range: "4000",
  rationale: "Mediana de 8 observacoes; IQR 4000.",
  status: "pending",
  created_by: "next-local-user",
  created_at: "2030-01-01T00:00:00Z",
  applied_by: null,
  applied_at: null,
};

describe("CalibrationPanel", () => {
  beforeEach(() => {
    vi.mocked(createCalibrationSuggestion).mockResolvedValue(suggestion);
    vi.mocked(applyCalibrationSuggestion).mockResolvedValue({
      id: "parameter-2",
      name: "training_cost_cents:seguranca",
      version: "v2",
      value: "32000",
      rationale: suggestion.rationale,
      created_at: "2030-01-01T00:01:00Z",
    });
  });

  it("creates, explains and explicitly applies a calibration suggestion", async () => {
    render(<CalibrationPanel />);

    fireEvent.change(screen.getByLabelText("Categoria"), {
      target: { value: "seguranca" },
    });
    fireEvent.submit(screen.getByRole("button", { name: "Gerar sugestão" }).closest("form")!);

    expect(await screen.findByText("R$ 320,00")).not.toBeNull();
    expect(screen.getByText(/8 observações/)).not.toBeNull();
    const applyButton = screen.getByRole("button", { name: "Aplicar parâmetro" });
    expect((applyButton as HTMLButtonElement).disabled).toBe(true);

    fireEvent.click(screen.getByLabelText(/Confirmo a aplicação/));
    fireEvent.click(applyButton);

    await waitFor(() => expect(applyCalibrationSuggestion).toHaveBeenCalledWith("suggestion-1"));
    expect(await screen.findByText(/Versão v2 aplicada/)).not.toBeNull();
  });
});
