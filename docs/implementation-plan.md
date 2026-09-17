# Tequaly Workforce Readiness — Master Implementation Roadmap

**Design aprovado:** `docs/superpowers/specs/2026-08-10-twr-product-design.md`  
**Estratégia:** fatias verticais, synthetic-first e real-data-ready  
**Execução:** inline, com TDD, verificação e commits por tarefa

## Stack fixada

- Node.js `>=22.12`; gate final executado com `24.19.0`.
- pnpm `11.x`; ambiente atual `11.16.0`.
- Next.js App Router, React, TypeScript, Tailwind CSS e Playwright, fixados no lockfile criado na Fase 0.
- Python `3.12`.
- FastAPI, Pydantic 2, SQLAlchemy `2.0.x`, Alembic `1.18.x`, psycopg 3, OR-Tools e pytest, fixados em `uv.lock`.
- PostgreSQL `18.x` como banco de desenvolvimento e produção.
- SDK MCP Python oficial, somente com stdio local nesta entrega.

## Restrições globais

- Não criar entidade `Evidence`.
- Não integrar com Tequaly Field Intelligence.
- Não implementar RAG, ML, microserviços, Redis, Kafka, Kubernetes ou multi-tenant.
- Frontend, cadastro de conexões e MCP não contêm regras de elegibilidade ou solver.
- Hard constraints nunca são relaxadas silenciosamente.
- MCP não expõe ferramentas de escrita nesta entrega.
- A aplicação não possui runtime de modelo ou chave de provedor de IA.
- Dados demo são totalmente fictícios.

## Planos executáveis

1. [Entrega 1 — Núcleo operacional](superpowers/plans/2026-08-10-twr-core.md)
2. [Entrega 2 — Inteligência operacional](superpowers/plans/2026-08-10-twr-operational-intelligence.md)
3. [Entrega 3 — plano histórico substituído; núcleo MCP preservado](superpowers/plans/2026-08-10-twr-ai-mcp.md)
4. [Entrega 4 — Integração e qualidade final](superpowers/plans/2026-08-10-twr-integration-quality.md)

## Gates entre entregas

Cada entrega exige:

1. testes unitários e de integração verdes;
2. lint e typecheck verdes;
3. build de produção verde;
4. migração limpa e seed idempotente quando houver mudança de dados;
5. atualização da documentação e `docs/implementation-decisions.md`;
6. commit independente e revisão do diff.

## Resultado incremental

- Entrega 1: operação criada, elegibilidade calculada e três cenários comparáveis.
- Entrega 2: treinamento, fragilidade, auditoria, outcome e recalibração.
- Entrega 3: cinco consultas somente leitura expostas via MCP local.
- Entrega 4: importação/exportação, autenticação, E2E, desempenho e documentação final.

