# Tequaly Workforce Readiness � Master Implementation Roadmap

**Design aprovado:** `docs/superpowers/specs/2026-08-10-twr-product-design.md`  
**Estrat�gia:** fatias verticais, synthetic-first e real-data-ready  
**Execu��o:** inline, com TDD, verifica��o e commits por tarefa

## Stack fixada

- Node.js `>=22.12`; gate final executado com `24.19.0`.
- pnpm `11.x`; ambiente atual `11.16.0`.
- Next.js App Router, React, TypeScript, Tailwind CSS e Playwright, fixados no lockfile criado na Fase 0.
- Python `3.12`.
- FastAPI, Pydantic 2, SQLAlchemy `2.0.x`, Alembic `1.18.x`, psycopg 3, OR-Tools e pytest, fixados em `uv.lock`.
- PostgreSQL `18.x` como banco de desenvolvimento e produ��o.
- SDK MCP Python oficial, somente com stdio local nesta entrega.

## Restri��es globais

- N�o criar entidade `Evidence`.
- N�o integrar com Tequaly Field Intelligence.
- N�o implementar RAG, ML, microservi�os, Redis, Kafka, Kubernetes ou multi-tenant.
- Frontend, cadastro de conex�es e MCP n�o cont�m regras de elegibilidade ou solver.
- Hard constraints nunca s�o relaxadas silenciosamente.
- MCP n�o exp�e ferramentas de escrita nesta entrega.
- A aplica��o n�o possui runtime de modelo ou chave de provedor de IA.
- Dados demo s�o totalmente fict�cios.

## Planos execut�veis

1. [Entrega 1 � N�cleo operacional](superpowers/plans/2026-08-10-twr-core.md)
2. [Entrega 2 � Intelig�ncia operacional](superpowers/plans/2026-08-10-twr-operational-intelligence.md)
3. [Entrega 3 � plano hist�rico substitu�do; n�cleo MCP preservado](superpowers/plans/2026-08-10-twr-ai-mcp.md)
4. [Entrega 4 � Integra��o e qualidade final](superpowers/plans/2026-08-10-twr-integration-quality.md)

## Gates entre entregas

Cada entrega exige:

1. testes unit�rios e de integra��o verdes;
2. lint e typecheck verdes;
3. build de produ��o verde;
4. migra��o limpa e seed idempotente quando houver mudan�a de dados;
5. atualiza��o da documenta��o e `docs/implementation-decisions.md`;
6. commit independente e revis�o do diff.

## Resultado incremental

- Entrega 1: opera��o criada, elegibilidade calculada e tr�s cen�rios compar�veis.
- Entrega 2: treinamento, fragilidade, auditoria, outcome e recalibra��o.
- Entrega 3: cinco consultas somente leitura expostas via MCP local.
- Entrega 4: importa��o/exporta��o, autentica��o, E2E, desempenho e documenta��o final.

