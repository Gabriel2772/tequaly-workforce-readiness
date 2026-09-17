# Cat�logo determin�stico de ferramentas MCP

> Status: implementado como cat�logo local somente leitura. N�o existe runtime de modelo, chat interno ou configura��o de chave de provedor de IA.

## Contrato

`app.mcp.tools` cont�m um `ToolRegistry` tipado. Cada ferramenta possui nome est�vel, descri��o, schema de entrada com campos extras proibidos e efeito `read`. Argumentos inv�lidos e ferramentas desconhecidas s�o recusados antes de alcan�ar os servi�os.

## Ferramentas entregues

1. `get_readiness_overview`: indicadores executivos por horizonte;
2. `get_operation`: opera��o, demandas e requisitos por identificador;
3. `get_employee_profile`: perfil profissional sem custos individuais;
4. `get_operational_fragility`: cobertura e fragilidade explic�vel por horizonte;
5. `get_decision_run`: cen�rio calculado e evid�ncias audit�veis.

## Limites deliberados

N�o foram criadas ferramentas de simula��o, solver, sele��o, calibra��o, importa��o ou escrita. Otimiza��o, escolha humana, registro de resultado e aplica��o de calibra��o permanecem nos fluxos web autenticados e audit�veis.

O cat�logo � consumido pelo servidor MCP local por `stdio` e pela rota autenticada `GET /mcp-connections/catalog`, que apenas descreve as ferramentas. A p�gina de conex�es n�o executa ferramentas nem envia dados a Claude ou ChatGPT.
