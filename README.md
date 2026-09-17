# Tequaly Workforce Readiness

Aplicação auditável para cadastrar força de trabalho, avaliar prontidão e montar equipes operacionais com regras determinísticas e OR-Tools CP-SAT. O produto não contém chat interno, execução de modelos ou integração com provedores de IA e não solicita chaves OpenAI ou Anthropic.

## Escopo demonstrável

O seed principal usa 2.200 colaboradores; o benchmark usa 3.000. O catálogo sintético contém 12 famílias, 90 cargos canônicos, 130 aliases, 72 qualificações, 24 autorizações, 24 treinamentos e 8 operações. Esses números são hipóteses de demonstração, não dados oficiais da Tequaly. A integração produtiva ainda exige fontes governadas, mapeamento, validação de regras, LGPD e aceite de RH/operações.

Além do núcleo operacional, usuários autenticados podem organizar metadados das próprias conexões MCP em `/conexoes-mcp`. O TWR guarda apenas nome, destino, endpoint, transporte, observação, estado e timestamps; não guarda tokens, senhas, headers ou outros segredos. A validação é somente estrutural e nunca chama a URL cadastrada. A configuração e a autenticação efetivas acontecem externamente no Claude ou ChatGPT e podem depender do plano e de permissões administrativas.

## Requisitos

- Python 3.12 e [uv](https://docs.astral.sh/uv/);
- Node.js 22.12+ e pnpm 11 (gate final: Node.js 24.19.0 e pnpm 11.19.0);
- PostgreSQL 18 para a execução de referência e o gate de integração;
- Microsoft Edge para o E2E local configurado.

## Instalação e migração

```powershell
Copy-Item .env.example backend\.env

Set-Location backend
uv sync --group dev
uv run alembic upgrade head
uv run python ..\scripts\seed_demo.py

Set-Location ..\frontend
pnpm install
```

## Executar

Terminal da API:

```powershell
Set-Location backend
uv run uvicorn app.main:create_app --factory --reload
```

Terminal do frontend:

```powershell
Set-Location frontend
pnpm dev
```

Abra `http://localhost:3000`; a saúde da API fica em `http://localhost:8000/health`. O cadastro MCP por usuário requer login TWR. Para demonstração, use `viewer.demo`, `planner.demo` ou `admin.demo`, todos com a senha sintética `TequalyDemo!2026`. Em ambiente estrito, defina `TWR_AUTH_REQUIRED=true`.

## Inicialização offline no Windows

A entrega preparada para Windows inclui runtimes, dependências, build e banco local. Dê dois cliques em `INICIAR_TWR.bat` para iniciar a API e o frontend sem Codex e abrir `http://127.0.0.1:3000/conexoes-mcp` no Google Chrome. O inicializador evita processos duplicados, aguarda os serviços responderem e grava diagnósticos na pasta `logs/`.

O funcionamento offline depende de manter na mesma pasta os diretórios `.runtime/`, `backend/.venv/`, `backend/.local/`, `frontend/node_modules/` e `frontend/.next/` fornecidos com a entrega.

## MCP

A página `/conexoes-mcp` consome estas rotas autenticadas:

- `GET/POST /mcp-connections`;
- `PATCH/DELETE /mcp-connections/{connection_id}`;
- `POST /mcp-connections/{connection_id}/validate`;
- `GET /mcp-connections/catalog`.

O servidor MCP técnico local permanece disponível por `stdio` e expõe cinco ferramentas determinísticas somente leitura:

```powershell
Set-Location backend
uv run python -m app.mcp_server
```

Consulte `docs/mcp.md` e `docs/ai-tools.md` para o schema, limites e catálogo.

## Verificação

Backend completo e testes focados do cadastro MCP:

```powershell
Set-Location backend
uv run pytest -q
uv run pytest tests/unit/mcp_connections tests/integration/mcp_connections -q
uv run ruff check app tests
uv run mypy app
uv run alembic upgrade head
```

Frontend completo e E2E focado:

```powershell
Set-Location frontend
pnpm test
pnpm exec vitest run features/mcp-connections/mcp-connections-page.test.tsx components/app-shell.test.tsx
pnpm typecheck
pnpm lint
pnpm build
pnpm e2e
pnpm exec playwright test e2e/mcp-connections.spec.ts
```

O Playwright usa o build de produção e recria um SQLite isolado em `frontend/.e2e/`. Para o round-trip PostgreSQL, defina `TWR_TEST_DATABASE_URL` com um banco vazio cujo nome termine em `_test`.

## Funcionalidades entregues

Cadastros e perfis, operações e requisitos, elegibilidade explicável, otimização em três objetivos, seleção e outcomes auditáveis, calibração supervisionada, capacitação, fragilidade, dashboard executivo, importação com preview, exportações seguras, qualidade de dados, autenticação por perfil, cadastro individual de conexões MCP e MCP local somente leitura.

Veja `docs/` para arquitetura, modelo, otimização, UX, roteiro, plano de testes e evidências.
