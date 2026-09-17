"use client";

import { useState } from "react";

import type { DecisionOutcomeView, DecisionRunTimelineView } from "@/lib/api";

import { OutcomeComparison } from "./outcome-comparison";
import { OutcomeForm } from "./outcome-form";

type OutcomeContext = DecisionRunTimelineView["outcome_context"];

export function OutcomePanel({
  decisionRunId,
  assignments,
  trainingActions,
  initialOutcome,
}: {
  decisionRunId: string;
  assignments: OutcomeContext["assignments"];
  trainingActions: OutcomeContext["training_actions"];
  initialOutcome: DecisionOutcomeView | null;
}) {
  const [outcome, setOutcome] = useState(initialOutcome);
  return outcome ? (
    <OutcomeComparison outcome={outcome} />
  ) : (
    <OutcomeForm
      assignments={assignments}
      decisionRunId={decisionRunId}
      onRecorded={setOutcome}
      trainingActions={trainingActions}
    />
  );
}
