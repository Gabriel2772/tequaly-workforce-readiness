# Arquitetura implementada

## Limite do sistema

O Tequaly Workforce Readiness (TWR) � uma aplica��o web interna independente. O n�cleo de regras n�o usa LLM, RAG nem componentes do Tequaly Field Intelligence. O MCP local existe como adaptador t�cnico somente leitura; a �rea web de conex�es guarda apenas metadados individuais e n�o executa servidores remotos.

## Topologia

```text
Navegador
   |
   v
Next.js 16 (Server Components + Server Actions)
   |
   v
FastAPI (mon�lito modular)
   |-----------------------|--------------------|
   v                       v                    v
SQLAlchemy/Alembic     Regras determin�sticas   MCP local READ
   |                       |                    |
   v                       v                    v
PostgreSQL 18          OR-Tools CP-SAT      ToolRegistry tipado
```

PostgreSQL 18 � o banco de refer�ncia. SQLite � suportado pelos testes, pelo gate local e pelo E2E isolado; ele n�o substitui o round-trip obrigat�rio em PostgreSQL antes de produ��o.

## M�dulos entregues

- `core`, `db` e `auth`: configura��o, sess�o, metadados e ator m�nimo para escrita/auditoria;
- `workforce`: colaboradores, cargos e aliases, qualifica��es, autoriza��es, disponibilidade, aloca��es, custos, compet�ncias, restri��es e cat�logo de capacita��o;
- `operations`: opera��o, demanda por cargo, cargos compat�veis e requisitos;
- `eligibility`: pr�-filtro no banco, dez fam�lias de regras puras, motivos explic�veis e runs persistidos;
- `optimization`: modelo CP-SAT comum, restri��es r�gidas, diagn�stico de inviabilidade e tr�s objetivos lexicogr�ficos;
- `decisions`: snapshot de entrada, assignments, treinamentos, m�tricas e eventos de auditoria;
- `dashboard`, `fragility`, `training`, `imports`, `exports` e `data_quality`: intelig�ncia operacional, capacita��o e integra��o governada;
- `mcp.tools` e `mcp_server`: registro tipado e cinco consultas locais somente leitura;
- `mcp_connections`: CRUD autenticado de metadados MCP por usu�rio, valida��o estrutural e cat�logo;
- `demo`: gerador e seed sint�ticos determin�sticos.

SSO/OIDC, transporte MCP remoto, RAG e ferramentas de escrita por IA n�o fazem parte desta entrega.

## Contratos HTTP centrais

- `GET/POST/PATCH /employees` e subrecursos do perfil;
- `GET/POST /qualifications` e `GET /roles`;
- `GET/POST/PATCH /operations` com demandas e requisitos;
- `POST /operations/{id}/eligibility/run`;
- `GET /operations/{id}/eligibility/latest`;
- `POST /operations/{id}/optimize`;
- `GET /operations/{id}/scenarios`;
- `GET /dashboard/overview`, `GET /fragility` e rotas de capacita��o;
- `POST /imports/preview`, confirma��o controlada e exporta��es;
- `GET/POST /mcp-connections`, muta��es por ID, valida��o e cat�logo;
- `GET /health`.

Em modo estrito, escritas exigem sess�o assinada e perfil `planner` ou `admin`; o fallback por cabe�alho existe apenas no desenvolvimento local. Os servi�os persistem fatos e snapshots antes de devolver a decis�o.

## Depend�ncias e execu��o

Rotas chamam servi�os de aplica��o; regras de elegibilidade e o modelo CP-SAT n�o importam FastAPI. Reposit�rios e servi�os usam SQLAlchemy. Opera��es longas rodam no processo da API com limite expl�cito; n�o h� Redis, broker ou worker no core.
