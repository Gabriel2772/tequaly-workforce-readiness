"use client";

import { useState } from "react";
import type { FormEvent } from "react";
import { useRouter } from "next/navigation";

import { StatusBadge } from "@/components/status-badge";
import type { OptimizationScenario } from "@/lib/api";
import { selectScenario } from "@/lib/api";

const objectiveLabels = {
  MIN_COST: "Menor custo",
  FASTEST_READY: "Maior rapidez",
  MAX_INTERNAL: "Maior aproveitamento interno",
} as const;

function integerMetric(scenario: OptimizationScenario, key: string): number {
  const value = scenario.metrics[key];
  return typeof value === "number" ? value : 0;
}

function money(cents: number): string {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(cents / 100);
}

export function ScenarioSelection({ scenarios, selectedRunId }: { scenarios: OptimizationScenario[]; selectedRunId: string | null }) {
  const router = useRouter();
  const [currentSelection, setCurrentSelection] = useState(selectedRunId);
  const [confirmedRunId, setConfirmedRunId] = useState<string | null>(null);
  const [pendingRunId, setPendingRunId] = useState<string | null>(null);
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>, scenarioId: string) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setPendingRunId(scenarioId);
    setMessage("");
    try {
      const selection = await selectScenario(scenarioId, String(data.get("note") ?? ""));
      setCurrentSelection(selection.decision_run_id);
      setConfirmedRunId(null);
      setMessage(selection.idempotent ? "Este cenário já estava selecionado." : "Cenário selecionado e auditado.");
      router.refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível selecionar o cenário.");
    } finally {
      setPendingRunId(null);
    }
  }

  return (
    <section className="planner-panel" aria-labelledby="selection-title">
      <header className="panel-header"><div><p className="eyebrow">Decisão humana</p><h2 id="selection-title">Selecionar cenário operacional</h2></div></header>
      <div className="selection-grid">
        {scenarios.map((scenario) => {
          const selected = scenario.id === currentSelection;
          const trainingCount = integerMetric(scenario, "training_count");
          return (
            <form className={`selection-card${selected ? " selection-card-current" : ""}`} key={scenario.id} onSubmit={(event) => submit(event, scenario.id)}>
              <header><h3>{objectiveLabels[scenario.objective]}</h3><StatusBadge tone={selected ? "success" : "info"}>{selected ? "Selecionado" : scenario.status}</StatusBadge></header>
              <dl><div><dt>Custo previsto</dt><dd>{money(integerMetric(scenario, "total_incremental_cost_cents"))}</dd></div><div><dt>Capacitação</dt><dd>{trainingCount} {trainingCount === 1 ? "treinamento" : "treinamentos"}</dd></div><div><dt>Aproveitamento interno</dt><dd>{integerMetric(scenario, "internal_assignment_count")}</dd></div></dl>
              <label>Justificativa da escolha<textarea maxLength={500} name="note" placeholder="Registre o contexto da decisão" /></label>
              <label className="confirmation-check"><input checked={confirmedRunId === scenario.id} onChange={(event) => setConfirmedRunId(event.target.checked ? scenario.id : null)} type="checkbox" />Confirmo que revisei as métricas previstas</label>
              <button className="primary-action button-action" disabled={confirmedRunId !== scenario.id || pendingRunId !== null || !["OPTIMAL", "FEASIBLE", "TIMEOUT_FEASIBLE"].includes(scenario.status)} type="submit">{pendingRunId === scenario.id ? "Selecionando…" : "Selecionar cenário"}</button>
            </form>
          );
        })}
      </div>
      <p aria-live="polite" className="form-feedback" role="status">{message}</p>
    </section>
  );
}
