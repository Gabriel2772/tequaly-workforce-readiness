# TWR MCP Connections and Navigation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the internal AI copilot with per-user, revocable Claude/ChatGPT MCP connections and deliver a polished icon-based navigation and product mark.

**Architecture:** Keep FastAPI as the application, OAuth authorization, and MCP resource host. Reuse the installed MCP SDK for OAuth handlers, protected-resource discovery, bearer middleware, and Streamable HTTP; keep TWR-specific consent, grants, token storage, and RBAC in focused `app/mcp` modules. The Next.js UI remains a client of authenticated management endpoints and never stores provider credentials.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2, Alembic, MCP Python SDK 2.x, Pydantic 2, Next.js 16.3, React 19, TypeScript 6, Vitest, Playwright.

**Spec:** `docs/superpowers/specs/2026-08-25-twr-mcp-connections-navigation-design.md`

## Global Constraints

- Remove the internal chat and floating AI button; do not add another chat surface.
- Expose exactly five `READ` MCP tools and no generic URL, SQL, write, solver, import, calibration, or outcome tool.
- The only remote OAuth scope is `twr:read`; the minimum TWR role is `viewer`.
- Use Authorization Code with PKCE `S256`, exact registered redirect URIs, required `resource`, short-lived authorization codes, 15-minute access tokens, and 30-day rotating refresh tokens.
- Persist only hashes of authorization codes, CSRF values, and refresh tokens; never persist raw values or log authorization headers.
- Remote MCP is disabled by default and requires an authenticated TWR deployment; production requires a public HTTPS base URL.
- Preserve local stdio MCP behavior and use the same deterministic tool registry for both transports.
- Use the installed MCP SDK for protocol framing, OAuth handlers, resource metadata, and Streamable HTTP.
- Do not add OpenAI or Anthropic API keys, model settings, RAG, SSO, conversation history, or public directory publication.
- Read the relevant Next.js 16 guide under `frontend/node_modules/next/dist/docs/` before changing App Router pages, per `frontend/AGENTS.md`.
- Use TDD for every behavior change and make a focused commit after every task.

## File Structure

### Backend MCP package

- `backend/app/mcp/models.py`: persistent OAuth clients, pending authorization requests, codes, grants, and refresh-token families.
- `backend/app/mcp/schemas.py`: management and consent HTTP contracts.
- `backend/app/mcp/security.py`: secret hashing, signed access tokens, canonical resource checks, and CSRF comparison.
- `backend/app/mcp/repository.py`: transactional persistence and ownership queries; no HTTP or MCP protocol logic.
- `backend/app/mcp/oauth_provider.py`: adapter implementing the MCP SDK authorization-provider and token-verifier protocols.
- `backend/app/mcp/oauth_routes.py`: exposes SDK OAuth routes at the approved public paths.
- `backend/app/mcp/router.py`: authenticated connection info, listing, revocation, and consent endpoints.
- `backend/app/mcp/tools.py`: five deterministic read tool definitions.
- `backend/app/mcp/registry.py`: strict read-only registry moved from the former AI namespace.
- `backend/app/mcp/types.py`: registry context and definitions.
- `backend/app/mcp/server.py`: shared stdio server plus authenticated Streamable HTTP ASGI app.

### Frontend

- `frontend/components/icons.tsx`: accessible, stroke-consistent SVG icon system.
- `frontend/components/brand-mark.tsx`: original T/W readiness symbol.
- `frontend/features/mcp/connections-page.tsx`: connection cards, environment diagnostics, grants, copy, and revoke interactions.
- `frontend/features/mcp/consent-page.tsx`: authenticated approve/deny flow.
- `frontend/app/conexoes-ia/page.tsx`: route composition for connection management.
- `frontend/app/conexoes-ia/autorizar/page.tsx`: route composition for OAuth consent.

---

### Task 1: MCP configuration and persistent authorization model

**Files:**
- Create: `backend/app/mcp/__init__.py`
- Create: `backend/app/mcp/models.py`
- Create: `backend/migrations/versions/0010_mcp_oauth.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/migrations/env.py`
- Modify: `.env.example`
- Modify: `backend/tests/test_config.py`
- Modify: `backend/tests/integration/test_migrations.py`

**Interfaces:**
- Produces: `Settings.mcp_resource_url: str | None`, `Settings.mcp_issuer_url: str | None`, `Settings.mcp_allowed_redirect_hosts: list[str]`, and explicit request-limit settings.
- Produces: `McpOAuthClient`, `McpAuthorizationRequest`, `McpAuthorizationCode`, `McpAuthorizationGrant`, and `McpRefreshToken` SQLAlchemy models.

- [ ] **Step 1: Write failing configuration and migration tests**

```python
def test_remote_mcp_defaults_to_disabled() -> None:
    settings = Settings(_env_file=None)
    assert settings.mcp_remote_enabled is False
    assert settings.mcp_resource_url is None


def test_remote_mcp_derives_canonical_urls() -> None:
    settings = Settings(
        _env_file=None,
        auth_required=True,
        public_base_url="https://readiness.example.com",
    mcp_remote_enabled=True,
    mcp_oauth_secret="mcp-test-secret-with-enough-entropy",
)
    assert settings.mcp_resource_url == "https://readiness.example.com/mcp"
    assert settings.mcp_issuer_url == "https://readiness.example.com/oauth"

with pytest.raises(ValidationError):
    Settings(_env_file=None, mcp_remote_enabled=True, auth_required=False)
```

Extend the migration assertions with the exact table set:

```python
assert {
    "mcp_oauth_clients",
    "mcp_authorization_requests",
    "mcp_authorization_codes",
    "mcp_authorization_grants",
    "mcp_refresh_tokens",
} <= set(inspect(engine).get_table_names())
```

- [ ] **Step 2: Run the focused tests and confirm failure**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/test_config.py tests/integration/test_migrations.py -q`

Expected: FAIL because MCP settings and migration `0010_mcp_oauth` do not exist.

- [ ] **Step 3: Add exact settings and model invariants**

Add these settings and derived properties:

```python
public_base_url: str | None = None
mcp_remote_enabled: bool = False
mcp_access_token_minutes: int = 15
mcp_refresh_token_days: int = 30
mcp_oauth_secret: SecretStr | None = None
mcp_allowed_redirect_hosts: list[str] = []
mcp_tool_timeout_seconds: float = 30.0
mcp_max_request_bytes: int = 1_048_576
mcp_rate_limit_per_minute: int = 120

@property
def mcp_resource_url(self) -> str | None:
    return f"{self.public_base_url.rstrip('/')}/mcp" if self.public_base_url else None

@property
def mcp_issuer_url(self) -> str | None:
    return f"{self.public_base_url.rstrip('/')}/oauth" if self.public_base_url else None
```

Add a model validator: enabled remote MCP requires `auth_required=True`, a non-empty public base URL, a dedicated OAuth secret, and at least one allowed redirect host. Reject non-HTTPS public URLs outside `development`; allow HTTP localhost only in development.

Implement model columns with these rules:

```python
MCP_SCOPE = "twr:read"
AUTHORIZATION_REQUEST_MINUTES = 10
AUTHORIZATION_CODE_MINUTES = 5

# Client: UUID id, unique client_id, client_name, optional client_uri,
# JSON redirect_uris, token_endpoint_auth_method="none", active, timestamps.
# Request: hashed request id, client_id, redirect_uri, state, resource,
# JSON scopes, PKCE challenge/method, optional CSRF hash, status, expiry,
# optional decided_by_user_id and decided_at.
# Code: hashed code, grant_id, client_id, user_id, redirect_uri, resource,
# JSON scopes, PKCE challenge, expiry, optional consumed_at.
# Grant: user_id, client_id, JSON scopes, expiry, last_used_at, revoked_at,
# optional revoked_by_user_id and revocation_reason.
# Refresh: hashed token, grant_id, family_id, client_id, JSON scopes,
# expiry, optional consumed_at and revoked_at.
```

Create indexes for client lookup, request/code hash lookup, user grant listing, and refresh hash/family lookup. Add migration downgrade operations in strict reverse dependency order.

- [ ] **Step 4: Run tests and schema drift check**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/test_config.py tests/integration/test_migrations.py -q`

Expected: PASS, one linear migration head, offline PostgreSQL SQL compiles, SQLite round trip returns to only `alembic_version`.

- [ ] **Step 5: Commit**

```powershell
git add .env.example backend/app/core/config.py backend/app/mcp backend/migrations backend/tests/test_config.py backend/tests/integration/test_migrations.py
git commit -m "feat: add MCP authorization persistence"
```

### Task 2: OAuth security primitives

**Files:**
- Create: `backend/app/mcp/security.py`
- Create: `backend/tests/unit/mcp/test_security.py`

**Interfaces:**
- Produces: `McpAccessTokenClaims`, `hash_secret`, `new_secret`, `create_access_token`, `parse_access_token`, `verify_pkce_s256`, and `redirect_uri_allowed`.
- Consumes: canonical MCP resource URL and dedicated OAuth secret from Task 1.

- [ ] **Step 1: Write failing security tests**

```python
def test_access_token_is_audience_bound_and_tamper_evident() -> None:
    now = datetime(2026, 8, 25, 12, tzinfo=UTC)
    token = create_access_token(
        user_id="user-1",
        grant_id="grant-1",
        client_id="client-1",
        scopes=["twr:read"],
        resource="https://readiness.example.com/mcp",
        secret="mcp-test-secret-with-enough-entropy",
        expires_at=now + timedelta(minutes=15),
    )
    claims = parse_access_token(
        token,
        secret="mcp-test-secret-with-enough-entropy",
        expected_resource="https://readiness.example.com/mcp",
        now=now,
    )
    assert claims.user_id == "user-1"
    assert claims.grant_id == "grant-1"
    with pytest.raises(InvalidAccessToken):
        parse_access_token(
            token,
            secret="mcp-test-secret-with-enough-entropy",
            expected_resource="https://other.example.com/mcp",
            now=now,
        )


def test_pkce_requires_s256_and_exact_redirect_host() -> None:
    verifier = "A" * 43
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    assert verify_pkce_s256(verifier, challenge) is True
    assert redirect_uri_allowed("https://chatgpt.com/aip/callback", ["chatgpt.com"]) is True
    assert redirect_uri_allowed("https://chatgpt.com.evil.test/aip/callback", ["chatgpt.com"]) is False
```

- [ ] **Step 2: Run tests and confirm failure**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/unit/mcp/test_security.py -q`

Expected: FAIL because `app.mcp.security` does not exist.

- [ ] **Step 3: Implement small, deterministic primitives**

Use URL-safe random values with at least 32 bytes of entropy, SHA-256 hashes for database lookup, `hmac.compare_digest`, and a signed canonical JSON payload:

```python
@dataclass(frozen=True)
class McpAccessTokenClaims:
    user_id: str
    grant_id: str
    client_id: str
    scopes: list[str]
    resource: str
    expires_at: datetime
    token_id: str


def hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_secret() -> str:
    return secrets.token_urlsafe(32)
```

Reject malformed encoding, non-canonical signatures, expiration, missing `twr:read`, and audience mismatch. Allow redirect URIs only when they are HTTPS and their normalized hostname is in the allowlist, or when hostname is `localhost`/`127.0.0.1` in development.

- [ ] **Step 4: Run security tests**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/unit/mcp/test_security.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/mcp/security.py backend/tests/unit/mcp/test_security.py
git commit -m "feat: add audience-bound MCP tokens"
```

### Task 3: OAuth repository and MCP SDK provider

**Files:**
- Create: `backend/app/mcp/repository.py`
- Create: `backend/app/mcp/oauth_provider.py`
- Create: `backend/tests/unit/mcp/test_oauth_provider.py`

**Interfaces:**
- Produces: `McpOAuthRepository(session)` transactional operations.
- Produces: `SQLAlchemyOAuthProvider(session_factory, settings)` implementing `OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]` and `TokenVerifier`.
- Produces provider helpers: `get_consent`, `approve_consent`, `deny_consent`, `list_user_grants`, and `revoke_user_grant`.

- [ ] **Step 1: Write failing provider lifecycle tests**

Create an in-memory SQLite factory with one active `viewer`, then assert this exact lifecycle:

```python
params = AuthorizationParams(
    state="state-1",
    scopes=["twr:read"],
    code_challenge="challenge",
    redirect_uri=AnyUrl("https://chatgpt.com/aip/callback"),
    redirect_uri_provided_explicitly=True,
    resource="https://readiness.example.com/mcp",
)
consent_url = await provider.authorize(client_info, params)
request_id = parse_qs(urlparse(consent_url).query)["request"][0]
consent, csrf = await provider.get_consent(request_id, actor)
redirect_url = await provider.approve_consent(request_id, csrf, actor)
code = parse_qs(urlparse(redirect_url).query)["code"][0]
loaded = await provider.load_authorization_code(client_info, code)
tokens = await provider.exchange_authorization_code(client_info, loaded)
verified = await provider.verify_token(tokens.access_token)
assert verified is not None
assert verified.subject == actor.user_id
```

Add separate tests for: exact redirect rejection; `resource` mismatch; scope mismatch; expired request/code; single-use code; refresh rotation; reused refresh revoking its family; inactive user; revoked grant; and user A unable to revoke user B's grant.

- [ ] **Step 2: Run tests and confirm failure**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/unit/mcp/test_oauth_provider.py -q`

Expected: FAIL because repository and provider are not defined.

- [ ] **Step 3: Implement the repository boundary**

Use one `Session` per provider call and commit only inside repository commands. Implement direct SQLAlchemy methods. The simple lookups follow this form:

```python
def get_client(self, client_id: str) -> McpOAuthClient | None:
    return self.session.scalar(
        select(McpOAuthClient).where(
            McpOAuthClient.client_id == client_id,
            McpOAuthClient.active.is_(True),
        )
    )


def active_grant(self, grant_id: UUID) -> McpAuthorizationGrant | None:
    now = datetime.now(UTC)
    return self.session.scalar(
        select(McpAuthorizationGrant).where(
            McpAuthorizationGrant.id == grant_id,
            McpAuthorizationGrant.revoked_at.is_(None),
            McpAuthorizationGrant.expires_at > now,
        )
    )
```

Add `save_public_client`, `create_request`, `load_request`, `set_csrf`, `approve_request`, `deny_request`, `consume_code`, `rotate_refresh`, and `revoke_grant`. Hash inbound opaque values before lookup; use UTC timestamps; verify request state and CSRF in the same transaction that issues the code. `consume_code` sets `consumed_at` before committing. `rotate_refresh` marks the old token consumed, issues the new hash in the same family, and revokes the entire family when a consumed token is presented again. `revoke_grant` includes `actor_user_id` in its `WHERE` clause so cross-user revocation returns `False`.

- [ ] **Step 4: Implement the SDK adapter and rerun tests**

Map database records to the SDK types without exposing raw stored values. Token verification follows this complete boundary:

```python
async def verify_token(self, token: str) -> AccessToken | None:
    try:
        claims = parse_access_token(
            token,
            secret=self.settings.mcp_oauth_secret.get_secret_value(),
            expected_resource=self.settings.mcp_resource_url,
        )
    except InvalidAccessToken:
        return None
    with self.session_factory() as session:
        repository = McpOAuthRepository(session)
        grant = repository.active_grant(UUID(claims.grant_id))
        user = session.get(AppUser, UUID(claims.user_id))
        if grant is None or user is None or not user.active:
            return None
        grant.last_used_at = datetime.now(UTC)
        session.commit()
    return AccessToken(
        token=token,
        client_id=claims.client_id,
        scopes=claims.scopes,
        expires_at=int(claims.expires_at.timestamp()),
        resource=claims.resource,
        subject=claims.user_id,
        claims={"grant_id": claims.grant_id, "jti": claims.token_id},
    )
```

Implement all methods required by `OAuthAuthorizationServerProvider`: client lookup/registration; authorization-request creation; code loading/exchange; refresh loading/rotation; access loading; and token revocation. Each method calls the repository and security functions already defined. Code exchange returns a 15-minute signed access token plus a 30-day opaque refresh token; refresh exchange preserves or narrows scopes but never expands them. Access-token revocation parses `grant_id`; refresh-token revocation resolves its hash. Do not implement identity assertion or confidential-client secrets.

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/unit/mcp/test_oauth_provider.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/mcp/repository.py backend/app/mcp/oauth_provider.py backend/tests/unit/mcp/test_oauth_provider.py
git commit -m "feat: implement per-user MCP OAuth grants"
```

### Task 4: OAuth discovery, consent, and connection-management HTTP APIs

**Files:**
- Create: `backend/app/mcp/schemas.py`
- Create: `backend/app/mcp/rate_limit.py`
- Create: `backend/app/mcp/oauth_routes.py`
- Create: `backend/app/mcp/router.py`
- Create: `backend/tests/unit/mcp/test_rate_limit.py`
- Create: `backend/tests/integration/mcp/test_oauth_api.py`
- Create: `backend/tests/integration/mcp/test_management_api.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `build_oauth_routes(provider, settings) -> list[BaseRoute]`.
- Produces: `GET /mcp-management/info`, `GET /mcp-management/connections`, `DELETE /mcp-management/connections/{grant_id}`.
- Produces: `DELETE /mcp-management/admin/connections/{grant_id}` guarded by `require_admin_actor`.
- Produces: `GET /oauth/consent/{request_id}` and `POST /oauth/consent`.

- [ ] **Step 1: Write failing metadata and full-flow API tests**

The integration test must use `TestClient`, register a public client, start authorization, log in as a `viewer`, approve consent, exchange the code, and inspect the resulting grant:

```python
metadata = client.get("/.well-known/oauth-authorization-server/oauth")
assert metadata.json()["issuer"] == "https://readiness.example.com/oauth"
assert metadata.json()["authorization_endpoint"] == "https://readiness.example.com/oauth/authorize"
assert metadata.json()["token_endpoint_auth_methods_supported"] == ["none"]
registration = client.post("/oauth/register", json={
    "client_name": "ChatGPT test client",
    "redirect_uris": ["https://chatgpt.com/aip/callback"],
    "token_endpoint_auth_method": "none",
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "scope": "twr:read",
})
authorization = client.get("/oauth/authorize", params={
    "response_type": "code",
    "client_id": registration.json()["client_id"],
    "redirect_uri": "https://chatgpt.com/aip/callback",
    "scope": "twr:read",
    "state": "state-1",
    "code_challenge": challenge,
    "code_challenge_method": "S256",
    "resource": "https://readiness.example.com/mcp",
}, follow_redirects=False)
assert authorization.headers["location"].startswith("http://localhost:3000/conexoes-ia/autorizar")
```

Continue the test through `/auth/login`, consent GET/POST, `/oauth/token`, management listing, revocation, and failed refresh. Add `401` tests for unauthenticated consent/management and ownership tests for user A/user B.

Add rate-limit tests with an injected clock: registration permits 10 attempts per IP per hour and returns `429` on the 11th; token exchange permits 60 attempts per IP/client per minute; MCP permits the configured 120 calls per user/client/IP per minute. Assert the response includes `Retry-After` and contains no token or authorization header.

- [ ] **Step 2: Run API tests and confirm failure**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/unit/mcp/test_rate_limit.py tests/integration/mcp/test_oauth_api.py tests/integration/mcp/test_management_api.py -q`

Expected: FAIL with missing routes.

- [ ] **Step 3: Expose SDK routes under the approved public paths**

Build routes with `mcp.server.auth.routes.create_auth_routes` and issuer `https://<host>/oauth`. Map the SDK metadata route to the RFC 8414 path and prefix the SDK operational paths to obtain `/oauth/authorize`, `/oauth/token`, `/oauth/register`, and `/oauth/revoke`:

```python
def public_oauth_path(path: str) -> str:
    if path == "/.well-known/oauth-authorization-server":
        return "/.well-known/oauth-authorization-server/oauth"
    return f"/oauth{path}"
```

Copy each SDK operational `Route` endpoint and allowed methods into a new Starlette `Route` with the public path. Build the SDK `OAuthMetadata`, replace `token_endpoint_auth_methods_supported` and `revocation_endpoint_auth_methods_supported` with `["none"]`, and serve it through the SDK `MetadataHandler` at both the canonical path and root alias. Protected-resource metadata points to the canonical issuer `/oauth`. Assert metadata advertises `/oauth/authorize`, `/oauth/token`, `/oauth/register`, and `/oauth/revoke`. Enable `ClientRegistrationOptions` with only `twr:read` and enable `RevocationOptions`; `register_client` rejects every method other than `none`. Wrap `/oauth/register` and `/oauth/token` with the bounded in-memory fixed-window limiter from `rate_limit.py`; the key contains route, normalized client IP, and client ID when present. The limiter is process-local by design for this monolith and exposes this contract:

```python
@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int


def check(self, key: str, *, limit: int, window_seconds: int) -> RateLimitDecision:
    now = self.clock()
    live = [instant for instant in self.events[key] if instant > now - window_seconds]
    if len(live) >= limit:
        return RateLimitDecision(False, max(1, int(live[0] + window_seconds - now)))
    live.append(now)
    self.events[key] = live
    return RateLimitDecision(True, 0)
```

- [ ] **Step 4: Add management and consent routers**

Define stable response contracts:

```python
class McpConnectionInfo(BaseModel):
    enabled: bool
    public_url: str | None
    https_ready: bool
    scope: Literal["twr:read"]
    tools: list[str]


class McpConnectionView(BaseModel):
    id: UUID
    client_name: str
    client_uri: str | None
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime
    status: Literal["active", "expired", "revoked"]


class ConsentDecision(BaseModel):
    request_id: str
    csrf_token: str
    approved: bool
```

Require `require_session_actor` for every route except info when remote MCP is disabled. Consent GET returns client, scope, five tool names, expiry, and a fresh CSRF token. Consent POST returns a server-constructed callback such as `{ "redirect_url": "https://client.example/callback?code=authorization-code" }`; it never accepts a redirect URL from the browser.

User revocation requires grant ownership. Administrative revocation uses `require_admin_actor`, accepts an audit reason of 3–240 characters, and may revoke any grant without changing its owner.

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/unit/mcp/test_rate_limit.py tests/integration/mcp/test_oauth_api.py tests/integration/mcp/test_management_api.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/mcp backend/app/main.py backend/tests/integration/mcp
git commit -m "feat: expose MCP OAuth and connection APIs"
```

### Task 5: Shared read tools and authenticated Streamable HTTP

**Files:**
- Create: `backend/app/mcp/types.py`
- Create: `backend/app/mcp/registry.py`
- Create: `backend/app/mcp/tools.py`
- Create: `backend/app/mcp/server.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/integration/ai/test_mcp.py` and move it to `backend/tests/integration/mcp/test_transports.py`
- Modify: `backend/tests/unit/ai/tools/test_registry.py` and move it to `backend/tests/unit/mcp/test_registry.py`
- Delete: `backend/app/ai/tools/__init__.py`
- Delete: `backend/app/ai/tools/read_tools.py`
- Delete: `backend/app/ai/tools/registry.py`
- Delete: `backend/app/ai/tools/types.py`
- Delete: `backend/app/mcp_server.py`

**Interfaces:**
- Produces: `build_read_registry() -> ToolRegistry`.
- Produces: `build_mcp_server(session_factory, token_verifier=None) -> MCPServer[Any]`.
- Produces: `build_remote_mcp_app(session_factory, provider, settings) -> Starlette`.
- Consumes: `SQLAlchemyOAuthProvider.verify_token` from Task 3.

- [ ] **Step 1: Write failing transport and identity tests**

Preserve the existing stdio equivalence test, then add a remote request test that obtains a valid access token from Task 4 and sends MCP initialization followed by `tools/list`:

```python
initialize = client.post(
    "/mcp",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": "2025-06-18",
        "Origin": "https://readiness.example.com",
    },
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "integration-test", "version": "1"},
        },
    },
)
assert initialize.status_code == 200
```

Add cases for missing token (`401` plus `resource_metadata`), wrong audience (`401`), revoked grant (`401`), unexpected Origin, oversized payload (`413`), rate limit (`429`), read-tool timeout, extra tool arguments, and exact five-name catalog. Use `caplog` to prove audit records contain actor/client/tool/outcome/duration but neither the bearer token nor the `Authorization` header.

- [ ] **Step 2: Run transport tests and confirm failure**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/integration/mcp/test_transports.py tests/unit/mcp/test_registry.py -q`

Expected: FAIL because the remote transport and moved package do not exist.

- [ ] **Step 3: Move the neutral tool registry and build both transports**

Remove `openai_tools()` from the registry. Preserve strict Pydantic input validation and all five existing service handlers. Resolve the remote actor from the SDK auth context:

```python
def current_actor_id() -> str:
    access = get_access_token()
    return access.subject if access and access.subject else "mcp-local-viewer"
```

Build remote transport with the canonical resource and issuer:

```python
AuthSettings(
    issuer_url=AnyHttpUrl(settings.mcp_issuer_url),
    resource_server_url=AnyHttpUrl(settings.mcp_resource_url),
    required_scopes=["twr:read"],
)
```

Use `stateless_http=True`, `json_response=True`, the configured 1 MiB request limit, and `TransportSecuritySettings` with explicit public host/origin plus localhost allowances only in development. Wrap tool execution in `asyncio.wait_for(asyncio.to_thread(execute), timeout=settings.mcp_tool_timeout_seconds)`. Wrap `/mcp` with the Task 4 limiter keyed by normalized IP plus parsed access-token user/client claims. Mount the MCP Starlette app at `/` after all FastAPI routes.

Pass the provider as `token_verifier`, but do not pass it as `auth_server_provider` to `MCPServer`; Task 4 already installs the authorization-server routes at their approved paths, and passing both would create duplicate root `/authorize` and `/token` routes.

Emit one structured application log after each call with `event=mcp_tool_call`, `actor_id`, `client_id`, `grant_id`, `tool_name`, `outcome`, and `duration_ms`. Do not log tool arguments, employee data, raw request bodies, authorization codes, refresh tokens, access tokens, or headers.

- [ ] **Step 4: Wire the mounted app lifespan and run tests**

Enter `remote_mcp_app.router.lifespan_context(remote_mcp_app)` inside the FastAPI lifespan so the SDK session manager starts and stops with the main process. When remote MCP is disabled, do not mount the resource routes and return disabled info from the management endpoint.

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/integration/mcp/test_transports.py tests/unit/mcp/test_registry.py -q`

Expected: PASS with stdio and HTTP returning the same overview payload.

- [ ] **Step 5: Commit**

```powershell
git add backend/app/mcp backend/app/main.py backend/tests/integration/mcp backend/tests/unit/mcp
git rm backend/app/mcp_server.py backend/app/ai/tools backend/tests/integration/ai/test_mcp.py backend/tests/unit/ai/tools/test_registry.py
git commit -m "feat: add authenticated Streamable HTTP MCP"
```

### Task 6: Remove the internal copilot and OpenAI runtime

**Files:**
- Delete: `backend/app/ai/__init__.py`
- Delete: `backend/app/ai/orchestrator.py`
- Delete: `backend/app/ai/provider.py`
- Delete: `backend/app/ai/router.py`
- Delete: `backend/app/ai/schemas.py`
- Delete: `backend/app/ai/types.py`
- Delete: `backend/tests/integration/ai/test_chat_api.py`
- Delete: `backend/tests/unit/ai/test_orchestrator.py`
- Delete: `backend/tests/unit/ai/test_provider.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `.env.example`
- Modify: `backend/tests/test_health.py`
- Modify: `backend/tests/test_config.py`

**Interfaces:**
- Removes: `/copilot/health`, `/copilot/chat`, `AIOrchestrator`, and all `TWR_LLM_*` settings.
- Preserves: `/health`, deterministic MCP tools, and all operational routes.

- [ ] **Step 1: Change tests to the new public contract**

```python
def test_health_reports_core_and_remote_mcp_state() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mcp_remote": "disabled"}


def test_removed_copilot_routes_are_not_found() -> None:
    client = TestClient(create_app())
    assert client.get("/copilot/health").status_code == 404
    assert client.post("/copilot/chat", json={"message": "x"}).status_code == 404
```

- [ ] **Step 2: Run focused tests and confirm failure**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/test_health.py tests/test_config.py -q`

Expected: FAIL while the old LLM contract still exists.

- [ ] **Step 3: Remove the old runtime and regenerate the lock**

Delete the listed files after confirming every read tool now lives under `app.mcp`. Remove `openai>=2,<3` and all LLM fields from `Settings`; run:

Run: `cd backend; uv lock`

Expected: `openai` disappears from direct and transitive project requirements unless another retained dependency requires it.

- [ ] **Step 4: Run backend unit and integration tests**

Run: `cd backend; .venv\Scripts\python.exe -m pytest tests/test_health.py tests/test_config.py tests/unit/mcp tests/integration/mcp -q`

Expected: PASS and both old copilot routes return `404`.

- [ ] **Step 5: Commit**

```powershell
git add .env.example backend
git commit -m "refactor: remove internal AI copilot"
```

### Task 7: Frontend connection management page

**Files:**
- Modify: `frontend/lib/api.ts`
- Create: `frontend/features/mcp/connections-page.tsx`
- Create: `frontend/features/mcp/connections-page.test.tsx`
- Create: `frontend/app/conexoes-ia/page.tsx`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Produces: `McpConnectionInfo`, `McpConnection`, `getMcpConnectionInfo`, `listMcpConnections`, and `revokeMcpConnection`.
- Consumes: management API contracts from Task 4.

- [ ] **Step 1: Read the Next.js guides and write failing UI tests**

Read: `frontend/node_modules/next/dist/docs/01-app/01-getting-started/03-layouts-and-pages.md` and the client-component/data-fetching guide present in the same docs tree.

Test disabled and enabled states:

```tsx
const toolNames = [
  "get_readiness_overview",
  "get_operation",
  "get_employee_profile",
  "get_operational_fragility",
  "get_decision_run",
];

it("explains localhost limitations and exposes no fake connection", async () => {
  getMcpConnectionInfo.mockResolvedValue({
    enabled: false,
    public_url: null,
    https_ready: false,
    scope: "twr:read",
    tools: toolNames,
  });
  listMcpConnections.mockResolvedValue([]);
  render(<ConnectionsPage />);
  expect(await screen.findByText(/endereço público HTTPS/i)).not.toBeNull();
  expect(screen.getByRole("button", { name: "Conectar ao ChatGPT" })).toBeDisabled();
});

it("revokes only after confirmation", async () => {
  render(<ConnectionsPage />);
  fireEvent.click(await screen.findByRole("button", { name: /revogar chatgpt/i }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar revogação" }));
  await waitFor(() => expect(revokeMcpConnection).toHaveBeenCalledWith("grant-1"));
});
```

- [ ] **Step 2: Run the component test and confirm failure**

Run: `pnpm --filter frontend test -- frontend/features/mcp/connections-page.test.tsx`

Expected: FAIL because the component and API functions do not exist.

- [ ] **Step 3: Add typed API calls and the client component**

Use browser-side fetch with `credentials: "include"`. Add a DELETE helper that parses the same safe API error shape as `writeRequest`:

```typescript
export type McpConnectionInfo = {
  enabled: boolean;
  public_url: string | null;
  https_ready: boolean;
  scope: "twr:read";
  tools: string[];
};

export function revokeMcpConnection(grantId: string): Promise<void> {
  return deleteRequest(`/mcp-management/connections/${encodeURIComponent(grantId)}`);
}
```

Render four sections from the spec: security introduction, Claude/ChatGPT cards, exact copyable MCP URL plus tool catalog, and authorized connections. Open only stable generic provider surfaces (`https://claude.ai/` and `https://chatgpt.com/`) in a new tab; never claim automatic installation.

- [ ] **Step 4: Add responsive styles and run tests**

Use existing color tokens, 12 px panel radius, visible `:focus-visible`, a two-column provider grid collapsing below 800 px, and status text that does not rely on color.

Run: `pnpm --filter frontend test -- frontend/features/mcp/connections-page.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add frontend/lib/api.ts frontend/features/mcp frontend/app/conexoes-ia frontend/app/globals.css
git commit -m "feat: add MCP connection management page"
```

### Task 8: Frontend OAuth consent and login return flow

**Files:**
- Create: `frontend/features/mcp/consent-page.tsx`
- Create: `frontend/features/mcp/consent-page.test.tsx`
- Create: `frontend/app/conexoes-ia/autorizar/page.tsx`
- Modify: `frontend/features/auth/login-form.tsx`
- Modify: `frontend/features/auth/login-form.test.tsx`
- Modify: `frontend/app/entrar/page.tsx`
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/globals.css`

**Interfaces:**
- Produces: `getMcpConsent(requestId) -> Promise<McpConsentView>` and `decideMcpConsent(command) -> Promise<{redirect_url: string}>`.
- Consumes: opaque `request` query parameter only; never consumes a browser-provided redirect URI.

- [ ] **Step 1: Write failing consent and login-return tests**

```tsx
it("shows client, scope and exact read tools before approval", async () => {
  getMcpConsent.mockResolvedValue(consentFixture);
  render(<ConsentPage requestId="request-1" />);
  expect(await screen.findByRole("heading", { name: /autorizar chatgpt test client/i })).not.toBeNull();
  expect(screen.getByText("twr:read")).not.toBeNull();
  expect(screen.getByText("get_employee_profile")).not.toBeNull();
});

it("sends the server csrf token and follows only the returned redirect", async () => {
  decideMcpConsent.mockResolvedValue({ redirect_url: "https://chatgpt.com/aip/callback?code=safe" });
  render(<ConsentPage requestId="request-1" />);
  fireEvent.click(await screen.findByRole("button", { name: "Autorizar acesso" }));
  await waitFor(() => expect(decideMcpConsent).toHaveBeenCalledWith({
    request_id: "request-1",
    csrf_token: "csrf-1",
    approved: true,
  }));
});
```

Extend `LoginForm` tests so a validated internal `next=/conexoes-ia/autorizar?request=request-1` is used after login and external/protocol-relative values fall back to `/`.

- [ ] **Step 2: Run tests and confirm failure**

Run: `pnpm --filter frontend test -- frontend/features/mcp/consent-page.test.tsx frontend/features/auth/login-form.test.tsx`

Expected: FAIL because consent APIs and safe `next` handling are absent.

- [ ] **Step 3: Implement safe login return and consent states**

Use this exact internal-return predicate:

```typescript
export function safeInternalPath(value: string | null): string {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/";
}
```

Consent handles loading, expired request, unauthenticated, approval, denial, and API failure. For unauthenticated requests, use:

```typescript
router.push(`/entrar?next=${encodeURIComponent(currentPath)}`);
```

On success call `window.location.assign(response.redirect_url)`; the backend remains the authority that constructed that URL.

- [ ] **Step 4: Run focused frontend tests**

Run: `pnpm --filter frontend test -- frontend/features/mcp/consent-page.test.tsx frontend/features/auth/login-form.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add frontend/features/mcp frontend/features/auth frontend/app/conexoes-ia frontend/app/entrar frontend/lib/api.ts frontend/app/globals.css
git commit -m "feat: add MCP consent experience"
```

### Task 9: Sidebar icons, product mark, and copilot UI removal

**Files:**
- Create: `frontend/components/icons.tsx`
- Create: `frontend/components/brand-mark.tsx`
- Create: `frontend/components/app-shell.test.tsx`
- Modify: `frontend/components/app-shell.tsx`
- Modify: `frontend/app/globals.css`
- Delete: `frontend/features/copilot/copilot-panel.tsx`
- Delete: `frontend/features/copilot/copilot-panel.test.tsx`
- Delete: `frontend/e2e/copilot.spec.ts`
- Modify: `frontend/lib/api.ts`

**Interfaces:**
- Produces: `Icon({ name, size, className })` where `name` is a closed union of the ten navigation symbols.
- Produces: `BrandMark()` with decorative SVG hidden from assistive technology by the labeled brand link.
- Removes: all frontend copilot API types/functions and floating UI.

- [ ] **Step 1: Write failing navigation accessibility tests**

```tsx
it("renders meaningful icon navigation and the MCP destination", () => {
  usePathname.mockReturnValue("/conexoes-ia");
  render(<AppShell><main>Conteúdo</main></AppShell>);
  const connection = screen.getByRole("link", { name: "Claude & ChatGPT" });
  expect(connection.getAttribute("aria-current")).toBe("page");
  expect(screen.queryByRole("button", { name: /copiloto/i })).toBeNull();
  expect(screen.getByRole("link", { name: "Tequaly Workforce Readiness" })).not.toBeNull();
});
```

Assert every navigation link has a unique accessible name and no old two-letter marker text remains.

- [ ] **Step 2: Run the shell test and confirm failure**

Run: `pnpm --filter frontend test -- frontend/components/app-shell.test.tsx`

Expected: FAIL because the new destination and SVG system are absent.

- [ ] **Step 3: Implement original inline SVG assets**

Use a shared `viewBox="0 0 24 24"`, `fill="none"`, `stroke="currentColor"`, `strokeWidth={1.8}`, rounded caps/joins, and `aria-hidden="true"`. Define these names exactly:

```typescript
export type IconName =
  | "overview" | "people" | "qualification" | "operation"
  | "planner" | "training" | "risk" | "audit"
  | "settings" | "connections";
```

The brand SVG combines a geometric T/W path, three nodes, and one readiness check. Do not import or imitate proprietary Claude, OpenAI, or Tequaly logos.

- [ ] **Step 4: Replace markers, remove copilot, and verify responsive focus**

Add `{ href: "/conexoes-ia", label: "Claude & ChatGPT", icon: "connections" }` and replace every `marker` with `icon`. Remove `<CopilotPanel />`, deleted API functions/types, and all `.copilot-*` CSS. Add native `title` plus accessible link names in collapsed mode and a visible active indicator independent of color.

Run: `pnpm --filter frontend test -- frontend/components/app-shell.test.tsx`

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add frontend/components frontend/app/globals.css frontend/lib/api.ts frontend/features frontend/e2e
git commit -m "feat: redesign navigation and remove copilot UI"
```

### Task 10: End-to-end OAuth/MCP proof, documentation, and final verification

**Files:**
- Create: `frontend/e2e/mcp-connections.spec.ts`
- Modify: `frontend/playwright.config.ts`
- Modify: `frontend/e2e/global-setup.ts`
- Modify: `README.md`
- Modify: `ENTREGA_E_CONTINUIDADE_CLAUDE.md`
- Modify: `.env.example`

**Interfaces:**
- Proves the user-visible flow and direct MCP protocol call against the packaged application.
- Documents local disabled mode and public HTTPS production configuration without provider API keys.

- [ ] **Step 1: Add a failing E2E flow**

Configure the E2E backend with these exact additional values:

```typescript
TWR_AUTH_REQUIRED: "true",
TWR_SESSION_SECRET: "e2e-session-secret-with-enough-entropy",
TWR_PUBLIC_BASE_URL: "http://127.0.0.1:8000",
TWR_MCP_REMOTE_ENABLED: "true",
TWR_MCP_OAUTH_SECRET: "e2e-mcp-secret-with-enough-entropy",
TWR_MCP_ALLOWED_REDIRECT_HOSTS: '["127.0.0.1"]',
```

Register `http://127.0.0.1:3000/mcp-test-callback` as the development callback. The test must:

```typescript
test("user authorizes, uses, and revokes a personal MCP connection", async ({ page, request }) => {
  await page.goto("/entrar");
  await page.getByLabel("Usuário").fill("planejador.demo");
  await page.getByLabel("Senha").fill("TequalyDemo!2026");
  await page.getByRole("button", { name: "Entrar" }).click();
  await page.getByRole("link", { name: "Claude & ChatGPT" }).click();
  await expect(page.getByRole("heading", { name: /conexões claude e chatgpt/i })).toBeVisible();
  await expect(page.getByText("http://127.0.0.1:8000/mcp")).toBeVisible();
});
```

Use Playwright's API request context for dynamic registration, PKCE authorization/token exchange, and MCP `initialize`/`tools/list`; use the browser page for consent and revocation. Assert the call after revocation returns `401`.

- [ ] **Step 2: Build and run the E2E test to expose integration gaps**

Run: `pnpm --filter frontend build`

Run: `pnpm --filter frontend e2e -- mcp-connections.spec.ts`

Expected before fixes: FAIL at the first remaining integration or presentation defect.

- [ ] **Step 3: Fix only evidence-backed integration defects and document operation**

Document these exact modes:

```dotenv
# Local UI/stdio demonstration: remote MCP stays disabled.
TWR_MCP_REMOTE_ENABLED=false

# Public deployment example; values belong in a secret manager.
TWR_AUTH_REQUIRED=true
TWR_PUBLIC_BASE_URL=https://readiness.example.com
TWR_MCP_REMOTE_ENABLED=true
TWR_MCP_OAUTH_SECRET=replace-in-secret-manager
TWR_MCP_ALLOWED_REDIRECT_HOSTS=["chatgpt.com","claude.ai"]
```

Explain that each person adds the displayed TWR MCP URL in their own Claude/ChatGPT client; no ChatGPT/Claude subscription token or model API key enters TWR. Include connection, consent, revocation, localhost, HTTPS, plan/admin limitations, and the five read tools.

- [ ] **Step 4: Run complete verification**

Run backend:

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check app tests
.venv\Scripts\python.exe -m mypy app
```

Run frontend from repository root:

```powershell
pnpm --filter frontend test
pnpm --filter frontend typecheck
pnpm --filter frontend lint
pnpm --filter frontend build
pnpm --filter frontend e2e
```

Expected: backend suite passes except the existing PostgreSQL test when `TWR_TEST_DATABASE_URL` is absent; Ruff and mypy are green; all Vitest files, typecheck, lint, production build, and five existing plus the new Edge E2E flow pass.

- [ ] **Step 5: Inspect the presentation and commit**

Open `/conexoes-ia`, `/risco-e-cobertura`, and the collapsed sidebar at widths 1440, 1024, and 390 px. Verify no overlap, clipped label, missing focus ring, floating AI button, provider-brand imitation, or false “connected” state. Then commit:

```powershell
git add .env.example README.md ENTREGA_E_CONTINUIDADE_CLAUDE.md frontend/e2e frontend/playwright.config.ts
git commit -m "test: verify per-user MCP connection flow"
```

### Task 11: Delivery package refresh

**Files:**
- Modify: `ENTREGA_E_CONTINUIDADE_CLAUDE.md`
- Create: `scripts/package_delivery.ps1`
- Create: `outputs/TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25_MCP.zip`

**Interfaces:**
- Produces a clean handoff archive that excludes `.git`, `.venv`, `node_modules`, `.next`, local databases, secrets, caches, test artifacts, and prior ZIP files.

- [ ] **Step 1: Verify the handoff reflects the final state**

Add final commit identifiers, all verification counts, implemented OAuth/MCP behavior, local/public setup instructions, security decisions, remaining production dependencies, and the explicit statement that provider subscriptions are not embedded in TWR.

- [ ] **Step 2: Scan the tracked tree for secret patterns**

Run:

```powershell
git grep -n -I -E "sk-proj-|OPENAI_API_KEY=.+|ANTHROPIC_API_KEY=.+|TWR_MCP_OAUTH_SECRET=.+" -- ':!docs/superpowers/plans/*'
```

Expected: no real secret; only empty or clearly synthetic example values where documented.

- [ ] **Step 3: Build the archive using the existing packaging workflow**

Create `scripts/package_delivery.ps1` with an explicit repository root, a uniquely named staging directory under the system temporary directory, and these excluded directory names: `.git`, `.worktrees`, `.venv`, `node_modules`, `.next`, `.local`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.e2e`, `outputs`, `playwright-report`, and `test-results`. Exclude `.env` and `.env.*` except `.env.example`, copy the remaining tracked project tree to staging, create the ZIP, and remove only the validated staging directory in a `finally` block. Then run:

```powershell
.\scripts\package_delivery.ps1 -OutputPath .\outputs\TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25_MCP.zip
```

Do not archive `backend/.local/` or `backend/.env`.

- [ ] **Step 4: Inspect archive contents and hash**

```powershell
tar -tf outputs/TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25_MCP.zip
Get-FileHash outputs/TEQUALY_WORKFORCE_READINESS_ENTREGA_2026-08-25_MCP.zip -Algorithm SHA256
```

Expected: source, migrations, tests, docs, samples, and lockfiles are present; ignored runtime artifacts and secrets are absent.

- [ ] **Step 5: Commit the tracked handoff documentation**

```powershell
git add ENTREGA_E_CONTINUIDADE_CLAUDE.md scripts/package_delivery.ps1
git commit -m "docs: refresh MCP delivery handoff"
```
