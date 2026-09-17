# Tequaly Workforce Readiness � entrega e continuidade

Data de consolida��o: 26 de agosto de 2026
Branch: `feat/twr-core`
Commit: consulte `git log -1 --oneline` no pacote.

## 1. Veredito e fronteira

A vers�o demonstr�vel re�ne n�cleo determin�stico, solver, trilha de auditoria, autentica��o por perfil, importa��o/exporta��o, intelig�ncia operacional, cadastro individual de conex�es MCP e servidor MCP local somente leitura.

N�o existe chat interno, execu��o de modelos, depend�ncia de OpenAI/Anthropic ou campo de chave de provedor de IA. O fluxo OAuth planejado anteriormente foi removido; o TWR n�o autentica Claude ou ChatGPT. A p�gina MCP apenas organiza metadados n�o secretos por usu�rio autenticado. A configura��o final, inclusive eventual autentica��o exigida pelo servidor, acontece no cliente externo e pode depender de plano, fun��o ou administrador.

Para produ��o ainda s�o necess�rios dados oficiais, valida��o das regras com RH/opera��es, PostgreSQL na infraestrutura alvo, SSO corporativo, implanta��o, observabilidade e aceite de seguran�a/acessibilidade.

## 2. Premissas simuladas

O seed principal cont�m 2.200 colaboradores e o benchmark 3.000, com 12 fam�lias, 90 cargos can�nicos, 130 aliases, 72 qualifica��es, 24 autoriza��es, 24 treinamentos e 8 opera��es. S�o hip�teses reprodut�veis, n�o headcount ou cat�logo oficial da Tequaly. Dados reais devem entrar por profiling, mapeamento, preview e aprova��o governada; nunca substituir o seed silenciosamente.

## 3. Arquitetura entregue

```text
Next.js 16 / React 19 / TypeScript
             |
             v
FastAPI modular + sess�o TWR assinada
      |              |                 |
      v              v                 v
SQLAlchemy       regras/CP-SAT    ToolRegistry read-only
      |                                  |
      v                                  v
PostgreSQL alvo / SQLite teste       MCP stdio local
             |
             v
user_mcp_connections (metadados por usu�rio)
```

O frontend n�o cont�m regra de elegibilidade/solver. A valida��o MCP � estrutural e n�o abre conex�o para URLs do usu�rio. O servidor local continua iniciado por `uv run python -m app.mcp_server` e exp�e cinco ferramentas determin�sticas de leitura.

## 4. Schema e rotas MCP atuais

Migra��o: `0010_user_mcp_connections`, ap�s `0009_import_batches`.

Tabela `user_mcp_connections`:

- `id`, `user_id` com FK para `app_users`;
- `name` (120), `client_type` (`claude|chatgpt`);
- `endpoint_url` (2048), `transport` (`streamable_http|sse`);
- `notes` (1000), `enabled`;
- `last_validated_at`, `created_at`, `updated_at`;
- unique `uq_user_mcp_connection_name` sobre usu�rio, destino e nome;
- �ndice `ix_user_mcp_connections_owner` sobre usu�rio e atualiza��o.

Rotas autenticadas:

- `GET /mcp-connections`;
- `POST /mcp-connections`;
- `PATCH /mcp-connections/{connection_id}`;
- `POST /mcp-connections/{connection_id}/validate`;
- `DELETE /mcp-connections/{connection_id}`;
- `GET /mcp-connections/catalog`.

O owner sempre vem da sess�o. A mesma resposta `404` protege IDs ausentes e de outro usu�rio. `409` � reservado � constraint nominal. Os eventos de auditoria omitem URL e notas.

## 5. Fluxo visual entregue

- rota frontend autenticada `/conexoes-mcp`;
- cria��o, edi��o, valida��o, c�pia sem segredos, ativa��o, desativa��o e exclus�o;
- busca e filtros por destino/estado;
- estados de loading, erro recuper�vel, sess�o expirada e vazio;
- cards de Claude/ChatGPT com limites de plano/admin;
- sidebar com dez �cones SVG, marca vetorial original, active state com boundary de segmento, modo compacto e gaveta m�vel que fecha tamb�m em mudan�a de pathname.

Capturas: n�o h� PNG est�tico rastreado no pacote. O Playwright est� configurado com `screenshot: "only-on-failure"` e `trace: "retain-on-failure"`; artefatos de execu��o ficam em `frontend/test-results/`, s�o privados/ignorados e n�o entram no ZIP. O fluxo vis�vel � provado pelo E2E `frontend/e2e/mcp-connections.spec.ts` em desktop e viewport 390 � 844.

## 6. Cat�logo MCP local

1. `get_readiness_overview`;
2. `get_operation`;
3. `get_employee_profile` sem custos individuais;
4. `get_operational_fragility`;
5. `get_decision_run`.

N�o existem ferramentas de escrita, solver, sele��o, outcome, importa��o ou calibra��o.

## 7. Instala��o, execu��o e migra��es

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

Contas sint�ticas: `viewer.demo`, `planner.demo`, `admin.demo`; senha comum `TequalyDemo!2026`. N�o reutilizar em produ��o.

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

Resultado final (preenchido somente ap�s o gate):

| Gate | Resultado |
|---|---|
| Backend pytest | `204 passed, 1 skipped` (skip: PostgreSQL round-trip sem `TWR_TEST_DATABASE_URL`) |
| Backend Ruff | passou (`All checks passed!`) |
| Backend mypy | passou (105 source files, sem issues) |
| Frontend Vitest | passou (23 arquivos, 43 testes) |
| Frontend TypeScript | passou |
| Frontend ESLint | passou |
| Next.js build | passou; build lista `/conexoes-mcp` |
| Playwright Edge | 6 passaram em 5,6 min; migra��es `0001..0010` e seed de 300 |

A cadeia Alembic passa pela ponte `0010_mcp_oauth`, e o teste de migra��es cobre o upgrade legado.

O round-trip PostgreSQL real permanece condicionado a `TWR_TEST_DATABASE_URL` apontando para um banco vazio terminado em `_test`; o gate local usa SQLite para migra��es/E2E.

## 9. Pend�ncias de produ��o

1. receber fontes oficiais de pessoas, cargos, qualifica��es, autoriza��es, treinamentos, opera��es, disponibilidade e custos;
2. definir base legal, minimiza��o, reten��o, perfis de acesso e controles LGPD;
3. validar mapeamentos e regras com respons�veis de RH/opera��es;
4. executar migra��es, integra��o, performance e backup/restore em PostgreSQL alvo;
5. substituir contas demo e fallback local por SSO corporativo;
6. configurar TLS, cofre de segredos da pr�pria aplica��o, logs, m�tricas, alertas, deploy e rollback;
7. realizar testes de seguran�a, acessibilidade e aceite com dados controlados;
8. decidir separadamente qualquer servidor MCP remoto, com identidade, autentica��o, limites e observabilidade pr�prios.

## 10. Continuidade

Leia nesta ordem: este arquivo, `README.md`, `docs/architecture.md`, `docs/data-model.md`, `docs/mcp.md`, `docs/test-plan.md` e a spec implementada em `docs/superpowers/specs/2026-08-25-twr-user-mcp-registry-visual-design.md`.

Preserve `backend/.local/`; nunca inclua `.env`, bancos, caches, `.venv`, `node_modules`, `.next`, traces ou resultados Playwright no Git/ZIP. O arquivo de entrega � gerado exclusivamente por `git archive HEAD`.
