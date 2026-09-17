"use server";

import { revalidatePath } from "next/cache";
import type { OptimizationScenario } from "@/lib/api";
import { ApiError, optimizeOperation, runEligibility } from "@/lib/api";

export type PlannerActionState = { status: "idle" | "success" | "error"; message: string };

function field(formData: FormData, name: string): string {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function errorState(error: unknown): PlannerActionState {
  if (error instanceof ApiError) {
    return { status: "error", message: `${error.message} Revise a operação e tente novamente.` };
  }
  return { status: "error", message: "Não foi possível concluir. Verifique a API e tente novamente." };
}

export async function runEligibilityAction(_state: PlannerActionState, formData: FormData): Promise<PlannerActionState> {
  try {
    await runEligibility(field(formData, "operation_id"));
    revalidatePath("/planejador");
    return { status: "success", message: "Elegibilidade recalculada com sucesso." };
  } catch (error) { return errorState(error); }
}

export async function optimizeOperationAction(_state: PlannerActionState, formData: FormData): Promise<PlannerActionState> {
  try {
    const objective = field(formData, "objective") as OptimizationScenario["objective"];
    await optimizeOperation(field(formData, "operation_id"), objective);
    revalidatePath("/planejador");
    return { status: "success", message: "Cenário calculado e salvo com sucesso." };
  } catch (error) { return errorState(error); }
}
