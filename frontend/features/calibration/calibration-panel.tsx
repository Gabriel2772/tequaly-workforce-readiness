"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import {
  applyCalibrationSuggestion,
  createCalibrationSuggestion,
} from "@/lib/api";
import type {
  CalibrationParameterName,
  CalibrationParameterView,
  CalibrationSuggestionView,
} from "@/lib/api";

const parameterLabels: Record<CalibrationParameterName, string> = {
  training_cost_cents: "Custo de treinamento",
  mobilization_lead_time_days: "Prazo de mobilização",
  travel_cost_cents: "Custo de deslocamento",
};

function parameterValue(parameter: CalibrationParameterName, value: string): string {
  if (parameter === "mobilization_lead_time_days") {
    return `${new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 1 }).format(Number(value))} dias`;
  }
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(Number(value) / 100);
}

export function CalibrationPanel() {
  const [suggestion, setSuggestion] = useState<CalibrationSuggestionView | null>(null);
  const [applied, setApplied] = useState<CalibrationParameterView | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState("");

  async function generate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setMessage("");
    setApplied(null);
    setConfirmed(false);
    const data = new FormData(event.currentTarget);
    try {
      const result = await createCalibrationSuggestion({
        parameter: String(data.get("parameter")) as CalibrationParameterName,
        category: String(data.get("category")),
      });
      setSuggestion(result);
    } catch (error) {
      setSuggestion(null);
      setMessage(
        error instanceof Error
          ? error.message
          : "Não foi possível gerar a sugestão de calibração.",
      );
    } finally {
      setPending(false);
    }
  }

  async function apply() {
    if (!suggestion || !confirmed) return;
    setPending(true);
    setMessage("");
    try {
      const result = await applyCalibrationSuggestion(suggestion.id);
      setApplied(result);
      setSuggestion({ ...suggestion, status: "applied" });
      setMessage(`Versão ${result.version} aplicada com trilha de auditoria.`);
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Não foi possível aplicar a calibração.",
      );
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="planner-panel calibration-panel" aria-labelledby="calibration-title">
      <header className="panel-header">
        <div>
          <p className="eyebrow">Aprendizado supervisionado</p>
          <h2 id="calibration-title">Calibração de parâmetros</h2>
          <p className="panel-summary">
            Use resultados reais para propor ajustes robustos. Toda mudança exige confirmação
            humana, cria uma nova versão e preserva o histórico anterior.
          </p>
        </div>
      </header>

      <form className="calibration-controls" onSubmit={generate}>
        <label>
          Parâmetro
          <select defaultValue="training_cost_cents" name="parameter">
            {Object.entries(parameterLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          Categoria
          <input name="category" placeholder="Ex.: seguranca, soldagem, Curitiba" required />
        </label>
        <button className="secondary-action button-action" disabled={pending} type="submit">
          {pending ? "Analisando…" : "Gerar sugestão"}
        </button>
      </form>

      {suggestion ? (
        <div className="calibration-result">
          <div className="calibration-values" aria-label="Comparação da calibração">
            <div><span>Valor vigente</span><strong>{parameterValue(suggestion.parameter_name, suggestion.current_value)}</strong></div>
            <div><span>Valor proposto</span><strong>{parameterValue(suggestion.parameter_name, suggestion.proposed_value)}</strong></div>
            <div><span>Base estatística</span><strong>{suggestion.sample_size} observações</strong></div>
            <div><span>Dispersão (IQR)</span><strong>{parameterValue(suggestion.parameter_name, suggestion.interquartile_range)}</strong></div>
          </div>
          <p className="metric-note">
            Estimativa pela mediana, resistente a valores extremos. {suggestion.rationale}
          </p>
          <label className="confirmation-check">
            <input
              checked={confirmed}
              disabled={suggestion.status !== "pending"}
              onChange={(event) => setConfirmed(event.target.checked)}
              type="checkbox"
            />
            Confirmo a aplicação deste parâmetro e a criação de uma nova versão.
          </label>
          <button
            className="primary-action button-action"
            disabled={!confirmed || pending || suggestion.status !== "pending"}
            onClick={apply}
            type="button"
          >
            Aplicar parâmetro
          </button>
        </div>
      ) : (
        <p className="empty-state">São necessárias pelo menos 5 observações comparáveis.</p>
      )}
      <p aria-live="polite" className="form-feedback" role="status">
        {applied ? `Versão ${applied.version} aplicada. ${message}` : message}
      </p>
    </section>
  );
}
