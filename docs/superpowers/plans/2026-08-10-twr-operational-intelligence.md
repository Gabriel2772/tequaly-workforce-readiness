# TWR Operational Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Acrescentar treinamento operacional e estratégico, fragilidade, seleção humana, outcome e sugestões auditáveis de recalibração.

**Architecture:** Novos serviços consomem os resultados estruturados do núcleo; não recalculam elegibilidade com regras próprias. A decisão selecionada, o resultado real e toda sugestão permanecem vinculados ao `DecisionRun` que os originou.

**Tech Stack:** A mesma stack do núcleo, com OR-Tools para investimento preventivo, SQLAlchemy/PostgreSQL para histórico e React para heatmaps e timelines acessíveis.

## Global Constraints

- Não aplicar sugestão de recalibração automaticamente.
- Não usar ML para risco, treinamento ou recalibração.
- Pesos de operações confirmadas/prováveis/hipotéticas são visíveis e configuráveis.
- Toda seleção ou alteração persistente produz audit event.
- Fragilidade e risco são explicáveis por regras.

---

### Task 1: Operational training plan

**Files:**
- Create: `backend/app/training/types.py`, `operation_service.py`, `router.py`
- Test: `backend/tests/unit/training/test_operation_plan.py`, `backend/tests/integration/training/test_api.py`
- Create: `frontend/features/training/operation-training-plan.tsx`

**Interfaces:**
- Produces: `TrainingPlanningService.for_operation(operation_id, decision_run_id | None) -> OperationTrainingPlan`.
- Produces: `GET /operations/{id}/training-plan`.

- [ ] **Step 1: Write gap conversion tests**

```python
def test_trainable_gap_becomes_scheduled_action():
    plan = service.for_operation(operation_id)
    assert plan.actions[0].completes_at <= operation.mobilization_deadline
```

- [ ] **Step 2: Implement action construction**

Choose an available session that grants or renews the missing qualification, ends before the deadline and minimizes completion time then cost.

- [ ] **Step 3: Persist decision training actions**

When a scenario is selected, copy the chosen actions into `decision_training_actions` with source session and expected values.

- [ ] **Step 4: Implement operation training UI**

Show person, gap, course, date, cost, impact and blocking reason when no session exists.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add operation training plans"
```

### Task 2: Strategic training investment optimizer

**Files:**
- Create: `backend/app/training/investment_model.py`, `investment_service.py`
- Test: `backend/tests/unit/training/test_investment_model.py`, `backend/tests/integration/training/test_investment_api.py`
- Create: `frontend/features/training/investment-planner.tsx`

**Interfaces:**
- Produces: `plan_investment(horizon, budget_cents, weights) -> InvestmentPlan`.
- Produces: `POST /training/investment-plan`.

- [ ] **Step 1: Write coverage-gain and budget tests**

Assert total cost never exceeds budget and a training that unlocks two weighted positions outranks one that unlocks one equal-cost position.

- [ ] **Step 2: Implement deterministic opportunity generation**

Generate only employee/training pairs that close a known gap for at least one future demand and finish inside the horizon.

- [ ] **Step 3: Implement CP-SAT objective**

Maximize integer-scaled `CoverageGain`; tie-break by lower cost, earlier availability and fewer actions.

- [ ] **Step 4: Add strategic planner UI**

Expose horizon, budget, visible weights, selected people, cost, unlocked positions and benefited operations.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: optimize preventive training investment"
```

### Task 3: Operational fragility engine

**Files:**
- Create: `backend/app/fragility/types.py`, `rules.py`, `service.py`, `router.py`
- Test: `backend/tests/unit/fragility/test_metrics.py`, `test_risk_rules.py`
- Create: `frontend/features/risk/fragility-heatmap.tsx`, `fragility-detail.tsx`, `frontend/app/risco-e-cobertura/page.tsx`

**Interfaces:**
- Produces: `FragilityService.calculate(horizon_days, operation_ids) -> FragilityReport`.
- Produces: `GET /risk/fragility`.

- [ ] **Step 1: Write formula tests**

```python
def test_single_point_of_failure():
    metric = calculate(required_count=2, eligible_count=2)
    assert metric.redundancy == 0
    assert metric.single_point_of_failure is True
```

- [ ] **Step 2: Implement metrics and explanation rules**

Calculate coverage, redundancy, expiries, allocations, trainable count and missing sessions. Risk output includes threshold, observed value and reason codes.

- [ ] **Step 3: Implement server-side aggregation**

Aggregate by role and requirement without transferring employee-level datasets until drill-down is requested.

- [ ] **Step 4: Implement accessible heatmap**

Every cell includes numeric/text status, tooltip and keyboard-accessible detail; color is supplementary.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add explainable workforce fragility"
```

### Task 4: Scenario selection and decision timeline

**Files:**
- Create: `backend/app/decisions/schemas.py`, `router.py`, `selection_service.py`
- Test: `backend/tests/integration/decisions/test_selection.py`
- Create: `frontend/features/decisions/decision-timeline.tsx`, `scenario-selection.tsx`, `frontend/app/auditoria/page.tsx`

**Interfaces:**
- Produces: `select_scenario(decision_run_id, actor_id, note) -> SelectedDecision`.
- Produces: `POST /decision-runs/{id}/select`, `GET /decision-runs`, `GET /decision-runs/{id}`.

- [ ] **Step 1: Write authorization and audit tests**

Viewer selection returns 403; planner selection stores actor, timestamp, optional note and audit event.

- [ ] **Step 2: Implement idempotent selection command**

Repeat selection of the same run without changes is safe; replacing a prior selection creates an explicit supersession event.

- [ ] **Step 3: Build decision timeline DTO**

Combine execution, input version, solution, selection, changes and training without reading LLM messages.

- [ ] **Step 4: Add confirmation UI and timeline**

Display predicted metrics before confirmation and record the human note.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add auditable scenario selection"
```

### Task 5: Decision outcome comparison

**Files:**
- Create: `backend/app/decisions/outcome_service.py`
- Test: `backend/tests/unit/decisions/test_outcome.py`, `backend/tests/integration/decisions/test_outcome_api.py`
- Create: `frontend/features/decisions/outcome-form.tsx`, `outcome-comparison.tsx`

**Interfaces:**
- Produces: `record_outcome(command, actor_id) -> DecisionOutcomeView`.
- Produces: `POST /decision-runs/{id}/outcome`.

- [ ] **Step 1: Write comparison tests**

Assert cost variance, readiness delay/advance, substitutions and performed-versus-planned training are calculated from stored decision values.

- [ ] **Step 2: Implement validated outcome command**

Money uses integer cents; times are timezone-aware; substitutions reference valid employees and preserve the original assignment.

- [ ] **Step 3: Persist outcome and audit event atomically**

No partial outcome is visible if audit persistence fails.

- [ ] **Step 4: Implement form and comparison UI**

Show predicted, actual, absolute difference and percentage where meaningful.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: compare decision outcomes"
```

### Task 6: Calibration suggestions with human approval

**Files:**
- Create: `backend/app/calibration/types.py`, `statistics.py`, `service.py`, `router.py`
- Test: `backend/tests/unit/calibration/test_statistics.py`, `backend/tests/integration/calibration/test_approval.py`
- Create: `frontend/features/decisions/calibration-suggestion.tsx`

**Interfaces:**
- Produces: `suggest(parameter, category) -> CalibrationSuggestion`.
- Produces: `apply_suggestion(suggestion_id, actor_id, confirmed) -> CalibrationParameter`.
- Produces: `POST /calibration/suggestions/{id}/apply`.

- [ ] **Step 1: Write robust-statistics tests**

Use medians for skewed samples, require a minimum sample count of five and include sample size plus confidence basis.

- [ ] **Step 2: Implement suggestion generation**

Supported initial parameters: training cost by category, mobilization lead time and travel cost by base pair.

- [ ] **Step 3: Enforce confirmation**

`confirmed=false` never changes parameters; successful application creates a versioned parameter and audit event.

- [ ] **Step 4: Implement suggestion UI**

Show current/proposed value, sample, rationale and explicit apply confirmation.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add human-approved recalibration"
```

### Task 7: Overview dashboard

**Files:**
- Create: `backend/app/dashboard/service.py`, `router.py`, `schemas.py`
- Test: `backend/tests/unit/dashboard/test_service.py`, `backend/tests/integration/dashboard/test_api.py`
- Create: `frontend/app/page.tsx`, `frontend/features/dashboard/readiness-summary.tsx`, `operations-list.tsx`, `risk-alerts.tsx`
- Test: `frontend/features/dashboard/readiness-summary.test.tsx`

**Interfaces:**
- Produces: `DashboardService.get_overview(horizon_days) -> DashboardOverview`.
- Produces: `GET /dashboard/overview`.

- [ ] **Step 1: Write metric aggregation tests**

Assert active collaborators, readiness, expiring qualifications, risky operations, uncovered positions and planned training cost match source services.

- [ ] **Step 2: Implement composed read service**

Reuse workforce, fragility and operation query services; do not duplicate formulas or scan all employee details in Python.

- [ ] **Step 3: Implement overview page**

Add compact KPI cards, future operations, bottleneck heatmap, expiries and fragility alerts with drill-down links.

- [ ] **Step 4: Add loading, empty and error states**

Ensure the page remains useful when no operations exist and exposes retry for failed aggregates.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add workforce readiness dashboard"
```

### Task 8: Operational intelligence E2E and documentation gate

**Files:**
- Create: `frontend/e2e/operational-intelligence.spec.ts`
- Create: `docs/training.md`, `docs/fragility.md`, `docs/decision-audit.md`, `docs/test-results/operational-intelligence.md`
- Modify: `docs/demo-script.md`, `docs/implementation-decisions.md`

**Interfaces:**
- Produces: verified operation-to-outcome demonstration.

- [ ] **Step 1: Add seeded E2E scenario**

Select a scenario, inspect training, open fragility, record a simulated outcome and view a recalibration suggestion.

- [ ] **Step 2: Run full backend/frontend checks**

Expected: all prior core tests plus new suites pass.

- [ ] **Step 3: Verify migration and seed from zero**

Expected: no duplicate decision/training/calibration demo data after a second seed.

- [ ] **Step 4: Record evidence and limitations**

Include exact commands, durations, pass counts and parameters not yet supported.

- [ ] **Step 5: Commit**

```text
git commit -m "docs: complete operational intelligence delivery"
```
