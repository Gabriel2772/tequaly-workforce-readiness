# Evidências — cadastro MCP por usuário e MCP local

Data: 26 de agosto de 2026.

## TDD focado

- query keys legítimas: RED com 3 falsos positivos (`monkey`, `author`, `hockey`); GREEN `35 passed`;
- integridade: RED por detector ainda ausente; GREEN `23 passed`, cobrindo formatos PostgreSQL/SQLite e propagação de erro não relacionado;
- load/retry e filtro ativo/inativo: mutação RED detectada; restauração GREEN `10 passed`;
- boundary de rota e fechamento por pathname: RED `2 failed, 3 passed`; GREEN `5 passed`;
- E2E inicial: RED por accessible names ambíguos/ocultos; alinhamento usa nomes estáveis e login real.

## Cobertura

- CRUD e isolamento por sessão entre dois usuários;
- rejeição de campos extras, owner e credenciais;
- validação de URL sem acesso de rede;
- auditoria sem URL/notas;
- catálogo exato de cinco ferramentas somente leitura e equivalência do MCP stdio;
- estados da página, erro/retry, filtros, cópia, ativação e exclusão;
- sidebar desktop/compacta/móvel, SVGs rotulados e active state correto;
- Playwright: login `planner.demo`, criar, validar, desativar, ativar, excluir e navegação móvel.

## Gate final

| Comando | Resultado |
|---|---|
| `uv run pytest -q` | `204 passed, 1 skipped` (skip: PostgreSQL round-trip sem `TWR_TEST_DATABASE_URL`) |
| `uv run ruff check app tests` | passou (`All checks passed!`) |
| `uv run mypy app` | passou (105 source files, sem issues) |
| `pnpm test` | passou (23 arquivos, 43 testes) |
| `pnpm typecheck` | passou |
| `pnpm lint` | passou |
| `pnpm build` | passou; build lista `/conexoes-mcp` |
| `pnpm e2e` | 6 passaram em 5,6 min; migrações `0001..0010` e seed de 300 |

A cadeia Alembic passa pela ponte `0010_mcp_oauth`, e o teste de migrações cobre o upgrade legado.

O PostgreSQL round-trip real pode aparecer como único skip quando `TWR_TEST_DATABASE_URL` não estiver configurada. Nenhuma chave ou segredo foi usado ou registrado.
