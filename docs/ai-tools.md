# Catálogo determinístico de ferramentas MCP

> Status: implementado como catálogo local somente leitura. Não existe runtime de modelo, chat interno ou configuração de chave de provedor de IA.

## Contrato

`app.mcp.tools` contém um `ToolRegistry` tipado. Cada ferramenta possui nome estável, descrição, schema de entrada com campos extras proibidos e efeito `read`. Argumentos inválidos e ferramentas desconhecidas são recusados antes de alcançar os serviços.

## Ferramentas entregues

1. `get_readiness_overview`: indicadores executivos por horizonte;
2. `get_operation`: operação, demandas e requisitos por identificador;
3. `get_employee_profile`: perfil profissional sem custos individuais;
4. `get_operational_fragility`: cobertura e fragilidade explicável por horizonte;
5. `get_decision_run`: cenário calculado e evidências auditáveis.

## Limites deliberados

Não foram criadas ferramentas de simulação, solver, seleção, calibração, importação ou escrita. Otimização, escolha humana, registro de resultado e aplicação de calibração permanecem nos fluxos web autenticados e auditáveis.

O catálogo é consumido pelo servidor MCP local por `stdio` e pela rota autenticada `GET /mcp-connections/catalog`, que apenas descreve as ferramentas. A página de conexões não executa ferramentas nem envia dados a Claude ou ChatGPT.
