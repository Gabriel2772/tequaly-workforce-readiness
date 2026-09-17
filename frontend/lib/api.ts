function apiUrl(): string {
  if (typeof window !== "undefined") {
    return process.env.NEXT_PUBLIC_TWR_API_URL
      ?? `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return process.env.TWR_API_URL ?? "http://localhost:8000";
}

export type EmployeeListItem = {
  id: string;
  employee_number: string;
  name: string;
  role_name: string;
  base_location: string;
  seniority_level: string;
  active: boolean;
  updated_at: string;
};

export type PaginatedEmployees = {
  items: EmployeeListItem[];
  page: number;
  page_size: number;
  total: number;
};

export type DataQualityOverview = {
  active_employees: number;
  complete_profiles: number;
  completeness_percent: number | null;
  source_mode: "synthetic_demo" | "operational";
  issues: Array<{
    code: string;
    label: string;
    count: number;
    severity: "low" | "medium" | "high";
    action: string;
  }>;
};

export type UserSession = {
  id: string;
  username: string;
  display_name: string;
  role: "viewer" | "planner" | "admin";
  expires_at: string;
};

export type McpClientType = "claude" | "chatgpt";
export type McpTransport = "streamable_http" | "sse";
export type McpConnectionInput = {
  name: string;
  client_type: McpClientType;
  endpoint_url: string;
  transport: McpTransport;
  notes?: string | null;
  enabled?: boolean;
};
export type McpConnection = McpConnectionInput & {
  id: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
  last_validated_at: string | null;
};
export type McpConnectionValidation = {
  valid: boolean;
  normalized_endpoint_url: string;
  validated_at: string;
};
export type McpTool = {
  name: string;
  description: string;
  effect: "read";
  input_schema: Record<string, unknown>;
};

export type ImportContractName =
  | "employees"
  | "employee_qualifications"
  | "operations"
  | "training_catalog";

export type ImportPreviewView = {
  token: string;
  contract: ImportContractName;
  contract_version: string;
  filename: string;
  source_hash: string;
  mapping: Record<string, string>;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  errors: Array<{ row: number; code: string; field: string | null; message: string }>;
  sample_rows: Array<Record<string, unknown>>;
  expires_at: string;
};

export type ImportCommitSummary = {
  batch_id: string;
  contract: ImportContractName;
  created: number;
  updated: number;
  total: number;
  idempotent: boolean;
};

export type QualificationSummary = {
  id: string;
  nome: string;
  categoria: string;
  emitida_em: string;
  vence_em: string | null;
  status: string;
};

export type QualificationReference = {
  id: string;
  code: string;
  name: string;
  category: string;
  method: string | null;
  level: string | null;
  validity_days: number | null;
  active: boolean;
  updated_at: string;
};

export type PaginatedQualifications = {
  items: QualificationReference[];
  page: number;
  page_size: number;
  total: number;
};

export type RoleReference = {
  id: string;
  family_id: string;
  code: string;
  name: string;
  active: boolean;
  updated_at: string;
};

export type PaginatedRoles = {
  items: RoleReference[];
  page: number;
  page_size: number;
  total: number;
};

export type EmployeeWriteResult = {
  id: string;
  employee_number: string;
  updated_at: string;
};

export type OperationView = {
  id: string;
  code: string;
  name: string;
  client_name: string;
  base_location: string;
  starts_at: string;
  ends_at: string;
  mobilization_deadline: string | null;
  status: string;
  budget_cents: number | null;
  updated_at: string;
};

export type PaginatedOperations = {
  items: OperationView[];
  page: number;
  page_size: number;
  total: number;
};

export type OperationDetail = OperationView & {
  demands: Array<{
    id: string;
    role_id: string;
    quantity: number;
    shift_code: string;
    priority: number;
  }>;
  requirements: Array<{
    id: string;
    role_demand_id: string | null;
    code: string;
    name: string;
    requirement_type: string;
    mandatory: boolean;
    payload: Record<string, unknown>;
  }>;
};

export type EligibilityReason = {
  code: string;
  message: string;
  details: Record<string, unknown>;
};

export type CandidateEligibility = {
  employee_id: string;
  demand_id: string;
  classification: "ELIGIBLE" | "TRAINABLE" | "INELIGIBLE";
  reasons: EligibilityReason[];
  gaps: Array<Record<string, unknown>>;
  required_training: string[];
  ready_at: string | null;
};

export type EligibilityRun = {
  id: string;
  operation_id: string;
  rules_version: string;
  input_hash: string;
  status: string;
  started_at: string;
  finished_at: string;
  runtime_ms: number;
  candidate_count: number;
  evaluated_count: number;
  eligible_count: number;
  trainable_count: number;
  ineligible_count: number;
  results: CandidateEligibility[];
};

export type OptimizationScenario = {
  id: string;
  operation_id: string;
  objective: "MIN_COST" | "FASTEST_READY" | "MAX_INTERNAL";
  status:
    | "OPTIMAL"
    | "FEASIBLE"
    | "INFEASIBLE"
    | "TIMEOUT"
    | "TIMEOUT_FEASIBLE"
    | "ERROR";
  solver_version: string;
  rules_version: string;
  input_snapshot_hash: string;
  runtime_ms: number;
  metrics: Record<string, unknown>;
  assignments: Array<{
    employee_id: string;
    demand_id: string;
    starts_at: string;
    ends_at: string;
    incremental_cost_cents: number;
  }>;
  training: Array<{
    employee_id: string;
    training_catalog_id: string;
    ready_at: string;
    cost_cents: number;
    duration_minutes: number;
  }>;
  blockers: Array<{
    code: string;
    demand_id: string | null;
    required_headcount: number;
    available_candidates: number;
    uncovered_headcount: number;
    blocking_requirement_ids: string[];
    affected_demand_ids: string[];
  }>;
  created_by: string;
  created_at: string;
};

export type ScenarioCollection = { items: OptimizationScenario[] };

export type OperationTrainingPlanView = {
  operation_id: string;
  decision_run_id: string | null;
  mobilization_deadline: string;
  actions: Array<{
    employee_id: string;
    employee_name: string;
    qualification_id: string;
    qualification_name: string;
    training_catalog_id: string;
    training_name: string;
    training_session_id: string;
    starts_at: string;
    completes_at: string;
    cost_cents: number;
    duration_minutes: number;
    affected_demand_ids: string[];
    unlocked_position_count: number;
  }>;
  blockers: Array<{
    employee_id: string;
    employee_name: string;
    qualification_id: string;
    qualification_name: string;
    code: string;
    message: string;
    deadline: string;
    affected_demand_ids: string[];
  }>;
  total_cost_cents: number;
  total_duration_minutes: number;
  unlocked_position_count: number;
};

export type InvestmentPlanView = {
  horizon: string;
  budget_cents: number;
  weights: { confirmed: number; probable: number; hypothetical: number };
  status: string;
  actions: Array<{
    employee_id: string;
    employee_name: string;
    qualification_id: string;
    qualification_name: string;
    training_catalog_id: string;
    training_name: string;
    training_session_id: string;
    completes_at: string;
    cost_cents: number;
    coverage_gain: number;
    unlocked_position_count: number;
    benefited_operations: Array<{
      operation_id: string;
      operation_name: string;
      weight: number;
      unlocked_position_count: number;
    }>;
  }>;
  total_cost_cents: number;
  coverage_gain: number;
  unlocked_position_count: number;
  opportunity_count: number;
  runtime_ms: number;
};

export type FragilityReportView = {
  generated_at: string;
  horizon_days: number;
  operation_count: number;
  summary: Record<"low" | "medium" | "high" | "critical", number>;
  cells: Array<{
    operation_id: string;
    operation_name: string;
    operation_status: string;
    mobilization_deadline: string;
    demand_id: string;
    role_id: string;
    role_name: string;
    shift_code: string;
    requirement_ids: string[];
    requirement_names: string[];
    metric: {
      required_count: number;
      eligible_count: number;
      trainable_count: number;
      expiring_count: number;
      allocated_count: number;
      missing_session_count: number;
      coverage_ratio: number;
      redundancy: number;
      single_point_of_failure: boolean;
    };
    risk: {
      severity: "low" | "medium" | "high" | "critical";
      reason_codes: string[];
      explanations: Array<{
        code: string;
        message: string;
        threshold: number;
        observed: number;
      }>;
    };
  }>;
};

export type SelectedDecisionView = {
  id: string;
  decision_run_id: string;
  operation_id: string;
  actor_id: string;
  note: string | null;
  selected_at: string;
  supersedes_decision_run_id: string | null;
  idempotent: boolean;
};

export type DecisionRunTimelineView = {
  run: OptimizationScenario;
  selection: SelectedDecisionView | null;
  timeline: Array<{
    event_type: string;
    occurred_at: string;
    actor_id: string | null;
    payload: Record<string, unknown>;
  }>;
  outcome: DecisionOutcomeView | null;
  outcome_context: {
    assignments: Array<{
      id: string;
      employee_id: string;
      employee_name: string;
      role_demand_id: string;
    }>;
    training_actions: Array<{
      id: string;
      employee_id: string;
      employee_name: string;
      training_catalog_id: string;
      training_name: string;
    }>;
  };
};

export type DecisionOutcomeView = {
  id: string;
  decision_run_id: string;
  recorded_by: string;
  recorded_at: string;
  comparison: {
    cost: {
      predicted_cents: number;
      actual_cents: number;
      variance_cents: number;
      variance_percent: number | null;
    };
    readiness: {
      predicted_at: string;
      actual_at: string;
      variance_minutes: number;
      status: string;
    };
    assignments: { substitution_count: number };
    training: {
      planned_count: number;
      performed_count: number;
      unperformed_count: number;
      completion_percent: number | null;
    };
  };
  substitutions: Array<{
    original_assignment_id: string;
    role_demand_id: string;
    original_employee_id: string;
    actual_employee_id: string;
  }>;
  performed_training_action_ids: string[];
  calibration_observations: CalibrationObservation[];
};

export type CalibrationParameterName =
  | "training_cost_cents"
  | "mobilization_lead_time_days"
  | "travel_cost_cents";

export type CalibrationObservation = {
  parameter: CalibrationParameterName;
  category: string;
  value: string;
};

export type CalibrationSuggestionView = {
  id: string;
  parameter_name: CalibrationParameterName;
  category: string;
  current_value: string;
  proposed_value: string;
  sample_size: number;
  confidence_basis: string;
  interquartile_range: string;
  rationale: string;
  status: string;
  created_by: string;
  created_at: string;
  applied_by: string | null;
  applied_at: string | null;
};

export type CalibrationParameterView = {
  id: string;
  name: string;
  version: string;
  value: string;
  rationale: string | null;
  created_at: string;
};

export type DashboardOverviewView = {
  generated_at: string;
  horizon_days: number;
  active_employee_count: number;
  readiness_percent: number | null;
  expiring_qualification_count: number;
  risky_operation_count: number;
  uncovered_position_count: number;
  planned_training_cost_cents: number;
  upcoming_operations: Array<{
    id: string; name: string; client_name: string; status: string;
    mobilization_deadline: string;
    severity: "unknown" | "low" | "medium" | "high" | "critical";
    analysis_status: "pending" | "completed";
    readiness_percent: number | null; uncovered_position_count: number;
  }>;
  risk_alerts: Array<{
    operation_id: string; operation_name: string; demand_id: string;
    role_name: string; shift_code: string;
    severity: "low" | "medium" | "high" | "critical";
    required_count: number; eligible_count: number;
    uncovered_position_count: number; explanation: string;
  }>;
  expiring_qualifications: Array<{
    employee_id: string; employee_name: string; qualification_id: string;
    qualification_name: string; expires_on: string; days_remaining: number;
  }>;
};

export type EmployeeProfile = {
  cargo_funcao_principal: string;
  nome: string;
  qualificacoes: QualificationSummary[];
  competencias_tecnicas: Array<{ nome: string; nivel: number; avaliada_em: string }>;
  autorizacoes: Array<{
    nome: string;
    escopo: string | null;
    vence_em: string | null;
    status: string;
  }>;
  disponibilidade: Array<{ inicio: string; fim: string; status: string }>;
  base_localizacao: string;
  experiencia_senioridade: string;
  alocacoes: Array<{ operacao: string; inicio: string; fim: string; status: string }>;
  custos_incrementais: Array<{
    moeda: string;
    custo_hora_centavos: number;
    custo_viagem_centavos: number;
    vigencia_inicio: string;
  }>;
  capacitacoes_agendadas: Array<{
    treinamento: string;
    inicio: string;
    fim: string;
    status: string;
  }>;
  restricoes_operacionais: Array<{
    restricao: string;
    escopo: string | null;
    inicio: string | null;
    fim: string | null;
  }>;
  prontidao: Record<string, unknown>;
  updated_at: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiUrl()}${path}`, { cache: "no-store", credentials: "include" });
  if (!response.ok) {
    throw new ApiError(response.status, `API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

async function mutationRequest<T>(
  path: string,
  method: "POST" | "PATCH" | "DELETE",
  payload?: Record<string, unknown>,
): Promise<T> {
  const response = await fetch(`${apiUrl()}${path}`, {
    method,
    headers: {
      ...(payload ? { "Content-Type": "application/json" } : {}),
      "X-TWR-Actor": "next-local-user",
      "X-TWR-Role": "planner",
    },
    body: payload ? JSON.stringify(payload) : undefined,
    cache: "no-store",
    credentials: "include",
  });
  if (!response.ok) {
    let message = `API request failed: ${response.status}`;
    const body = (await response.json().catch(() => null)) as
      | { detail?: string | { message?: string } }
      | null;
    if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (body?.detail?.message) {
      message = body.detail.message;
    }
    throw new ApiError(response.status, message);
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}

async function writeRequest<T>(path: string, payload: Record<string, unknown>): Promise<T> {
  return mutationRequest<T>(path, "POST", payload);
}

async function adminWriteRequest<T>(path: string, payload: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${apiUrl()}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-TWR-Actor": "next-local-admin",
      "X-TWR-Role": "admin",
    },
    body: JSON.stringify(payload),
    cache: "no-store",
    credentials: "include",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string | { message?: string } }
      | null;
    const message =
      typeof body?.detail === "string"
        ? body.detail
        : body?.detail?.message ?? `API request failed: ${response.status}`;
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as T;
}

export function listEmployees(parameters: URLSearchParams): Promise<PaginatedEmployees> {
  return request<PaginatedEmployees>(`/employees?${parameters.toString()}`);
}

export function getEmployeeProfile(employeeId: string): Promise<EmployeeProfile> {
  return request<EmployeeProfile>(`/employees/${encodeURIComponent(employeeId)}/profile`);
}

export function listQualifications(): Promise<PaginatedQualifications> {
  return request<PaginatedQualifications>("/qualifications?page=1&page_size=100");
}

export function listRoles(): Promise<PaginatedRoles> {
  return request<PaginatedRoles>("/roles?page=1&page_size=100");
}

export function createQualification(payload: {
  code: string;
  name: string;
  category: string;
  validity_days?: number;
}): Promise<QualificationReference> {
  return writeRequest<QualificationReference>("/qualifications", payload);
}

export function createEmployee(payload: {
  employee_number: string;
  name: string;
  canonical_role_id: string;
  base_location: string;
  seniority_level: string;
}): Promise<EmployeeWriteResult> {
  return writeRequest<EmployeeWriteResult>("/employees", payload);
}

export function listOperations(): Promise<PaginatedOperations> {
  return request<PaginatedOperations>("/operations?page=1&page_size=100");
}

export function getOperation(operationId: string): Promise<OperationDetail> {
  return request<OperationDetail>(`/operations/${encodeURIComponent(operationId)}`);
}

export function createOperation(payload: {
  code: string;
  name: string;
  client_name: string;
  base_location: string;
  starts_at: string;
  ends_at: string;
  mobilization_deadline?: string;
  budget_cents?: number;
  demands: Array<{
    role_id: string;
    quantity: number;
    shift_code: string;
  }>;
  requirements: never[];
}): Promise<{ id: string; code: string; updated_at: string }> {
  return writeRequest<{ id: string; code: string; updated_at: string }>("/operations", payload);
}

export function getLatestEligibility(operationId: string): Promise<EligibilityRun> {
  return request<EligibilityRun>(
    `/operations/${encodeURIComponent(operationId)}/eligibility/latest`,
  );
}

export function runEligibility(operationId: string): Promise<EligibilityRun> {
  return writeRequest<EligibilityRun>(
    `/operations/${encodeURIComponent(operationId)}/eligibility/run`,
    {},
  );
}

export function optimizeOperation(
  operationId: string,
  objective: OptimizationScenario["objective"],
): Promise<OptimizationScenario> {
  return writeRequest<OptimizationScenario>(
    `/operations/${encodeURIComponent(operationId)}/optimize`,
    { objective },
  );
}

export function listScenarios(operationId: string): Promise<ScenarioCollection> {
  return request<ScenarioCollection>(
    `/operations/${encodeURIComponent(operationId)}/scenarios`,
  );
}

export function getOperationTrainingPlan(
  operationId: string,
  decisionRunId?: string,
): Promise<OperationTrainingPlanView> {
  const query = decisionRunId
    ? `?decision_run_id=${encodeURIComponent(decisionRunId)}`
    : "";
  return request<OperationTrainingPlanView>(
    `/operations/${encodeURIComponent(operationId)}/training-plan${query}`,
  );
}

export function planTrainingInvestment(payload: {
  horizon: string;
  budget_cents: number;
  weights: InvestmentPlanView["weights"];
}): Promise<InvestmentPlanView> {
  return writeRequest<InvestmentPlanView>("/training/investment-plan", payload);
}

export function getFragility(
  horizonDays = 180,
  operationIds: string[] = [],
): Promise<FragilityReportView> {
  const parameters = new URLSearchParams({ horizon_days: String(horizonDays) });
  for (const operationId of operationIds) parameters.append("operation_ids", operationId);
  return request<FragilityReportView>(`/risk/fragility?${parameters.toString()}`);
}

export function listDecisionRuns(): Promise<ScenarioCollection> {
  return request<ScenarioCollection>("/decision-runs");
}

export function getDecisionRun(decisionRunId: string): Promise<DecisionRunTimelineView> {
  return request<DecisionRunTimelineView>(
    `/decision-runs/${encodeURIComponent(decisionRunId)}`,
  );
}

export function selectScenario(decisionRunId: string, note: string): Promise<SelectedDecisionView> {
  return writeRequest<SelectedDecisionView>(
    `/decision-runs/${encodeURIComponent(decisionRunId)}/select`,
    { note },
  );
}

export function recordDecisionOutcome(
  decisionRunId: string,
  payload: {
    actual_cost_cents: number;
    actual_ready_at: string;
    substitutions: Array<{
      original_assignment_id: string;
      actual_employee_id: string;
    }>;
    performed_training_action_ids: string[];
    calibration_observations?: CalibrationObservation[];
  },
): Promise<DecisionOutcomeView> {
  return writeRequest<DecisionOutcomeView>(
    `/decision-runs/${encodeURIComponent(decisionRunId)}/outcome`,
    payload,
  );
}

export function createCalibrationSuggestion(payload: {
  parameter: CalibrationParameterName;
  category: string;
}): Promise<CalibrationSuggestionView> {
  return writeRequest<CalibrationSuggestionView>("/calibration/suggestions", payload);
}

export function applyCalibrationSuggestion(
  suggestionId: string,
): Promise<CalibrationParameterView> {
  return writeRequest<CalibrationParameterView>(
    `/calibration/suggestions/${encodeURIComponent(suggestionId)}/apply`,
    { confirmed: true },
  );
}

export function getDataQualityOverview(): Promise<DataQualityOverview> {
  return request<DataQualityOverview>("/data-quality/overview");
}

export function previewImport(payload: {
  contract: ImportContractName;
  filename: string;
  content_base64: string;
  mapping?: Record<string, string>;
}): Promise<ImportPreviewView> {
  return adminWriteRequest<ImportPreviewView>("/imports/preview", payload);
}

export function commitImport(
  previewToken: string,
  confirmed: boolean,
): Promise<ImportCommitSummary> {
  return adminWriteRequest<ImportCommitSummary>("/imports/commit", {
    preview_token: previewToken,
    confirmed,
  });
}

export async function downloadExport(
  type: "employees" | "readiness" | "gaps" | "scenarios" | "training" | "risk" | "decision_runs",
  format: "csv" | "xlsx",
): Promise<{ blob: Blob; filename: string }> {
  const response = await fetch(`${apiUrl()}/exports/${type}?format=${format}`, {
    headers: { "X-TWR-Actor": "next-local-viewer", "X-TWR-Role": "viewer" },
    credentials: "include",
  });
  if (!response.ok) throw new ApiError(response.status, `API request failed: ${response.status}`);
  const disposition = response.headers.get("content-disposition") ?? "";
  const filename = disposition.match(/filename="([^"]+)"/)?.[1] ?? `twr-${type}.${format}`;
  return { blob: await response.blob(), filename };
}

export function getDashboardOverview(horizonDays = 180): Promise<DashboardOverviewView> {
  return request<DashboardOverviewView>(`/dashboard/overview?horizon_days=${horizonDays}`);
}

export async function loginSession(payload: { username: string; password: string }): Promise<UserSession> {
  const response = await fetch(`${apiUrl()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
    credentials: "include",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { detail?: string | { message?: string } } | null;
    const message = typeof body?.detail === "string" ? body.detail : body?.detail?.message ?? "Não foi possível iniciar a sessão.";
    throw new ApiError(response.status, message);
  }
  return (await response.json()) as UserSession;
}

export async function getCurrentSession(): Promise<UserSession | null> {
  const response = await fetch(`${apiUrl()}/auth/me`, { cache: "no-store", credentials: "include" });
  if (response.status === 401) return null;
  if (!response.ok) throw new ApiError(response.status, "Não foi possível verificar a sessão.");
  return (await response.json()) as UserSession;
}

export async function logoutSession(): Promise<void> {
  const response = await fetch(`${apiUrl()}/auth/logout`, { method: "POST", cache: "no-store", credentials: "include" });
  if (!response.ok) throw new ApiError(response.status, "Não foi possível encerrar a sessão.");
}

export function listMcpConnections(): Promise<McpConnection[]> {
  return request<McpConnection[]>("/mcp-connections");
}

export function createMcpConnection(payload: McpConnectionInput): Promise<McpConnection> {
  return mutationRequest<McpConnection>("/mcp-connections", "POST", payload);
}

export function updateMcpConnection(
  connectionId: string,
  payload: Partial<McpConnectionInput>,
): Promise<McpConnection> {
  return mutationRequest<McpConnection>(
    `/mcp-connections/${encodeURIComponent(connectionId)}`,
    "PATCH",
    payload,
  );
}

export function validateMcpConnection(connectionId: string): Promise<McpConnectionValidation> {
  return mutationRequest<McpConnectionValidation>(
    `/mcp-connections/${encodeURIComponent(connectionId)}/validate`,
    "POST",
  );
}

export function deleteMcpConnection(connectionId: string): Promise<void> {
  return mutationRequest<void>(
    `/mcp-connections/${encodeURIComponent(connectionId)}`,
    "DELETE",
  );
}

export function getMcpToolCatalog(): Promise<McpTool[]> {
  return request<McpTool[]>("/mcp-connections/catalog");
}
