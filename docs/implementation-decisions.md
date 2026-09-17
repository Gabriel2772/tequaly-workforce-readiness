# Decisões de implementação

## ID-001 — Monólito modular

Um FastAPI, um Next.js e um banco. Mantém regras, transações e auditoria coesas; módulos compartilham release.

## ID-002 — Synthetic-first, real-data-ready

O core usa dados fictícios determinísticos porque a disponibilidade dos dados Tequaly é incerta. A troca por dados reais exige confirmação de schema, aliases, LGPD, qualidade e regras; não exige reescrever elegibilidade/solver.

## ID-003 — Seed principal de 2.200 pessoas

A escala de demonstração é 2.200, com fixture rápida menor e benchmark de 3.000. Ela é uma hipótese operacional conservadora baseada no contexto pesquisado, não uma contagem oficial atual.

## ID-004 — 90 cargos canônicos e 130 aliases

Títulos de origem não são usados diretamente como função operacional. Essa normalização reduz fragmentação, mas precisa de governança e validação com RH/operações antes da carga real.

## ID-005 — 120 itens de prontidão

O seed distribui 72 qualificações, 24 autorizações e 24 treinamentos. Quantidade e equivalências são simuladas; catálogo real e validade devem vir de fontes Tequaly controladas.

## ID-006 — PostgreSQL 18; SQLite para testes locais

PostgreSQL 18 é a referência. Centavos e minutos inteiros evitam ambiguidade no CP-SAT. SQLite torna testes e E2E reproduzíveis, mas não substitui o gate PostgreSQL.

## ID-007 — Sem broker no core

Runs são persistidos e executados no processo da API com timeout. Menos serviços simplificam o PoC; reinício pode interromper trabalho em andamento.

## ID-008 — Elegibilidade antes do solver

O solver não interpreta qualificações. Ele recebe candidatos previamente classificados, o que separa explicabilidade de busca combinatória e permite testar ambas isoladamente.

## ID-009 — Objetivos lexicográficos sequenciais

Cada prioridade é resolvida e fixada antes da próxima. Pesos arbitrários foram rejeitados porque ocultariam trade-offs e poderiam inverter prioridades de negócio.

## ID-010 — Core sem LLM, MCP ou RAG

O núcleo determinístico não depende dessas integrações. MCP foi acrescentado depois como adaptador opcional somente leitura; nenhuma decisão crítica depende de modelo generativo.

## ID-011 — Playwright contra build de produção

O gate E2E migra e semeia SQLite isolado, inicia a API e executa o build Next no Microsoft Edge instalado. Isso evita o custo/flutuação do primeiro compile do servidor de desenvolvimento.

## ID-012 — Fragilidade determinística e análise pendente explícita

Severidade deriva de regras versionáveis sobre cobertura, redundância, vencimento, alocação concorrente e turmas. Operação sem elegibilidade concluída aparece como análise pendente; zero não é usado para inventar risco crítico.

## ID-013 — Calibração robusta e supervisionada

Sugestões usam mediana e IQR com mínimo de cinco amostras comparáveis. Valores extremos não são removidos silenciosamente e nenhuma sugestão é aplicada sem confirmação humana e nova versão auditável.

## ID-014 — Histórico sintético claramente identificado

Cinco outcomes no seed tornam a calibração demonstrável, inclusive com um outlier deliberado. Autor, justificativa e documentação declaram a origem sintética; esses dados não podem ser apresentados como histórico Tequaly.

## ID-015 — Escritas do navegador com CORS restrito

Auditoria e calibração usam chamadas diretas à API. O backend aceita preflight apenas da origem configurada, com métodos e cabeçalhos explícitos. A rota estática `/health` evita que o gate E2E consulte e bloqueie o banco antes da migração.

## ID-016 — Preview persistido, arquivo original descartado

Importações guardam hash, contrato, mapeamento, dados normalizados e relatório por 30 minutos. O arquivo enviado não vira acervo documental nem entidade `Evidence`. Isso permite confirmação e auditoria sem ampliar o produto para gestão de documentos.

## ID-017 — Planilha sem fórmula na entrada e texto escapado na saída

XLSX com fórmula ou macro é recusado porque a carga deve transportar dados, não execução. Exportações escapam prefixos interpretáveis por planilhas e excluem segredos e custo individual.

## ID-018 — Higiene de dados como função operacional

Completude e pendências aparecem antes da importação. Cobertura calculada sobre base incompleta pode ser enganosa; por isso a interface separa qualidade cadastral de prontidão e mantém a origem sintética visível.

## ID-019 — Sessão assinada com modo local explícito

Escritas protegidas deixam de confiar em cabeçalhos quando `TWR_AUTH_REQUIRED=true`. A sessão usa cookie `HttpOnly`, assinatura HMAC, expiração curta, revalidação do usuário ativo e perfis `viewer`, `planner` e `admin`. O fallback por cabeçalhos permanece somente para execução local e compatibilidade dos testes; SSO/OIDC corporativo fica como integração de implantação, não como dependência do core.

## ID-020 — MCP estritamente somente leitura

Foram entregues cinco consultas no registro MCP. Simulação, solver, seleção, outcome, calibração e qualquer escrita ficaram fora do catálogo: exigem contexto humano, autorização e trilha de auditoria próprios. O transporte MCP do TWR é apenas stdio local; uma superfície HTTP hospedada seria complexidade e risco sem necessidade demonstrada.

## ID-021 — Cadastro individual não executa o endpoint

Cada conexão guarda somente metadados do usuário autenticado. A validação é estrutural e não acessa rede, evitando SSRF e alegações incorretas de disponibilidade. Configuração e eventual autenticação ocorrem externamente no Claude ou ChatGPT.
