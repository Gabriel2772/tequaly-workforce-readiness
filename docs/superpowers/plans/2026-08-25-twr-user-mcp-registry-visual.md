# TWR User MCP Registry and Visual Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the abandoned OAuth/copilot work with authenticated per-user MCP configuration management and a polished icon-based navigation shell.

**Architecture:** The FastAPI application stores non-secret MCP connection metadata owned by the existing TWR session user; it never proxies arbitrary MCP traffic or authenticates Claude/ChatGPT. The existing deterministic read-tool registry and local `stdio` MCP server move out of `app.ai`, while Next.js provides CRUD, validation, copy guidance, and the redesigned responsive shell.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, pytest, Ruff, mypy, Next.js 16, React 19, TypeScript 6, Vitest, Testing Library, Playwright, plain CSS and inline SVG.

**Spec:** `docs/superpowers/specs/2026-08-25-twr-user-mcp-registry-visual-design.md`

## Global Constraints

- There is no chat, conversation history, model execution, OAuth, OIDC, PKCE, consent, external-provider login, or LLM API key in the final tree.
- A connection stores only non-secret metadata; reject URL userinfo, fragments, embedded credentials, and secret/header fields.
- Every connection operation derives ownership from `require_session_actor`; never accept `user_id` from the client.
- Remote endpoints require HTTPS, except HTTP localhost when `Settings.environment == "development"`.
- Validation is structural only and performs no network request to a user-supplied URL.
- The existing MCP `stdio` server and its five deterministic read-only tools remain functional.
- Preserve `backend/.local/` and every unrelated user change; do not add the runtime directory to Git.
- The interrupted OAuth commits remain in history, but their code, migration objects, settings, dependencies, tests, and docs must be absent from the final tree.
- Use `apply_patch` for manual edits and deletions; do not use a destructive reset or checkout.
- Run focused RED/GREEN evidence for every task before the full proportional verification.

---

### Task 1: Remove OAuth and Copilot While Preserving the MCP Tool Core

**Files:**
- Create: `backend/app/mcp/tools/__init__.py`
- Create: `backend/app/mcp/tools/types.py`
- Create: `backend/app/mcp/tools/registry.py`
- Create: `backend/app/mcp/tools/read_tools.py`
- Modify: `backend/app/mcp_server.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `backend/.env.example`
- Modify: `.env.example`
- Modify: `backend/tests/test_config.py`
- Modify: `backend/tests/test_health.py`
- Create: `backend/tests/integration/mcp/test_surface.py`
- Create: `backend/tests/integration/mcp/test_stdio.py`
- Create: `backend/tests/unit/mcp/tools/test_registry.py`
- Delete: `backend/app/ai/__init__.py`
- Delete: `backend/app/ai/orchestrator.py`
- Delete: `backend/app/ai/provider.py`
- Delete: `backend/app/ai/router.py`
- Delete: `backend/app/ai/schemas.py`
- Delete: `backend/app/ai/types.py`
- Delete: `backend/app/ai/tools/__init__.py`
- Delete: `backend/app/ai/tools/types.py`
- Delete: `backend/app/ai/tools/registry.py`
- Delete: `backend/app/ai/tools/read_tools.py`
- Delete: `backend/app/mcp/models.py`
- Delete: `backend/app/mcp/oauth_provider.py`
- Delete: `backend/app/mcp/repository.py`
- Delete: `backend/app/mcp/security.py`
- Delete: `backend/migrations/versions/0010_mcp_oauth.py`
- Delete: `backend/tests/integration/ai/test_chat_api.py`
- Delete: `backend/tests/integration/ai/test_mcp.py`
- Delete: `backend/tests/unit/ai/test_orchestrator.py`
- Delete: `backend/tests/unit/ai/test_provider.py`
- Delete: `backend/tests/unit/ai/tools/test_registry.py`
- Delete: `backend/tests/unit/mcp/test_oauth_provider.py`
- Delete: `backend/tests/unit/mcp/test_security.py`

**Interfaces:**
- Consumes: existing `ToolDefinition`, `ToolContext`, `ToolRegistry`, `build_read_registry()` behavior and `build_mcp_server()` public function.
- Produces: `app.mcp.tools.types.ToolContext`, `app.mcp.tools.registry.ToolRegistry`, `app.mcp.tools.read_tools.build_read_registry()`, a chat-free `create_app()`, and `GET /health -> {"status": "ok"}`.

- [ ] **Step 1: Write failing surface-removal and MCP-preservation tests**

Add a test that proves the removed HTTP surface is unavailable while the local MCP builder still exposes the read-only tool catalog:

```python
def test_copilot_and_oauth_surfaces_are_absent() -> None:
    client = _client()
    assert client.get("/copilot/health").status_code == 404
    assert client.get("/.well-known/oauth-authorization-server").status_code == 404
    assert client.post("/oauth/token").status_code == 404


def test_local_mcp_keeps_five_read_only_tools() -> None:
    registry = build_read_registry()
    assert [item["name"] for item in registry.catalog()] == [
        "get_readiness_overview",
        "get_operation",
        "get_employee_profile",
        "get_operational_fragility",
        "get_decision_run",
    ]
    assert {item["effect"] for item in registry.catalog()} == {"read"}
```

Update config and health expectations so LLM/OAuth fields are rejected as absent from `Settings.model_fields` and health equals `{"status": "ok"}`.

- [ ] **Step 2: Run the focused tests and record RED**

Run:

```powershell
cd backend
uv run pytest tests/integration/mcp/test_surface.py tests/test_config.py tests/test_health.py -q
```

Expected: FAIL because the copilot route/settings still exist and `app.mcp.tools` is not defined.

- [ ] **Step 3: Move only the deterministic tool core and remove AI/OAuth code**

Copy the existing tool types, registry and read definitions into `app/mcp/tools`, then change imports such as:

```python
from app.mcp.tools.read_tools import build_read_registry
from app.mcp.tools.types import ToolContext
```

Reduce `create_app()` to ordinary routers and remove `AIOrchestrator`, providers, `ai_router`, `app.state.ai_*`, and all OAuth wiring. Reduce settings to non-AI application/session values. Remove the `openai` dependency and refresh `uv.lock` with:

```powershell
cd backend
uv lock
```

Delete the listed obsolete files, including the interrupted uncommitted contents of `backend/app/mcp/repository.py`, using `apply_patch`. Preserve `backend/.local/`.

- [ ] **Step 4: Run focused and full backend verification**

Run:

```powershell
cd backend
uv run pytest tests/integration/mcp/test_surface.py tests/integration/mcp/test_stdio.py tests/unit/mcp/tools/test_registry.py tests/test_config.py tests/test_health.py -q
uv run pytest -q
uv run ruff check app tests
uv run mypy app
```

Expected: focused and full suites PASS; Ruff and mypy report no errors; PostgreSQL round-trip may be the single expected skip without `TWR_TEST_DATABASE_URL`.

- [ ] **Step 5: Commit**

```powershell
git add .env.example backend/app backend/tests backend/migrations/versions/0010_mcp_oauth.py backend/pyproject.toml backend/uv.lock backend/.env.example
git commit -m "refactor: remove OAuth and copilot runtime"
```

---

### Task 2: Add Authenticated Per-User MCP Connection CRUD

**Files:**
- Create: `backend/app/mcp_connections/__init__.py`
- Create: `backend/app/mcp_connections/models.py`
- Create: `backend/app/mcp_connections/schemas.py`
- Create: `backend/app/mcp_connections/repository.py`
- Create: `backend/app/mcp_connections/service.py`
- Create: `backend/app/mcp_connections/router.py`
- Create: `backend/migrations/versions/0010_user_mcp_connections.py`
- Modify: `backend/app/main.py`
- Modify: `backend/migrations/env.py`
- Modify: `backend/tests/integration/test_migrations.py`
- Create: `backend/tests/unit/mcp_connections/test_validation.py`
- Create: `backend/tests/integration/mcp_connections/test_api.py`

**Interfaces:**
- Consumes: `AuthenticatedActor`, `require_session_actor`, `request_session`, `AuditEvent`, `build_read_registry()` and `Settings.environment`.
- Produces: `McpConnectionCreate`, `McpConnectionUpdate`, `McpConnectionView`, `McpConnectionValidation`, `McpToolView`; repository methods `list_for_user`, `get_for_user`, `create`, `update`, `delete`; and authenticated `/mcp-connections` endpoints.

- [ ] **Step 1: Write failing validation tests**

Cover exact accepted and rejected forms:

```python
@pytest.mark.parametrize("url", [
    "https://mcp.example.com/mcp",
    "https://MCP.EXAMPLE.COM:443/mcp",
])
def test_remote_endpoint_accepts_https(url: str) -> None:
    assert validate_endpoint(url, environment="production").startswith("https://")


@pytest.mark.parametrize("url", [
    "http://mcp.example.com/mcp",
    "https://user:secret@mcp.example.com/mcp",
    "https://mcp.example.com/mcp#fragment",
    "file:///etc/passwd",
])
def test_remote_endpoint_rejects_unsafe_forms(url: str) -> None:
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint(url, environment="production")


def test_localhost_http_is_development_only() -> None:
    assert validate_endpoint("http://localhost:3001/mcp", environment="development")
    with pytest.raises(InvalidMcpEndpoint):
        validate_endpoint("http://localhost:3001/mcp", environment="production")
```

- [ ] **Step 2: Write failing API ownership tests**

Create two active `AppUser` records, log in with separate `TestClient` instances, then assert:

```python
created = alice.post("/mcp-connections", json=payload)
assert created.status_code == 201
connection_id = created.json()["id"]
assert [item["id"] for item in alice.get("/mcp-connections").json()] == [connection_id]
assert bob.get("/mcp-connections").json() == []
assert bob.patch(f"/mcp-connections/{connection_id}", json={"enabled": False}).status_code == 404
assert bob.delete(f"/mcp-connections/{connection_id}").status_code == 404
assert alice.post(f"/mcp-connections/{connection_id}/validate").json()["valid"] is True
```

Also test unauthenticated `401`, duplicate name/destination `409`, field limits `422`, no `user_id` input, catalog exactly five read-only tools, and no outbound network mock being called by validation.

- [ ] **Step 3: Run RED**

Run:

```powershell
cd backend
uv run pytest tests/unit/mcp_connections/test_validation.py tests/integration/mcp_connections/test_api.py -q
```

Expected: FAIL with missing `app.mcp_connections` modules and routes.

- [ ] **Step 4: Implement the model, migration, schemas and structural validator**

Define the model with these exact fields and constraints:

```python
class UserMcpConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_mcp_connections"
    __table_args__ = (
        UniqueConstraint("user_id", "client_type", "name", name="uq_user_mcp_connection_name"),
        Index("ix_user_mcp_connections_owner", "user_id", "updated_at"),
    )

    user_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("app_users.id"))
    name: Mapped[str] = mapped_column(String(120))
    client_type: Mapped[str] = mapped_column(String(20))
    endpoint_url: Mapped[str] = mapped_column(String(2048))
    transport: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(String(1000))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_validated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

Pydantic commands use `Literal["claude", "chatgpt"]`, `Literal["streamable_http", "sse"]`, `name` length 1–120, URL length 1–2048, notes length at most 1000, and `extra="forbid"`. Canonicalize scheme/host case and remove only the default HTTPS port; retain path and query because some legitimate MCP endpoints use query parameters, but reject keys matching `token`, `key`, `secret`, `password`, or `auth` case-insensitively.

Replace the deleted OAuth migration with revision `0010_user_mcp_connections`, down revision `0009_import_batches`, creating only `user_mcp_connections` and its indexes/constraints.

- [ ] **Step 5: Implement ownership, audit and routes**

All repository selectors include both ID and owner:

```python
def get_for_user(self, connection_id: UUID, user_id: UUID) -> UserMcpConnection | None:
    return self.session.scalar(
        select(UserMcpConnection).where(
            UserMcpConnection.id == connection_id,
            UserMcpConnection.user_id == user_id,
        )
    )
```

Resolve `UUID(actor.user_id)` server-side. `POST`, `PATCH`, validate and `DELETE` emit `AuditEvent` with event types `mcp_connection.created`, `.updated`, `.validated`, `.deleted`, aggregate type `mcp_connection`, aggregate ID only, `occurred_at=datetime.now(UTC)`, and `payload` limited to `client_type`, `transport`, and `enabled`. Commit on success, rollback on error, translate duplicate constraint to `409`, and use the same `404` for missing/foreign IDs.

Declare `GET /mcp-connections/catalog` before any `/{connection_id}` route so `catalog` is never parsed as a UUID. It maps `build_read_registry().catalog()` to five `McpToolView` records without executing tools.

- [ ] **Step 6: Run focused, migration and full backend verification**

Run:

```powershell
cd backend
uv run pytest tests/unit/mcp_connections/test_validation.py tests/integration/mcp_connections/test_api.py tests/integration/test_migrations.py -q
uv run pytest -q
uv run ruff check app tests
uv run mypy app
```

Expected: all pass, aside from the environment-gated PostgreSQL skip.

- [ ] **Step 7: Commit**

```powershell
git add backend/app/mcp_connections backend/app/main.py backend/migrations backend/tests
git commit -m "feat: add per-user MCP connection registry"
```

---

### Task 3: Build the MCP Connections Page and Client API

**Files:**
- Modify: `frontend/lib/api.ts`
- Create: `frontend/app/conexoes-mcp/page.tsx`
- Create: `frontend/features/mcp-connections/mcp-connections-page.tsx`
- Create: `frontend/features/mcp-connections/mcp-connections-page.test.tsx`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Consumes: backend `/mcp-connections` CRUD, validation and catalog endpoints from Task 2; existing cookie-aware request behavior.
- Produces: `McpConnection`, `McpConnectionInput`, `McpConnectionValidation`, `McpTool`; API functions `listMcpConnections`, `createMcpConnection`, `updateMcpConnection`, `validateMcpConnection`, `deleteMcpConnection`, `getMcpToolCatalog`; and `McpConnectionsPage`.

- [ ] **Step 1: Write failing component tests for the complete flow**

Mock only `@/lib/api` and cover empty, populated and error states:

```tsx
it("creates, validates, copies, toggles and deletes a connection", async () => {
  render(<McpConnectionsPage />);
  await user.click(await screen.findByRole("button", { name: "Cadastrar MCP" }));
  await user.type(screen.getByLabelText("Nome"), "MCP Planejamento");
  await user.selectOptions(screen.getByLabelText("Destino"), "claude");
  await user.type(screen.getByLabelText("Endpoint MCP"), "https://mcp.example.com/mcp");
  await user.click(screen.getByRole("button", { name: "Salvar conexão" }));
  expect(createMcpConnection).toHaveBeenCalledWith(expect.objectContaining({ client_type: "claude" }));
  await user.click(await screen.findByRole("button", { name: "Validar configuração" }));
  expect(await screen.findByText("Configuração válida")).not.toBeNull();
  await user.click(screen.getByRole("button", { name: "Copiar configuração" }));
  expect(navigator.clipboard.writeText).toHaveBeenCalled();
  await user.click(screen.getByRole("button", { name: "Desativar" }));
  await user.click(screen.getByRole("button", { name: "Excluir" }));
  await user.click(screen.getByRole("button", { name: "Confirmar exclusão" }));
  expect(deleteMcpConnection).toHaveBeenCalled();
});
```

Also assert search and destination/state filters, edit prefill, login-required message on `401`, structural validation errors, plan/admin guidance, and no chat-related copy or controls.

- [ ] **Step 2: Run RED**

Run:

```powershell
cd frontend
npm test -- features/mcp-connections/mcp-connections-page.test.tsx
```

Expected: FAIL because the page, types and API functions do not exist.

- [ ] **Step 3: Add typed API functions**

Use these public shapes:

```ts
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
```

Refactor the private request layer to support the exact mutation methods while retaining all existing callers:

```ts
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
    const body = await response.json().catch(() => null) as
      | { detail?: string | { message?: string } }
      | null;
    const message = typeof body?.detail === "string"
      ? body.detail
      : body?.detail?.message ?? `API request failed: ${response.status}`;
    throw new ApiError(response.status, message);
  }
  return response.status === 204 ? (undefined as T) : response.json() as Promise<T>;
}
```

Keep `writeRequest()` as a POST wrapper around `mutationRequest()` so existing features do not change. Implement list/catalog with `request`, create/validate with POST, update with PATCH, and delete with DELETE.

- [ ] **Step 4: Implement the responsive page behavior**

The client component loads connections and catalog in parallel, keeps form state local, and refreshes the affected item after each mutation. Generate a secret-free copied guide:

```ts
function connectionGuide(connection: McpConnection): string {
  return JSON.stringify({
    name: connection.name,
    url: connection.endpoint_url,
    transport: connection.transport === "streamable_http" ? "streamable-http" : "sse",
  }, null, 2);
}
```

Use a semantic dialog for create/edit and delete confirmation, `aria-live` for mutation results, visible labels, actual buttons for actions, and provider cards that explain external plan/admin restrictions. Do not include authentication fields, secret fields, chat input, conversation list, or provider login buttons.

- [ ] **Step 5: Run focused and frontend quality checks**

Run:

```powershell
cd frontend
npm test -- features/mcp-connections/mcp-connections-page.test.tsx
npm run typecheck
npm run lint
```

Expected: component tests, TypeScript and ESLint pass.

- [ ] **Step 6: Commit**

```powershell
git add frontend/lib/api.ts frontend/app/conexoes-mcp frontend/features/mcp-connections frontend/app/globals.css
git commit -m "feat: add MCP connections workspace"
```

---

### Task 4: Redesign the Sidebar, Icons and Product Mark

**Files:**
- Create: `frontend/components/navigation-icons.tsx`
- Create: `frontend/components/app-shell.test.tsx`
- Modify: `frontend/components/app-shell.tsx`
- Modify: `frontend/app/globals.css`
- Delete: `frontend/features/copilot/copilot-panel.tsx`
- Delete: `frontend/features/copilot/copilot-panel.test.tsx`
- Delete: `frontend/e2e/copilot.spec.ts`
- Modify: `frontend/lib/api.ts`

**Interfaces:**
- Consumes: `/conexoes-mcp` page from Task 3 and existing `SessionPanel`.
- Produces: `NavigationIcon`, `WorkforceMark`, an icon-based navigation list including `Conexões MCP`, and a shell with desktop compact/mobile states and no copilot UI.

- [ ] **Step 1: Write failing shell tests**

Mock `usePathname()` and assert exact navigation and accessibility:

```tsx
it("uses labeled SVG navigation and exposes MCP without a copilot launcher", () => {
  render(<AppShell><main>Conteúdo</main></AppShell>);
  expect(screen.getByRole("link", { name: "Conexões MCP" })).not.toBeNull();
  expect(screen.getByRole("navigation", { name: "Navegação principal" }).querySelectorAll("svg")).toHaveLength(10);
  expect(screen.queryByRole("button", { name: /copiloto/i })).toBeNull();
  expect(screen.getByLabelText("Tequaly Workforce Readiness").querySelector("svg")).not.toBeNull();
});
```

Add tests for `aria-current="page"` on nested routes and the mobile menu button's `aria-expanded` transition.

- [ ] **Step 2: Run RED**

Run:

```powershell
cd frontend
npm test -- components/app-shell.test.tsx
```

Expected: FAIL because markers are text, MCP navigation is absent, mobile control is absent and copilot is mounted.

- [ ] **Step 3: Implement the SVG icon system and shell**

Create a typed icon map rather than duplicating inline markup:

```tsx
export type NavigationIconName =
  | "overview" | "people" | "qualification" | "operations" | "planner"
  | "training" | "risk" | "audit" | "settings" | "mcp";

export function NavigationIcon({ name }: { name: NavigationIconName }) {
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor">{/* path set */}</svg>;
}
```

Every glyph uses a 24×24 viewBox, 1.8–2 px round stroke, no provider trademark, and a visually distinct silhouette. `WorkforceMark` uses an original geometric T/W plus three readiness nodes.

Add `{ href: "/conexoes-mcp", label: "Conexões MCP", icon: "mcp" }`. Use `title={item.label}` and an explicit accessible name. Add a mobile toggle that closes after navigation and a backdrop that does not trap desktop focus. Remove `CopilotPanel`, its API exports, tests, styles and E2E file.

- [ ] **Step 4: Polish responsive CSS**

Define one icon size and consistent interaction tokens:

```css
.nav-icon { width: 20px; height: 20px; flex: 0 0 20px; }
.app-sidebar nav a:focus-visible { outline: 3px solid var(--focus); outline-offset: 2px; }
.app-sidebar nav a[aria-current="page"]::before { content: ""; position: absolute; inset-block: 8px; inset-inline-start: 0; width: 3px; }
```

At the existing compact breakpoint keep icons and native titles while visually hiding labels. At the mobile breakpoint use an off-canvas sidebar, visible menu button, backdrop, body-safe scrolling and a main content width of 100%. Delete all `.copilot-*` rules.

- [ ] **Step 5: Run focused, full frontend and build checks**

Run with Node 22.12+:

```powershell
cd frontend
npm test -- components/app-shell.test.tsx
npm test
npm run typecheck
npm run lint
npm run build
```

Expected: all component suites and production build pass; no copilot import or text remains.

- [ ] **Step 6: Commit**

```powershell
git add frontend/components frontend/features/copilot frontend/e2e/copilot.spec.ts frontend/lib/api.ts frontend/app/globals.css
git commit -m "feat: redesign navigation and remove copilot UI"
```

---

### Task 5: Prove the User Flow, Refresh Documentation and Package the Handoff

**Files:**
- Create: `frontend/e2e/mcp-connections.spec.ts`
- Modify: `frontend/playwright.config.ts`
- Modify: `README.md`
- Modify: `ENTREGA_E_CONTINUIDADE_CLAUDE.md`
- Modify: `docs/demo-script.md`
- Modify: `docs/mcp.md`
- Modify: `docs/ai-tools.md`
- Modify: `docs/test-plan.md`
- Modify: `docs/test-results/ai-mcp.md`
- Modify: `docs/superpowers/specs/2026-08-25-twr-user-mcp-registry-visual-design.md`
- Create: `outputs/TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25.zip` (ignored delivery artifact)

**Interfaces:**
- Consumes: all backend and frontend behavior from Tasks 1–4.
- Produces: E2E proof, accurate operator/developer documentation and a clean downloadable continuation package.

- [ ] **Step 1: Write the failing E2E flow**

Define `loginAsPlanner(page)` in this E2E file using `/entrar`, `planner.demo` and `TequalyDemo!2026`, then cover the visible lifecycle:

```ts
test("user manages a Claude MCP connection", async ({ page }) => {
  await loginAsPlanner(page);
  await page.getByRole("link", { name: "Conexões MCP" }).click();
  await page.getByRole("button", { name: "Cadastrar MCP" }).click();
  await page.getByLabel("Nome").fill("MCP Planejamento");
  await page.getByLabel("Destino").selectOption("claude");
  await page.getByLabel("Endpoint MCP").fill("https://mcp.example.com/mcp");
  await page.getByRole("button", { name: "Salvar conexão" }).click();
  await page.getByRole("button", { name: "Validar configuração" }).click();
  await expect(page.getByText("Configuração válida")).toBeVisible();
  await page.getByRole("button", { name: "Desativar" }).click();
  await page.getByRole("button", { name: "Ativar" }).click();
  await page.getByRole("button", { name: "Excluir" }).click();
  await page.getByRole("button", { name: "Confirmar exclusão" }).click();
  await expect(page.getByText("Nenhuma conexão cadastrada")).toBeVisible();
});
```

Add a mobile-width navigation assertion and a direct API ownership test if the backend integration suite does not already exercise the second user through real cookies.

- [ ] **Step 2: Run E2E RED and then GREEN after fixture alignment**

Run:

```powershell
cd frontend
npm run e2e -- e2e/mcp-connections.spec.ts
```

Expected RED before final fixture/selector alignment; after using the actual seeded login and stable accessible names, PASS.

- [ ] **Step 3: Update operator and handoff documentation**

Document exactly:

- the app has no internal AI chat and needs no OpenAI/Anthropic API key;
- TWR login remains required for per-user MCP registration;
- saved records contain no secrets and validation performs no network request;
- Claude/ChatGPT setup happens externally and can depend on plan/admin rights;
- local MCP remains available through `uv run python -m app.mcp_server`;
- commands to run backend, frontend, focused tests, full tests and migrations;
- simulated workforce assumptions and remaining production-data integration work;
- current schema, routes, screenshots and final test counts.

Remove `TWR_LLM_ENABLED` from the Playwright backend environment because that setting no longer exists.

Mark the revised spec status `implemented` only after every verification below passes.

- [ ] **Step 4: Run the whole-product verification matrix**

Backend:

```powershell
cd backend
uv run pytest -q
uv run ruff check app tests
uv run mypy app
```

Frontend with bundled Node 22.12+:

```powershell
cd frontend
npm test
npm run typecheck
npm run lint
npm run build
npm run e2e
```

Repository checks:

```powershell
rg -n "copilot|OpenAICompatibleProvider|llm_api_key|mcp_oauth|oauth_provider|authorization_code|refresh_token" backend frontend README.md docs --glob '!docs/superpowers/plans/2026-08-25-twr-mcp-connections-navigation.md' --glob '!docs/superpowers/specs/2026-08-25-twr-mcp-connections-navigation-design.md'
git diff --check
git status --short
```

Expected: test/type/lint/build/E2E commands pass; the forbidden-symbol scan finds only explicitly historical statements in the new spec/handoff; Git status contains no unexpected files and may contain only the ignored runtime `backend/.local/` outside the delivery archive.

- [ ] **Step 5: Commit the verified product and documentation**

```powershell
git add frontend/e2e/mcp-connections.spec.ts frontend/playwright.config.ts README.md ENTREGA_E_CONTINUIDADE_CLAUDE.md docs
git commit -m "docs: finalize MCP registry delivery"
```

- [ ] **Step 6: Refresh and inspect the downloadable package**

Create the archive only from tracked `HEAD`, which automatically excludes `.git`, `.worktrees`, `.superpowers`, `node_modules`, caches, virtual environments, databases, `.env`, logs and `backend/.local/`:

```powershell
git archive --format=zip --output=outputs/TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25.zip HEAD
tar -tf outputs/TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25.zip
```

Confirm the archive includes the revised spec, implementation plan, README, handoff and source tree. Scan the listing for `.env`, database, cache, `node_modules`, `.superpowers` and runtime artifacts; scan extracted text or `git grep` for secret patterns before delivery. The ZIP remains ignored and is not committed.

---

## Final Acceptance Checklist

- [ ] No OAuth or copilot runtime survives in backend or frontend.
- [ ] No OpenAI/Anthropic API key is requested or loaded.
- [ ] The local read-only MCP server still exposes five tools.
- [ ] Authenticated users can manage only their own MCP connection records.
- [ ] No secret is stored and validation makes no outbound network call.
- [ ] Claude and ChatGPT guidance is accurate and does not promise automatic login/installation.
- [ ] Sidebar, icons, product mark, desktop compact mode and mobile navigation are accessible and polished.
- [ ] Backend, frontend, production build and E2E verification pass.
- [ ] The final archive contains the implementation and complete continuation documentation but no runtime/private artifacts.
