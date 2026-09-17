export type FormActionState = {
  status: "idle" | "success" | "error";
  message: string;
};

export type WorkforceFormAction = (
  state: FormActionState,
  formData: FormData,
) => Promise<FormActionState>;

export const INITIAL_FORM_STATE: FormActionState = { status: "idle", message: "" };
