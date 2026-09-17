import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { OutcomePanel } from "./outcome-panel";

describe("OutcomePanel", () => {
  it("shows the recording form while the selected decision has no outcome", () => {
    render(
      <OutcomePanel
        assignments={[]}
        decisionRunId="run-1"
        initialOutcome={null}
        trainingActions={[]}
      />,
    );

    expect(screen.getByRole("heading", { name: "Registrar resultado real" })).not.toBeNull();
    expect(screen.queryByRole("heading", { name: "Previsto versus realizado" })).toBeNull();
  });
});
