"use client";

import { useState } from "react";

import type { OptimizationScenario } from "@/lib/api";

import { StatusBadge } from "@/components/status-badge";
import { ScenarioTabs } from "./scenario-tabs";

const objectiveLabels: Record<OptimizationScenario["objective"], string> = {
  MIN_COST: "Menor custo",
  FASTEST_READY: "Mais rápido",
  MAX_INTERNAL: "Aproveitamento interno",
};

const statusLabels: Record<OptimizationScenario["status"], string> = {
  OPTIMAL: "Ótimo",
  FEASIBLE: "Viável",
  INFEASIBLE: "Inviável",
  TIMEOUT: "Tempo esgotado",
  TIMEOUT_FEASIBLE: "Viável no limite de tempo",
  ERROR: "Erro",
};

function numericMetric(scenario: OptimizationScenario, key: string): number {
  const value = scenario.metrics[key];
  return typeof value === "number" ? value : 0;
}

function formatMoney(cents: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(cents / 100);
}

function formatReadyAt(epochMinutes: number): string {
  if (epochMinutes <= 0) return "Imediato";
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(epochMinutes * 60_000));
}

function statusTone(status: OptimizationScenario["status"]) {
  if (status === "OPTIMAL" || status === "FEASIBLE") return "success" as const;
  if (status === "TIMEOUT_FEASIBLE") return "warning" as const;
  return "danger" as const;
}

type ScenarioComparisonProps = { scenarios: OptimizationScenario[] };

export function ScenarioComparison({ scenarios }: ScenarioComparisonProps) {
  const [selected, setSelected] = useState(scenarios[0]?.id ?? "");

  return (
    <section className="planner-panel" aria-labelledby="scenario-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Etapa 2</p>
          <h2 id="scenario-title">Comparação de cenários</h2>
        </div>
      </header>

      <ScenarioTabs
        onSelect={setSelected}
        selectedId={selected}
        tabs={scenarios.map((scenario) => ({ id: scenario.id, label: objectiveLabels[scenario.objective] }))}
      />

      {scenarios.length === 0 ? (
        <p className="empty-state">Gere um cenário para comparar custo, prazo e uso interno.</p>
      ) : (
        <div className="scenario-grid">
          {scenarios.map((scenario) => (
            <article
              aria-labelledby={`scenario-tab-${scenario.id}`}
              className="scenario-card"
              id={`scenario-panel-${scenario.id}`}
              key={scenario.id}
              role="tabpanel"
            >
              <header>
                <h3>{objectiveLabels[scenario.objective]}</h3>
                <StatusBadge tone={statusTone(scenario.status)}>
                  {statusLabels[scenario.status]}
                </StatusBadge>
              </header>
              <dl className="scenario-metrics">
                <div>
                  <dt>Custo incremental</dt>
                  <dd>{formatMoney(numericMetric(scenario, "total_incremental_cost_cents"))}</dd>
                </div>
                <div>
                  <dt>Equipe pronta</dt>
                  <dd>{formatReadyAt(numericMetric(scenario, "team_ready_at_epoch_minutes"))}</dd>
                </div>
                <div>
                  <dt>Aproveitamento interno</dt>
                  <dd>{numericMetric(scenario, "internal_assignment_count")}</dd>
                </div>
                <div>
                  <dt>Já qualificados</dt>
                  <dd>{numericMetric(scenario, "qualified_assignment_count")}</dd>
                </div>
                <div>
                  <dt>Capacitações</dt>
                  <dd>{numericMetric(scenario, "training_count")}</dd>
                </div>
                <div>
                  <dt>Horas de capacitação</dt>
                  <dd>{Math.round(numericMetric(scenario, "training_minutes") / 60)} h</dd>
                </div>
              </dl>
              {scenario.blockers.length > 0 ? (
                <div className="blocker-alert" role="alert">
                  <strong>Cenário sem cobertura integral</strong>
                  {scenario.blockers.map((blocker, index) => (
                    <p key={`${blocker.code}-${blocker.demand_id ?? index}`}>
                      {blocker.uncovered_headcount} vagas sem cobertura; {blocker.available_candidates} candidatos para {blocker.required_headcount} posições.
                    </p>
                  ))}
                </div>
              ) : null}
              <footer>
                Solver {scenario.solver_version} · {scenario.runtime_ms.toLocaleString("pt-BR")} ms
              </footer>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
