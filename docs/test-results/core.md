# Evidências do gate do core

Data: 2026-08-11

Branch: `feat/twr-core`

Baseline funcional: `88676ce`

## Ambiente

- Windows 10 `10.0.19045`;
- Intel Celeron 3865U 1.80 GHz, 3,9 GB RAM;
- Python 3.12.13, FastAPI 0.141.1, SQLAlchemy 2.0.51, Alembic 1.18.5;
- OR-Tools 9.15.6755;
- Node.js 24.14.0, pnpm 11.16.0, Next.js 16.3.0;
- Microsoft Edge do sistema para Playwright.

## Banco limpo e idempotência

Executado em SQLite novo, a partir do diretório `backend`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe ..\scripts\seed_demo.py --employees 2200
.\.venv\Scripts\python.exe ..\scripts\seed_demo.py --employees 2200
```

Resultado: migrações `0001` a `0005` aplicadas; ambos os seeds retornaram exatamente 2.200 colaboradores, 90 cargos, 130 aliases, 72 qualificações, 24 autorizações, 24 treinamentos, 8 operações, 16 demandas e 16 requisitos. Tempo conjunto: 37,95 s. A segunda execução não duplicou registros.

Smoke via `TestClient`: `PASS`, com `/health=200`, 2.200 colaboradores, 8 operações e 72 qualificações.

## Backend

| Comando | Resultado |
|---|---|
| `python -m pytest` | 76 passed, 1 skipped, 80,48 s |
| `python -m pytest -q tests/performance/test_candidate_pool.py --durations=1` | 1 passed; chamada 9,26 s; total 13,43 s |
| `python -m ruff check .` | sem achados |
| `python -m mypy app` | sem achados em 48 arquivos |

O teste de performance usa 3.000 pessoas e também verifica internamente elegibilidade menor que 15 s e cada um dos três cenários menor que 30 s.

O único skip foi `test_postgresql_upgrade_downgrade_upgrade_round_trip`, condicionado por `TWR_TEST_DATABASE_URL`.

## Frontend

| Comando | Resultado |
|---|---|
| `pnpm test` | 7 arquivos, 8 testes, todos passaram; 77,90 s |
| `pnpm typecheck` | exit 0 |
| `pnpm lint` | exit 0 |
| `next build --webpack` | sucesso; compile 51 s, TypeScript 25,9 s, 3 páginas estáticas; `/planejador` dinâmico |
| `pnpm e2e` | 1 passed; fluxo 39,4 s; execução total 2,1 min |

O E2E criou SQLite limpo com 300 pessoas, aplicou as cinco migrações, executou elegibilidade e gerou `MIN_COST`, `FASTEST_READY` e `MAX_INTERNAL`; todos os POSTs retornaram 201 e os cenários persistidos foram reconsultados.

## Limitações verificadas

- Não há PostgreSQL, `psql` ou Docker disponíveis nesta máquina. Portanto, o round-trip PostgreSQL e o p95 de consultas no banco alvo permanecem pendentes e não são marcados como aprovados.
- SQLite foi usado somente para reprodutibilidade local/testes; PostgreSQL 18 continua sendo o baseline de implantação.
- Dados são sintéticos. Quantidade real de pessoas, cargos, aliases, requisitos e validade precisam de confirmação oficial Tequaly.
- Importação real, SSO, aprovação/outcome, fragilidade, MCP e RAG estavam fora do baseline de core medido neste relatório histórico.
