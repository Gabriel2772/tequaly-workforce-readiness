"use client";

import { useActionState } from "react";

import type { QualificationReference } from "@/lib/api";

import { INITIAL_FORM_STATE } from "./form-state";
import type { WorkforceFormAction } from "./form-state";


export function ReferenceCatalog({
  qualifications,
  createAction,
}: {
  qualifications: QualificationReference[];
  createAction?: WorkforceFormAction;
}) {
  const [state, formAction, isPending] = useActionState(
    createAction ?? (async (currentState) => currentState),
    INITIAL_FORM_STATE,
  );
  return (
    <div className="catalog-layout">
      <section aria-labelledby="new-qualification-title" className="catalog-form-panel">
        <h2 id="new-qualification-title">Nova qualificação</h2>
        <form action={createAction ? formAction : undefined} className="entity-form">
          <label>
            Código
            <input maxLength={48} name="code" required />
          </label>
          <label>
            Nome
            <input maxLength={180} name="name" required />
          </label>
          <label>
            Categoria
            <input maxLength={64} name="category" required />
          </label>
          <label>
            Validade em dias
            <input min={1} name="validity_days" type="number" />
          </label>
          <button disabled={isPending} type="submit">
            {isPending ? "Salvando…" : "Salvar qualificação"}
          </button>
          <p aria-live="polite" className={`form-feedback form-feedback-${state.status}`} role="status">
            {state.message}
          </p>
        </form>
      </section>
      <div className="table-frame">
        <table aria-label="Catálogo de qualificações" className="data-table">
        <thead>
          <tr>
            <th scope="col">Código</th>
            <th scope="col">Qualificação</th>
            <th scope="col">Categoria</th>
            <th scope="col">Validade</th>
            <th scope="col">Status</th>
          </tr>
        </thead>
        <tbody>
          {qualifications.map((qualification) => (
            <tr key={qualification.id}>
              <td>{qualification.code}</td>
              <td>
                <strong>{qualification.name}</strong>
                {qualification.method ? (
                  <span className="cell-detail">{qualification.method}</span>
                ) : null}
              </td>
              <td>{qualification.category}</td>
              <td>
                {qualification.validity_days
                  ? `${qualification.validity_days} dias`
                  : "Sem vencimento"}
              </td>
              <td>
                <span
                  className={`status ${qualification.active ? "status-active" : "status-inactive"}`}
                >
                  {qualification.active ? "Ativa" : "Inativa"}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </div>
  );
}
