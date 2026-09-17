"use client";

import { useActionState } from "react";

import { INITIAL_FORM_STATE } from "../workforce/form-state";
import type { WorkforceFormAction } from "../workforce/form-state";


type RoleOption = { id: string; name: string };

export function OperationForm({
  roles,
  action,
}: {
  roles: RoleOption[];
  action?: WorkforceFormAction;
}) {
  const [state, formAction, isPending] = useActionState(
    action ?? (async (currentState) => currentState),
    INITIAL_FORM_STATE,
  );

  return (
    <form action={action ? formAction : undefined} className="entity-form operation-form">
      <label>
        Código
        <input maxLength={48} name="code" required />
      </label>
      <label>
        Nome da operação
        <input maxLength={180} name="name" required />
      </label>
      <label>
        Cliente
        <input maxLength={180} name="client_name" required />
      </label>
      <label>
        Base
        <input maxLength={80} name="base_location" required />
      </label>
      <label>
        Início
        <input name="starts_at" required type="datetime-local" />
      </label>
      <label>
        Fim
        <input name="ends_at" required type="datetime-local" />
      </label>
      <label>
        Prazo de mobilização
        <input name="mobilization_deadline" type="datetime-local" />
      </label>
      <label>
        Orçamento em centavos
        <input min={0} name="budget_cents" type="number" />
      </label>
      <fieldset className="form-fieldset">
        <legend>Demanda inicial</legend>
        <label>
          Cargo demandado
          <select name="demand_role_id" required>
            <option value="">Selecione</option>
            {roles.map((role) => (
              <option key={role.id} value={role.id}>
                {role.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Quantidade
          <input defaultValue={1} min={1} name="demand_quantity" required type="number" />
        </label>
        <label>
          Turno
          <input defaultValue="default" maxLength={32} name="shift_code" required />
        </label>
      </fieldset>
      <button disabled={isPending} type="submit">
        {isPending ? "Salvando…" : "Salvar operação"}
      </button>
      <p aria-live="polite" className={`form-feedback form-feedback-${state.status}`} role="status">
        {state.message}
      </p>
    </form>
  );
}
