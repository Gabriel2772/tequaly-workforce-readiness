# Plano e gate de testes

## Camadas

- pytest unitário e integração: regras, ownership, validação estrutural, auditoria, migrações, APIs e MCP stdio;
- performance: 3.000 pessoas, elegibilidade e três objetivos;
- Vitest/Testing Library: fluxos, erros recuperáveis, filtros, navegação e acessibilidade;
- Playwright + Microsoft Edge: banco limpo, seed, login e fluxos visíveis em build de produção;
- qualidade: Ruff, mypy, ESLint, TypeScript, Next build, scan de símbolos e `git diff --check`.

## Invariantes MCP

- cada registro pertence ao usuário da sessão; `user_id` do browser é recusado;
- registro de outro usuário não pode ser listado, editado, validado ou excluído;
- nenhum segredo é aceito/persistido e nenhuma validação chama a rede;
- HTTPS remoto é obrigatório, exceto localhost HTTP em desenvolvimento;
- somente a constraint `uq_user_mcp_connection_name` vira `409`;
- o catálogo local contém exatamente cinco ferramentas com efeito `read`;
- a navegação ativa respeita boundary de segmento e a gaveta móvel fecha em mudança de pathname;
- o E2E cria, valida, desativa, ativa e exclui uma conexão após login real.

## Comandos focados

```powershell
Set-Location backend
uv run pytest tests/unit/mcp_connections tests/integration/mcp_connections -q

Set-Location ..\frontend
pnpm exec vitest run features/mcp-connections/mcp-connections-page.test.tsx components/app-shell.test.tsx
pnpm exec playwright test e2e/mcp-connections.spec.ts
```

## Gate completo

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

Checks de repositório:

```powershell
rg -n "copilot|OpenAICompatibleProvider|llm_api_key|mcp_oauth|oauth_provider|authorization_code|refresh_token" backend frontend README.md docs --glob '!docs/superpowers/plans/2026-08-25-twr-mcp-connections-navigation.md' --glob '!docs/superpowers/specs/2026-08-25-twr-mcp-connections-navigation-design.md'
git diff --check
git status --short
```

Ocorrências permitidas no scan são apenas asserções negativas de regressão e documentos históricos claramente identificados. Nenhum símbolo pode representar runtime ativo.

O E2E aplica migrações `0001` a `0010`, cria um SQLite isolado em `frontend/.e2e/` e semeia 300 pessoas. O round-trip PostgreSQL só roda com `TWR_TEST_DATABASE_URL` apontando para banco vazio terminado em `_test`.

## Resultado final

- Backend: `204 passed, 1 skipped`; Ruff passou e MyPy passou em 105 source files.
- Frontend: Vitest passou (23 arquivos, 43 testes), TypeScript e ESLint passaram.
- Build: Next.js passou e lista `/conexoes-mcp`.
- E2E: 6 passaram em 5,6 min, com migrações `0001..0010` e seed de 300.

A cadeia Alembic passa pela ponte `0010_mcp_oauth`, e o teste de migrações cobre o upgrade legado.

Detalhes do recurso MCP ficam em `docs/test-results/ai-mcp.md`.
