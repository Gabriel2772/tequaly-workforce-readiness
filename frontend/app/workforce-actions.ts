"use server";

import { revalidatePath } from "next/cache";

import type { FormActionState } from "@/features/workforce/form-state";
import { ApiError, createEmployee, createOperation, createQualification } from "@/lib/api";

function required(formData: FormData, field: string): string {
  const value = formData.get(field);
  return typeof value === "string" ? value.trim() : "";
}

function failure(error: unknown, duplicateMessage: string): FormActionState {
  if (error instanceof ApiError && error.status === 409) {
    return { status: "error", message: duplicateMessage };
  }
  if (error instanceof ApiError && error.status === 422) {
    return { status: "error", message: "Revise os campos informados e tente novamente." };
  }
  return { status: "error", message: "Não foi possível salvar. Verifique a API e tente novamente." };
}

export async function createQualificationAction(
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  const validity = required(formData, "validity_days");
  try {
    await createQualification({
      code: required(formData, "code"),
      name: required(formData, "name"),
      category: required(formData, "category"),
      ...(validity ? { validity_days: Number(validity) } : {}),
    });
    revalidatePath("/qualificacoes");
    return { status: "success", message: "Qualificação salva com sucesso." };
  } catch (error) {
    return failure(error, "Já existe uma qualificação com esse código.");
  }
}

export async function createEmployeeAction(
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  try {
    const result = await createEmployee({
      employee_number: required(formData, "employee_number"),
      name: required(formData, "name"),
      canonical_role_id: required(formData, "canonical_role_id"),
      base_location: required(formData, "base_location"),
      seniority_level: required(formData, "seniority_level"),
    });
    revalidatePath("/colaboradores");
    return {
      status: "success",
      message: `Colaborador ${result.employee_number} salvo com sucesso.`,
    };
  } catch (error) {
    return failure(error, "Já existe um colaborador com essa matrícula.");
  }
}

export async function createOperationAction(
  _state: FormActionState,
  formData: FormData,
): Promise<FormActionState> {
  const budget = required(formData, "budget_cents");
  const mobilizationDeadline = required(formData, "mobilization_deadline");
  try {
    const result = await createOperation({
      code: required(formData, "code"),
      name: required(formData, "name"),
      client_name: required(formData, "client_name"),
      base_location: required(formData, "base_location"),
      starts_at: new Date(required(formData, "starts_at")).toISOString(),
      ends_at: new Date(required(formData, "ends_at")).toISOString(),
      ...(mobilizationDeadline
        ? { mobilization_deadline: new Date(mobilizationDeadline).toISOString() }
        : {}),
      ...(budget ? { budget_cents: Number(budget) } : {}),
      demands: [
        {
          role_id: required(formData, "demand_role_id"),
          quantity: Number(required(formData, "demand_quantity")),
          shift_code: required(formData, "shift_code"),
        },
      ],
      requirements: [],
    });
    revalidatePath("/operacoes");
    return { status: "success", message: `Operação ${result.code} salva com sucesso.` };
  } catch (error) {
    return failure(error, "Já existe uma operação com esse código.");
  }
}
