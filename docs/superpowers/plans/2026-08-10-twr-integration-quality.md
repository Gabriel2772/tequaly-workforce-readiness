# TWR Integration and Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finalizar autenticação, importação/exportação, E2E, acessibilidade, desempenho e documentação verificável do MVP.

**Architecture:** Importação usa contratos canônicos e um pipeline de preview/validação/commit; autenticação local protege os mesmos Application Services usados por API, IA e MCP. A entrega termina com ambiente limpo, seed, testes e evidência visual real.

**Tech Stack:** FastAPI, SQLAlchemy/PostgreSQL, openpyxl, Python CSV, Next.js, Playwright, axe-core e ferramentas de benchmark locais.

## Global Constraints

- PostgreSQL continua sendo a fonte de verdade após importação.
- Upload não cria entidade `Evidence` e arquivos temporários não viram acervo documental.
- Commit de importação é transacional e auditado.
- Exportações não incluem secrets, tokens ou configuração da IA.
- Papéis mínimos: `ADMIN`, `PLANNER`, `VIEWER`.
- Nenhum teste ou integração é declarado funcional sem execução real.

---

### Task 1: Local authentication and authorization

**Files:**
- Create: `backend/app/auth/passwords.py`, `tokens.py`, `service.py`, `dependencies.py`, `router.py`
- Create: `backend/migrations/versions/0004_auth.py`
- Test: `backend/tests/unit/auth/test_passwords.py`, `backend/tests/integration/auth/test_permissions.py`
- Create: `frontend/app/login/page.tsx`, `frontend/lib/session.ts`

**Interfaces:**
- Produces: login/logout/current-user endpoints and `require_role(*roles)` dependency.
- Produces: authenticated browser session with secure cookie.

- [ ] **Step 1: Write role matrix tests**

Assert viewer reads but cannot mutate; planner manages operations/decisions; admin manages reference data and calibration.

- [ ] **Step 2: Implement password hashing and session tokens**

Use a memory-hard password hash, short-lived signed sessions, secure cookie flags and server-side role lookup.

- [ ] **Step 3: Apply authorization at service/API boundaries**

Protect all writes, not only buttons. Existing audit events receive the authenticated actor.

- [ ] **Step 4: Implement login UI and E2E roles**

Test successful login, failure, viewer restriction and logout.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add MVP authentication and roles"
```

### Task 2: Canonical import contracts and sample files

**Files:**
- Create: `backend/app/imports/contracts.py`, `normalization.py`, `types.py`
- Create: `scripts/generate_samples.py`
- Create: `samples/employees.csv`, `samples/qualifications.csv`, `samples/operations.xlsx`, `samples/training_catalog.xlsx`
- Test: `backend/tests/unit/imports/test_contracts.py`, `test_normalization.py`

**Interfaces:**
- Produces: `ImportContract`, `ColumnMapping`, `NormalizedRow`, sample generators.

- [ ] **Step 1: Write required-field and alias tests**

Unknown/duplicate column mappings fail; known role aliases normalize to canonical role IDs; dates use explicit locale rules.

- [ ] **Step 2: Implement four versioned contracts**

Define employees, employee qualifications, operations/demands and training catalog with stable field names and contract version.

- [ ] **Step 3: Generate representative samples**

Include valid rows plus separate intentionally invalid sample files for demo/testing.

- [ ] **Step 4: Round-trip samples through parsers**

Expected: generated valid files normalize without errors and preserve Unicode.

- [ ] **Step 5: Commit**

```text
git commit -m "feat: define import contracts and samples"
```

### Task 3: Preview and dry-run pipeline

**Files:**
- Create: `backend/app/imports/parsers.py`, `validators.py`, `preview_service.py`, `router.py`
- Test: `backend/tests/unit/imports/test_parsers.py`, `test_validators.py`, `backend/tests/integration/imports/test_preview_api.py`
- Create: `frontend/features/imports/import-wizard.tsx`, `mapping-step.tsx`, `validation-report.tsx`

**Interfaces:**
- Produces: `preview_import(file, contract, mapping, actor) -> ImportPreview`.
- Produces: `POST /imports/preview`.

- [ ] **Step 1: Write mandatory dry-run tests**

Cover invalid rows, duplicates, invalid dates, unknown qualifications, unknown roles and missing required fields.

- [ ] **Step 2: Implement safe CSV/XLSX parsing**

Apply file size/row limits, reject macros and unsupported formats, normalize headers and avoid formula evaluation.

- [ ] **Step 3: Implement row-level validation report**

Return counts, row number, stable error code, field and safe message. Do not persist domain data.

- [ ] **Step 4: Implement preview/mapping UI**

Show sample values, mapping choices and downloadable error report before confirmation.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: add import preview and dry-run"
```

### Task 4: Transactional import commit

**Files:**
- Create: `backend/app/imports/commit_service.py`, `staging.py`
- Create: `backend/migrations/versions/0005_import_batches.py`
- Test: `backend/tests/integration/imports/test_commit.py`, `test_rollback.py`

**Interfaces:**
- Produces: `commit_import(preview_token, actor, confirmed) -> ImportCommitSummary`.
- Produces: `POST /imports/commit`.

- [ ] **Step 1: Write rollback and stale-preview tests**

One invalid persistence operation rolls back the whole batch; changed/expired preview tokens cannot commit.

- [ ] **Step 2: Persist import batch metadata**

Store contract version, source hash, mapping, counts, actor and status. Do not retain the uploaded document as evidence.

- [ ] **Step 3: Implement transaction and idempotency**

Use validated normalized rows, natural-key duplicate policy and a single domain transaction plus audit event.

- [ ] **Step 4: Benchmark 3.000 employee dry-run/commit**

Dry-run target: 30 seconds. Record commit time separately and verify row counts/index use.

- [ ] **Step 5: Verify and commit**

```text
git commit -m "feat: commit imports transactionally"
```

### Task 5: Filtered exports

**Files:**
- Create: `backend/app/exports/types.py`, `service.py`, `router.py`
- Test: `backend/tests/unit/exports/test_service.py`, `backend/tests/integration/exports/test_api.py`
- Create: `frontend/components/export-button.tsx`

**Interfaces:**
- Produces: `export(type, filters, format, actor) -> StreamingExport`.
- Produces: `GET /exports/{type}` for CSV/XLSX.

- [ ] **Step 1: Write export coverage and secret tests**

Cover employees, readiness, gaps, scenarios, training, risk and decision runs. Assert no env/config/token fields occur.

- [ ] **Step 2: Implement streaming CSV/XLSX writers**

Apply the same filters and authorization as list APIs and escape spreadsheet formulas in user-controlled text.

- [ ] **Step 3: Add metadata sheet/header**

Include export time, actor, filters, contract version and timezone without secrets.

- [ ] **Step 4: Add export controls and smoke tests**

Download a filtered file and reparse it in a test to verify headers and row count.

- [ ] **Step 5: Commit**

```text
git commit -m "feat: export workforce planning data"
```

### Task 6: Full critical-path E2E

**Files:**
- Create: `frontend/e2e/full-demo.spec.ts`, `frontend/e2e/import.spec.ts`, `frontend/e2e/accessibility.spec.ts`
- Create: `backend/tests/e2e/test_mcp_equivalence.py`

**Interfaces:**
- Produces: automated version of the 20-step demo flow.

- [ ] **Step 1: Implement import-to-decision E2E**

Login, import sample, open employee, create operation, run eligibility, optimize, compare and select.

- [ ] **Step 2: Extend through intelligence and outcome**

Inspect training/fragility, ask fake-provider copilot, compare through MCP, record outcome and view recalibration.

- [ ] **Step 3: Add infeasible and no-LLM E2E**

Assert blockers are explicit and core buttons work with the provider disabled.

- [ ] **Step 4: Remove test flakiness**

Use seeded IDs and observable completion states; do not add arbitrary sleeps.

- [ ] **Step 5: Commit**

```text
git commit -m "test: cover complete TWR demonstration flow"
```

### Task 7: Accessibility, performance and security hardening

**Files:**
- Create: `scripts/benchmark.py`, `scripts/security_smoke.py`, `docs/performance.md`, `docs/security.md`
- Modify: frontend components identified by axe/keyboard tests
- Test: `backend/tests/performance/test_api_targets.py`, `frontend/e2e/accessibility.spec.ts`

**Interfaces:**
- Produces: reproducible benchmark and security smoke reports.

- [ ] **Step 1: Run keyboard and axe checks**

Cover navigation, tables, dialogs, scenario tabs, heatmap, copilot and confirmation. Fix critical/serious findings.

- [ ] **Step 2: Run 3.000-person benchmark**

Targets: list/profile API p95 ≤800 ms, eligibility ≤15 s, each solver ≤30 s and dry-run ≤30 s.

- [ ] **Step 3: Profile and fix measured bottlenecks**

Use query plans/counts and candidate-pool metrics. Add indexes or query changes only with before/after evidence.

- [ ] **Step 4: Run security smoke**

Check CORS, auth matrix, secret redaction, upload limits, formula injection, MCP auth and AI confirmation replay.

- [ ] **Step 5: Commit**

```text
git commit -m "perf: harden TWR for production-scale PoC"
```

### Task 8: Final documentation, screenshots and verification

**Files:**
- Create: `docs/demo-script.md`, `docs/future-opportunities.md`, `docs/limitations.md`, `docs/test-results/final.md`
- Create: `docs/screenshots/*.png`
- Modify: `README.md`, `docs/architecture.md`, `docs/data-model.md`, `docs/optimization.md`, `docs/ai-tools.md`, `docs/mcp.md`, `docs/test-plan.md`
- Create: `scripts/verify.py`

**Interfaces:**
- Produces: final deliverable set and one verification entrypoint.

- [ ] **Step 1: Implement verification script**

Run format/lint/typecheck, backend unit/integration, frontend component/E2E, production build, clean migration, double seed, API smoke, solver and MCP checks.

- [ ] **Step 2: Execute from a clean database**

Record exact environment, dependency locks, commands, pass/fail counts and durations.

- [ ] **Step 3: Capture real screenshots**

Capture dashboard, employee profile, operation, eligibility drill-down, scenario comparison, training, fragility, audit and copilot. Do not fabricate screens.

- [ ] **Step 4: Classify every module**

Use `IMPLEMENTADO`, `TESTADO`, `PARCIAL`, `NÃO IMPLEMENTADO` or `BLOQUEADO EXTERNAMENTE`, backed by test evidence.

- [ ] **Step 5: Final diff review and commit**

```text
git commit -m "docs: finalize TWR MVP delivery"
```

