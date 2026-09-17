"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import type { DecisionOutcomeView, DecisionRunTimelineView } from "@/lib/api";
import { recordDecisionOutcome } from "@/lib/api";

type OutcomeContext = DecisionRunTimelineView["outcome_context"];

export function OutcomeForm({
  decisionRunId,
  assignments,
  trainingActions,
  onRecorded,
}: {
  decisionRunId: string;
  assignments: OutcomeContext["assignments"];
  trainingActions: OutcomeContext["training_actions"];
  onRecorded: (outcome: DecisionOutcomeView) => void;
}) {
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage("");
    const data = new FormData(event.currentTarget);
    const substitutions = assignments.flatMap((assignment) => {
      const actualEmployeeId = String(data.get(`substitution_${assignment.id}`) ?? "").trim();
      return actualEmployeeId
        ? [{ original_assignment_id: assignment.id, actual_employee_id: actualEmployeeId }]
        : [];
    });
    const performedTrainingIds = trainingActions
      .filter((training) => data.get(`training_${training.id}`) === "on")
      .map((training) => training.id);
    const calibrationParameter = String(data.get("calibration_parameter") ?? "");
    const calibrationCategory = String(data.get("calibration_category") ?? "").trim();
    const rawCalibrationValue = String(data.get("calibration_value") ?? "").trim();
    const calibrationObservations =
      calibrationParameter && calibrationCategory && rawCalibrationValue
        ? [
            {
              parameter: calibrationParameter as
                | "training_cost_cents"
                | "mobilization_lead_time_days"
                | "travel_cost_cents",
              category: calibrationCategory,
              value: String(
                calibrationParameter.endsWith("_cents")
                  ? Math.round(Number(rawCalibrationValue) * 100)
                  : Number(rawCalibrationValue),
              ),
            },
          ]
        : [];
    try {
      const actualReadyAt = new Date(String(data.get("actual_ready_at")));
      const outcome = await recordDecisionOutcome(decisionRunId, {
        actual_cost_cents: Math.round(Number(data.get("actual_cost_reais")) * 100),
        actual_ready_at: actualReadyAt.toISOString(),
        substitutions,
        performed_training_action_ids: performedTrainingIds,
        calibration_observations: calibrationObservations,
      });
      onRecorded(outcome);
      setMessage("Resultado registrado e auditado.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Não foi possível registrar o resultado.");
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="planner-panel" aria-labelledby="outcome-form-title">
      <header className="panel-header"><div><p className="eyebrow">Retorno da operação</p><h2 id="outcome-form-title">Registrar resultado real</h2></div></header>
      <form className="outcome-form" onSubmit={submit}>
        <label>Custo realizado (R$)<input min="0" name="actual_cost_reais" required step="0.01" type="number" /></label>
        <label>Prontidão real<input name="actual_ready_at" required type="datetime-local" /></label>
        {assignments.length ? (
          <fieldset><legend>Substituições de equipe</legend>{assignments.map((assignment) => (
            <label key={assignment.id}>Substituto de {assignment.employee_name} (UUID)<input name={`substitution_${assignment.id}`} placeholder="Deixe vazio se não houve troca" type="text" /></label>
          ))}</fieldset>
        ) : null}
        {trainingActions.length ? (
          <fieldset><legend>Treinamentos realizados</legend>{trainingActions.map((training) => (
            <label className="confirmation-check" key={training.id}><input defaultChecked name={`training_${training.id}`} type="checkbox" />{training.training_name} realizado por {training.employee_name}</label>
          ))}</fieldset>
        ) : null}
        <fieldset>
          <legend>Observação para calibração (opcional)</legend>
          <p className="field-help">
            Informe um valor comparável somente quando houver evidência do realizado.
          </p>
          <label>
            Parâmetro de calibração
            <select defaultValue="" name="calibration_parameter">
              <option value="">Não registrar observação</option>
              <option value="training_cost_cents">Custo de treinamento</option>
              <option value="travel_cost_cents">Custo de deslocamento</option>
              <option value="mobilization_lead_time_days">Prazo de mobilização</option>
            </select>
          </label>
          <label>
            Categoria da observação
            <input name="calibration_category" placeholder="Ex.: seguranca, soldagem, Curitiba" />
          </label>
          <label>
            Valor observado
            <input aria-label="Valor observado" min="0" name="calibration_value" step="0.01" type="number" />
            <span className="field-help">Use reais para custos ou dias para prazo.</span>
          </label>
        </fieldset>
        <button className="primary-action button-action" disabled={pending} type="submit">{pending ? "Registrando…" : "Registrar resultado"}</button>
        <p aria-live="polite" className="form-feedback" role="status">{message}</p>
      </form>
    </section>
  );
}
