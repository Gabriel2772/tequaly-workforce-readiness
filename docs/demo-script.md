# Roteiro de demonstra��o

## Prepara��o

1. Migre um banco vazio at� `head`.
2. Execute `scripts/seed_demo.py` com 2.200 colaboradores.
3. Inicie FastAPI na porta 8000 e Next.js na porta 3000.
4. Entre como `planner.demo` com a senha sint�tica `TequalyDemo!2026`.

## Fluxo

1. Abra Vis�o geral e declare que as contagens s�o sint�ticas.
2. Em Colaboradores e Qualifica��es, mostre perfil e cat�logo can�nico.
3. Em Opera��es, consulte demanda, requisitos e prazo de mobiliza��o.
4. No Planejador, recalcule elegibilidade e compare eleg�veis, trein�veis e ineleg�veis.
5. Gere `MIN_COST`, `FASTEST_READY` e `MAX_INTERNAL`; compare custo, prontid�o, uso interno e capacita��o.
6. Em Risco e cobertura, explique cobertura, redund�ncia, vencimentos e conflitos.
7. Em Auditoria, selecione um cen�rio, registre outcome e mostre a calibra��o supervisionada.
8. Em Configura��es, mostre qualidade, preview separado do commit e exporta��es seguras.
9. Abra Conex�es MCP. Explique que a �rea organiza metadados por usu�rio e n�o cont�m conversa ou execu��o de modelo.
10. Cadastre `MCP Planejamento`, destino Claude, endpoint `https://mcp.example.com/mcp` e transporte Streamable HTTP.
11. Valide a configura��o e destaque que o resultado � estrutural e n�o acessa a rede.
12. Copie a configura��o sem segredos, desative, reative e exclua o registro.
13. Explique que a inclus�o no Claude ou ChatGPT acontece externamente e pode depender do plano ou de um administrador.
14. Em viewport m�vel, abra a gaveta, navegue para Conex�es MCP e confirme seu fechamento.
15. Opcionalmente, execute `uv run python -m app.mcp_server` em `backend` e liste as cinco ferramentas locais somente leitura.

## Fora desta demonstra��o

Dados reais, SSO corporativo, implanta��o, MCP remoto hospedado e integra��es com sistemas oficiais pertencem �s fases seguintes. N�o apresente o seed, custos ou par�metros como fatos da Tequaly. Nenhuma chave OpenAI ou Anthropic � necess�ria.
