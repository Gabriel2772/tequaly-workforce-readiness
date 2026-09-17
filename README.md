# Tequaly Workforce Readiness

Aplica��o audit�vel para cadastrar for�a de trabalho, avaliar prontid�o e montar equipes operacionais com regras determin�sticas e OR-Tools CP-SAT. O produto n�o cont�m chat interno, execu��o de modelos ou integra��o com provedores de IA e n�o solicita chaves OpenAI ou Anthropic.

## Escopo demonstr�vel

O seed principal usa 2.200 colaboradores; o benchmark usa 3.000. O cat�logo sint�tico cont�m 12 fam�lias, 90 cargos can�nicos, 130 aliases, 72 qualifica��es, 24 autoriza��es, 24 treinamentos e 8 opera��es. Esses n�meros s�o hip�teses de demonstra��o, n�o dados oficiais da Tequaly. A integra��o produtiva ainda exige fontes governadas, mapeamento, valida��o de regras, LGPD e aceite de RH/opera��es.

Al�m do n�cleo operacional, usu�rios autenticados podem organizar metadados das pr�prias conex�es MCP em `/conexoes-mcp`. O TWR guarda apenas nome, destino, endpoint, transporte, observa��o, estado e timestamps; n�o guarda tokens, senhas, headers ou outros segredos. A valida��o � somente estrutural e nunca chama a URL cadastrada. A configura��o e a autentica��o efetivas acontecem externamente no Claude ou ChatGPT e podem depender do plano e de permiss�es administrativas.

## Requisitos

- Python 3.12 e [uv](https://docs.astral.sh/uv/);
- Node.js 22.12+ e pnpm 11 (gate final: Node.js 24.19.0 e pnpm 11.19.0);
- PostgreSQL 18 para a execu��o de refer�ncia e o gate de integra��o;
- Microsoft Edge para o E2E local configurado.

## Instala��o e migra��o

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

Abra `http://localhost:3000`; a sa�de da API fica em `http://localhost:8000/health`. O cadastro MCP por usu�rio requer login TWR. Para demonstra��o, use `viewer.demo`, `planner.demo` ou `admin.demo`, todos com a senha sint�tica `TequalyDemo!2026`. Em ambiente estrito, defina `TWR_AUTH_REQUIRED=true`.

## Inicializa��o offline no Windows

A entrega preparada para Windows inclui runtimes, depend�ncias, build e banco local. D� dois cliques em `INICIAR_TWR.bat` para iniciar a API e o frontend sem Codex e abrir `http://127.0.0.1:3000/conexoes-mcp` no Google Chrome. O inicializador evita processos duplicados, aguarda os servi�os responderem e grava diagn�sticos na pasta `logs/`.

O funcionamento offline depende de manter na mesma pasta os diret�rios `.runtime/`, `backend/.venv/`, `backend/.local/`, `frontend/node_modules/` e `frontend/.next/` fornecidos com a entrega.

## MCP

A p�gina `/conexoes-mcp` consome estas rotas autenticadas:

- `GET/POST /mcp-connections`;
- `PATCH/DELETE /mcp-connections/{connection_id}`;
- `POST /mcp-connections/{connection_id}/validate`;
- `GET /mcp-connections/catalog`.

O servidor MCP t�cnico local permanece dispon�vel por `stdio` e exp�e cinco ferramentas determin�sticas somente leitura:

```powershell
Set-Location backend
uv run python -m app.mcp_server
```

Consulte `docs/mcp.md` e `docs/ai-tools.md` para o schema, limites e cat�logo.

## Verifica��o

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

O Playwright usa o build de produ��o e recria um SQLite isolado em `frontend/.e2e/`. Para o round-trip PostgreSQL, defina `TWR_TEST_DATABASE_URL` com um banco vazio cujo nome termine em `_test`.

## Funcionalidades entregues

Cadastros e perfis, opera��es e requisitos, elegibilidade explic�vel, otimiza��o em tr�s objetivos, sele��o e outcomes audit�veis, calibra��o supervisionada, capacita��o, fragilidade, dashboard executivo, importa��o com preview, exporta��es seguras, qualidade de dados, autentica��o por perfil, cadastro individual de conex�es MCP e MCP local somente leitura.

Veja `docs/` para arquitetura, modelo, otimiza��o, UX, roteiro, plano de testes e evid�ncias.
