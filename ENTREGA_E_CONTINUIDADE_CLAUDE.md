# Tequaly Workforce Readiness — entrega e continuidade

Data de consolidação: 26 de agosto de 2026
Branch: `feat/twr-core`
Commit: consulte `git log -1 --oneline` no pacote.

## 1. Veredito e fronteira

A versão demonstrável reúne núcleo determinístico, solver, trilha de auditoria, autenticação por perfil, importação/exportação, inteligência operacional, cadastro individual de conexões MCP e servidor MCP local somente leitura.

Não existe chat interno, execução de modelos, dependência de OpenAI/Anthropic ou campo de chave de provedor de IA. O fluxo OAuth planejado anteriormente foi removido; o TWR não autentica Claude ou ChatGPT. A página MCP apenas organiza metadados não secretos por usuário autenticado. A configuração final, inclusive eventual autenticação exigida pelo servidor, acontece no cliente externo e pode depender de plano, função ou administrador.

Para produção ainda são necessários dados oficiais, validação das regras com RH/operações, PostgreSQL na infraestrutura alvo, SSO corporativo, implantação, observabilidade e aceite de segurança/acessibilidade.

## 2. Premissas simuladas

O seed principal contém 2.200 colaboradores e o benchmark 3.000, com 12 famílias, 90 cargos canônicos, 130 aliases, 72 qualificações, 24 autorizações, 24 treinamentos e 8 operações. São hipóteses reprodutíveis, não headcount ou catálogo oficial da Tequaly. Dados reais devem entrar por profiling, mapeamento, preview e aprovação governada; nunca substituir o seed silenciosamente.

## 3. Arquitetura entregue

```text
Next.js 16 / React 19 / TypeScript
             |
             v
FastAPI modular + sessão TWR assinada
      |              |                 |
      v              v                 v
SQLAlchemy       regras/CP-SAT    ToolRegistry read-only
      |                                  |
      v                                  v
PostgreSQL alvo / SQLite teste       MCP stdio local
             |
             v
user_mcp_connections (metadados por usuário)
```

O frontend não contém regra de elegibilidade/solver. A validação MCP é estrutural e não abre conexão para URLs do usuário. O servidor local continua iniciado por `uv run python -m app.mcp_server` e expõe cinco ferramentas determinísticas de leitura.

## 4. Schema e rotas MCP atuais

Migração: `0010_user_mcp_connections`, após `0009_import_batches`.

Tabela `user_mcp_connections`:

- `id`, `user_id` com FK para `app_users`;
- `name` (120), `client_type` (`claude|chatgpt`);
- `endpoint_url` (2048), `transport` (`streamable_http|sse`);
- `notes` (1000), `enabled`;
- `last_validated_at`, `created_at`, `updated_at`;
- unique `uq_user_mcp_connection_name` sobre usuário, destino e nome;
- índice `ix_user_mcp_connections_owner` sobre usuário e atualização.

Rotas autenticadas:

- `GET /mcp-connections`;
- `POST /mcp-connections`;
- `PATCH /mcp-connections/{connection_id}`;
- `POST /mcp-connections/{connection_id}/validate`;
- `DELETE /mcp-connections/{connection_id}`;
- `GET /mcp-connections/catalog`.

O owner sempre vem da sessão. A mesma resposta `404` protege IDs ausentes e de outro usuário. `409` é reservado à constraint nominal. Os eventos de auditoria omitem URL e notas.

## 5. Fluxo visual entregue

- rota frontend autenticada `/conexoes-mcp`;
- criação, edição, validação, cópia sem segredos, ativação, desativação e exclusão;
- busca e filtros por destino/estado;
- estados de loading, erro recuperável, sessão expirada e vazio;
- cards de Claude/ChatGPT com limites de plano/admin;
- sidebar com dez ícones SVG, marca vetorial original, active state com boundary de segmento, modo compacto e gaveta móvel que fecha também em mudança de pathname.

Capturas: não há PNG estático rastreado no pacote. O Playwright está configurado com `screenshot: "only-on-failure"` e `trace: "retain-on-failure"`; artefatos de execução ficam em `frontend/test-results/`, são privados/ignorados e não entram no ZIP. O fluxo visível é provado pelo E2E `frontend/e2e/mcp-connections.spec.ts` em desktop e viewport 390 × 844.

## 6. Catálogo MCP local

1. `get_readiness_overview`;
2. `get_operation`;
3. `get_employee_profile` sem custos individuais;
4. `get_operational_fragility`;
5. `get_decision_run`.

Não existem ferramentas de escrita, solver, seleção, outcome, importação ou calibração.

## 7. Instalação, execução e migrações

```powershell
Copy-Item .env.example backend\.env

Set-Location backend
uv sync --group dev
uv run alembic upgrade head
uv run python ..\scripts\seed_demo.py
uv run uvicorn app.main:create_app --factory --reload
```

Em outro terminal:

```powershell
Set-Location frontend
pnpm install
pnpm dev
```

Contas sintéticas: `viewer.demo`, `planner.demo`, `admin.demo`; senha comum `TequalyDemo!2026`. Não reutilizar em produção.

MCP local:

```powershell
Set-Location backend
uv run python -m app.mcp_server
```

## 8. Testes

Comandos focados:

```powershell
Set-Location backend
uv run pytest tests/unit/mcp_connections tests/integration/mcp_connections -q

Set-Location ..\frontend
pnpm exec vitest run features/mcp-connections/mcp-connections-page.test.tsx components/app-shell.test.tsx
pnpm exec playwright test e2e/mcp-connections.spec.ts
```

Gate completo:

```powershell
Set-Location backend
uv run pytest -q
uv run ruff check app tests
uv run mypy app

Set-Location ..\frontend
pnpm test
pnpm typecheck
pnpm lint
pnpm build
pnpm e2e
```

Resultado final (preenchido somente após o gate):

| Gate | Resultado |
|---|---|
| Backend pytest | `204 passed, 1 skipped` (skip: PostgreSQL round-trip sem `TWR_TEST_DATABASE_URL`) |
| Backend Ruff | passou (`All checks passed!`) |
| Backend mypy | passou (105 source files, sem issues) |
| Frontend Vitest | passou (23 arquivos, 43 testes) |
| Frontend TypeScript | passou |
| Frontend ESLint | passou |
| Next.js build | passou; build lista `/conexoes-mcp` |
| Playwright Edge | 6 passaram em 5,6 min; migrações `0001..0010` e seed de 300 |

A cadeia Alembic passa pela ponte `0010_mcp_oauth`, e o teste de migrações cobre o upgrade legado.

O round-trip PostgreSQL real permanece condicionado a `TWR_TEST_DATABASE_URL` apontando para um banco vazio terminado em `_test`; o gate local usa SQLite para migrações/E2E.

## 9. Pendências de produção

1. receber fontes oficiais de pessoas, cargos, qualificações, autorizações, treinamentos, operações, disponibilidade e custos;
2. definir base legal, minimização, retenção, perfis de acesso e controles LGPD;
3. validar mapeamentos e regras com responsáveis de RH/operações;
4. executar migrações, integração, performance e backup/restore em PostgreSQL alvo;
5. substituir contas demo e fallback local por SSO corporativo;
6. configurar TLS, cofre de segredos da própria aplicação, logs, métricas, alertas, deploy e rollback;
7. realizar testes de segurança, acessibilidade e aceite com dados controlados;
8. decidir separadamente qualquer servidor MCP remoto, com identidade, autenticação, limites e observabilidade próprios.

## 10. Continuidade

Leia nesta ordem: este arquivo, `README.md`, `docs/architecture.md`, `docs/data-model.md`, `docs/mcp.md`, `docs/test-plan.md` e a spec implementada em `docs/superpowers/specs/2026-08-25-twr-user-mcp-registry-visual-design.md`.

Preserve `backend/.local/`; nunca inclua `.env`, bancos, caches, `.venv`, `node_modules`, `.next`, traces ou resultados Playwright no Git/ZIP. O arquivo de entrega é gerado exclusivamente por `git archive HEAD`.
