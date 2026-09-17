"use client";

import { useActionState } from "react";
import type { FormEventHandler } from "react";

import { INITIAL_FORM_STATE } from "./form-state";
import type { WorkforceFormAction } from "./form-state";


type RoleOption = { id: string; name: string };

export function EmployeeForm({
  roles,
  onSubmit,
  action,
}: {
  roles: RoleOption[];
  onSubmit?: FormEventHandler<HTMLFormElement>;
  action?: WorkforceFormAction;
}) {
  const [state, formAction, isPending] = useActionState(
    action ?? (async (currentState) => currentState),
    INITIAL_FORM_STATE,
  );
  return (
    <form action={action ? formAction : undefined} className="entity-form" onSubmit={onSubmit}>
      <label>
        Matrícula
        <input maxLength={40} name="employee_number" required />
      </label>
      <label>
        Nome
        <input maxLength={180} name="name" required />
      </label>
      <label>
        Cargo canônico
        <select name="canonical_role_id" required>
          <option value="">Selecione</option>
          {roles.map((role) => (
            <option key={role.id} value={role.id}>
              {role.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Base
        <input maxLength={80} name="base_location" required />
      </label>
      <label>
        Senioridade
        <select name="seniority_level" required>
          <option value="júnior">Júnior</option>
          <option value="pleno">Pleno</option>
          <option value="sênior">Sênior</option>
          <option value="especialista">Especialista</option>
        </select>
      </label>
      <button disabled={isPending} type="submit">
        {isPending ? "Salvando…" : "Salvar colaborador"}
      </button>
      <p aria-live="polite" className={`form-feedback form-feedback-${state.status}`} role="status">
        {state.message}
      </p>
    </form>
  );
}
