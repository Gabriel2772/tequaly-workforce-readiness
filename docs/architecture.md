# Arquitetura implementada

## Limite do sistema

O Tequaly Workforce Readiness (TWR) é uma aplicação web interna independente. O núcleo de regras não usa LLM, RAG nem componentes do Tequaly Field Intelligence. O MCP local existe como adaptador técnico somente leitura; a área web de conexões guarda apenas metadados individuais e não executa servidores remotos.

## Topologia

```text
Navegador
   |
   v
Next.js 16 (Server Components + Server Actions)
   |
   v
FastAPI (monólito modular)
   |-----------------------|--------------------|
   v                       v                    v
SQLAlchemy/Alembic     Regras determinísticas   MCP local READ
   |                       |                    |
   v                       v                    v
PostgreSQL 18          OR-Tools CP-SAT      ToolRegistry tipado
```

PostgreSQL 18 é o banco de referência. SQLite é suportado pelos testes, pelo gate local e pelo E2E isolado; ele não substitui o round-trip obrigatório em PostgreSQL antes de produção.

## Módulos entregues

- `core`, `db` e `auth`: configuração, sessão, metadados e ator mínimo para escrita/auditoria;
- `workforce`: colaboradores, cargos e aliases, qualificações, autorizações, disponibilidade, alocações, custos, competências, restrições e catálogo de capacitação;
- `operations`: operação, demanda por cargo, cargos compatíveis e requisitos;
- `eligibility`: pré-filtro no banco, dez famílias de regras puras, motivos explicáveis e runs persistidos;
- `optimization`: modelo CP-SAT comum, restrições rígidas, diagnóstico de inviabilidade e três objetivos lexicográficos;
- `decisions`: snapshot de entrada, assignments, treinamentos, métricas e eventos de auditoria;
- `dashboard`, `fragility`, `training`, `imports`, `exports` e `data_quality`: inteligência operacional, capacitação e integração governada;
- `mcp.tools` e `mcp_server`: registro tipado e cinco consultas locais somente leitura;
- `mcp_connections`: CRUD autenticado de metadados MCP por usuário, validação estrutural e catálogo;
- `demo`: gerador e seed sintéticos determinísticos.

SSO/OIDC, transporte MCP remoto, RAG e ferramentas de escrita por IA não fazem parte desta entrega.

## Contratos HTTP centrais

- `GET/POST/PATCH /employees` e subrecursos do perfil;
- `GET/POST /qualifications` e `GET /roles`;
- `GET/POST/PATCH /operations` com demandas e requisitos;
- `POST /operations/{id}/eligibility/run`;
- `GET /operations/{id}/eligibility/latest`;
- `POST /operations/{id}/optimize`;
- `GET /operations/{id}/scenarios`;
- `GET /dashboard/overview`, `GET /fragility` e rotas de capacitação;
- `POST /imports/preview`, confirmação controlada e exportações;
- `GET/POST /mcp-connections`, mutações por ID, validação e catálogo;
- `GET /health`.

Em modo estrito, escritas exigem sessão assinada e perfil `planner` ou `admin`; o fallback por cabeçalho existe apenas no desenvolvimento local. Os serviços persistem fatos e snapshots antes de devolver a decisão.

## Dependências e execução

Rotas chamam serviços de aplicação; regras de elegibilidade e o modelo CP-SAT não importam FastAPI. Repositórios e serviços usam SQLAlchemy. Operações longas rodam no processo da API com limite explícito; não há Redis, broker ou worker no core.
