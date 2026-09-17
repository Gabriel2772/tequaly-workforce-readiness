# Roteiro de demonstração

## Preparação

1. Migre um banco vazio até `head`.
2. Execute `scripts/seed_demo.py` com 2.200 colaboradores.
3. Inicie FastAPI na porta 8000 e Next.js na porta 3000.
4. Entre como `planner.demo` com a senha sintética `TequalyDemo!2026`.

## Fluxo

1. Abra Visão geral e declare que as contagens são sintéticas.
2. Em Colaboradores e Qualificações, mostre perfil e catálogo canônico.
3. Em Operações, consulte demanda, requisitos e prazo de mobilização.
4. No Planejador, recalcule elegibilidade e compare elegíveis, treináveis e inelegíveis.
5. Gere `MIN_COST`, `FASTEST_READY` e `MAX_INTERNAL`; compare custo, prontidão, uso interno e capacitação.
6. Em Risco e cobertura, explique cobertura, redundância, vencimentos e conflitos.
7. Em Auditoria, selecione um cenário, registre outcome e mostre a calibração supervisionada.
8. Em Configurações, mostre qualidade, preview separado do commit e exportações seguras.
9. Abra Conexões MCP. Explique que a área organiza metadados por usuário e não contém conversa ou execução de modelo.
10. Cadastre `MCP Planejamento`, destino Claude, endpoint `https://mcp.example.com/mcp` e transporte Streamable HTTP.
11. Valide a configuração e destaque que o resultado é estrutural e não acessa a rede.
12. Copie a configuração sem segredos, desative, reative e exclua o registro.
13. Explique que a inclusão no Claude ou ChatGPT acontece externamente e pode depender do plano ou de um administrador.
14. Em viewport móvel, abra a gaveta, navegue para Conexões MCP e confirme seu fechamento.
15. Opcionalmente, execute `uv run python -m app.mcp_server` em `backend` e liste as cinco ferramentas locais somente leitura.

## Fora desta demonstração

Dados reais, SSO corporativo, implantação, MCP remoto hospedado e integrações com sistemas oficiais pertencem às fases seguintes. Não apresente o seed, custos ou parâmetros como fatos da Tequaly. Nenhuma chave OpenAI ou Anthropic é necessária.
