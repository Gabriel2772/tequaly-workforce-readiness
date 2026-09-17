# Decis�es de implementa��o

## ID-001 � Mon�lito modular

Um FastAPI, um Next.js e um banco. Mant�m regras, transa��es e auditoria coesas; m�dulos compartilham release.

## ID-002 � Synthetic-first, real-data-ready

O core usa dados fict�cios determin�sticos porque a disponibilidade dos dados Tequaly � incerta. A troca por dados reais exige confirma��o de schema, aliases, LGPD, qualidade e regras; n�o exige reescrever elegibilidade/solver.

## ID-003 � Seed principal de 2.200 pessoas

A escala de demonstra��o � 2.200, com fixture r�pida menor e benchmark de 3.000. Ela � uma hip�tese operacional conservadora baseada no contexto pesquisado, n�o uma contagem oficial atual.

## ID-004 � 90 cargos can�nicos e 130 aliases

T�tulos de origem n�o s�o usados diretamente como fun��o operacional. Essa normaliza��o reduz fragmenta��o, mas precisa de governan�a e valida��o com RH/opera��es antes da carga real.

## ID-005 � 120 itens de prontid�o

O seed distribui 72 qualifica��es, 24 autoriza��es e 24 treinamentos. Quantidade e equival�ncias s�o simuladas; cat�logo real e validade devem vir de fontes Tequaly controladas.

## ID-006 � PostgreSQL 18; SQLite para testes locais

PostgreSQL 18 � a refer�ncia. Centavos e minutos inteiros evitam ambiguidade no CP-SAT. SQLite torna testes e E2E reproduz�veis, mas n�o substitui o gate PostgreSQL.

## ID-007 � Sem broker no core

Runs s�o persistidos e executados no processo da API com timeout. Menos servi�os simplificam o PoC; rein�cio pode interromper trabalho em andamento.

## ID-008 � Elegibilidade antes do solver

O solver n�o interpreta qualifica��es. Ele recebe candidatos previamente classificados, o que separa explicabilidade de busca combinat�ria e permite testar ambas isoladamente.

## ID-009 � Objetivos lexicogr�ficos sequenciais

Cada prioridade � resolvida e fixada antes da pr�xima. Pesos arbitr�rios foram rejeitados porque ocultariam trade-offs e poderiam inverter prioridades de neg�cio.

## ID-010 � Core sem LLM, MCP ou RAG

O n�cleo determin�stico n�o depende dessas integra��es. MCP foi acrescentado depois como adaptador opcional somente leitura; nenhuma decis�o cr�tica depende de modelo generativo.

## ID-011 � Playwright contra build de produ��o

O gate E2E migra e semeia SQLite isolado, inicia a API e executa o build Next no Microsoft Edge instalado. Isso evita o custo/flutua��o do primeiro compile do servidor de desenvolvimento.

## ID-012 � Fragilidade determin�stica e an�lise pendente expl�cita

Severidade deriva de regras version�veis sobre cobertura, redund�ncia, vencimento, aloca��o concorrente e turmas. Opera��o sem elegibilidade conclu�da aparece como an�lise pendente; zero n�o � usado para inventar risco cr�tico.

## ID-013 � Calibra��o robusta e supervisionada

Sugest�es usam mediana e IQR com m�nimo de cinco amostras compar�veis. Valores extremos n�o s�o removidos silenciosamente e nenhuma sugest�o � aplicada sem confirma��o humana e nova vers�o audit�vel.

## ID-014 � Hist�rico sint�tico claramente identificado

Cinco outcomes no seed tornam a calibra��o demonstr�vel, inclusive com um outlier deliberado. Autor, justificativa e documenta��o declaram a origem sint�tica; esses dados n�o podem ser apresentados como hist�rico Tequaly.

## ID-015 � Escritas do navegador com CORS restrito

Auditoria e calibra��o usam chamadas diretas � API. O backend aceita preflight apenas da origem configurada, com m�todos e cabe�alhos expl�citos. A rota est�tica `/health` evita que o gate E2E consulte e bloqueie o banco antes da migra��o.

## ID-016 � Preview persistido, arquivo original descartado

Importa��es guardam hash, contrato, mapeamento, dados normalizados e relat�rio por 30 minutos. O arquivo enviado n�o vira acervo documental nem entidade `Evidence`. Isso permite confirma��o e auditoria sem ampliar o produto para gest�o de documentos.

## ID-017 � Planilha sem f�rmula na entrada e texto escapado na sa�da

XLSX com f�rmula ou macro � recusado porque a carga deve transportar dados, n�o execu��o. Exporta��es escapam prefixos interpret�veis por planilhas e excluem segredos e custo individual.

## ID-018 � Higiene de dados como fun��o operacional

Completude e pend�ncias aparecem antes da importa��o. Cobertura calculada sobre base incompleta pode ser enganosa; por isso a interface separa qualidade cadastral de prontid�o e mant�m a origem sint�tica vis�vel.

## ID-019 � Sess�o assinada com modo local expl�cito

Escritas protegidas deixam de confiar em cabe�alhos quando `TWR_AUTH_REQUIRED=true`. A sess�o usa cookie `HttpOnly`, assinatura HMAC, expira��o curta, revalida��o do usu�rio ativo e perfis `viewer`, `planner` e `admin`. O fallback por cabe�alhos permanece somente para execu��o local e compatibilidade dos testes; SSO/OIDC corporativo fica como integra��o de implanta��o, n�o como depend�ncia do core.

## ID-020 � MCP estritamente somente leitura

Foram entregues cinco consultas no registro MCP. Simula��o, solver, sele��o, outcome, calibra��o e qualquer escrita ficaram fora do cat�logo: exigem contexto humano, autoriza��o e trilha de auditoria pr�prios. O transporte MCP do TWR � apenas stdio local; uma superf�cie HTTP hospedada seria complexidade e risco sem necessidade demonstrada.

## ID-021 � Cadastro individual n�o executa o endpoint

Cada conex�o guarda somente metadados do usu�rio autenticado. A valida��o � estrutural e n�o acessa rede, evitando SSRF e alega��es incorretas de disponibilidade. Configura��o e eventual autentica��o ocorrem externamente no Claude ou ChatGPT.
