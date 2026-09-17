# Tequaly Workforce Readiness — Product Design

**Data:** 2026-08-10  
**Status:** design para revisão  
**Fontes de verdade:** `01_TEQUALY_WORKFORCE_READINESS_CONTEXT.md`, `02_TEQUALY_WORKFORCE_READINESS_SPEC.md` e `03_PROMPT_CODEX_TEQUALY_WORKFORCE_READINESS.md` fornecidos pelo usuário.

## 1. Objetivo

Construir uma aplicação web interna e independente para transformar dados estruturados de colaboradores, requisitos operacionais, disponibilidade, capacitações e custos em decisões de prontidão e alocação reproduzíveis.

Para uma operação futura, o sistema deverá:

1. classificar candidatos como `ELIGIBLE`, `TRAINABLE` ou `INELIGIBLE`;
2. explicar requisitos satisfeitos e lacunas com códigos determinísticos;
3. gerar cenários de menor custo, prontidão mais rápida e melhor aproveitamento interno;
4. apresentar treinamentos, riscos e bloqueadores;
5. registrar a decisão humana e comparar o previsto com o realizado;
6. expor as mesmas capacidades para a interface web, o copiloto e o MCP.

## 2. Escopo e limites

O MVP inclui cadastro e consulta de workforce, operações e requisitos, regras de elegibilidade, OR-Tools, planejamento de treinamento, fragilidade, auditoria, outcome/recalibração, importação/exportação, autenticação simples, copiloto OpenAI-compatible e MCP.

O MVP não inclui:

- integração com Tequaly Field Intelligence;
- entidade `Evidence` ou gestão documental;
- OCR, RAG, vector database ou knowledge graph;
- machine learning ou recalibração automática;
- microserviços, Kafka, Kubernetes ou data lake;
- multi-tenant, SSO corporativo ou IAM complexo;
- decisão autônoma do LLM;
- aplicativo mobile nativo.

## 3. Premissas de organização e volume

Fontes públicas consultadas em agosto de 2026 sustentam a seguinte premissa:

- o site oficial da Tequaly informa mais de 2.000 colaboradores;
- o LinkedIn enquadra a empresa na faixa de 1.001–5.000 empregados;
- o Glassdoor exibe 120 títulos de cargo informados por usuários, com duplicidades e variações;
- a atuação cobre engenharia, fabricação, implantação, manutenção, logística e operações em diferentes localidades e segmentos industriais.

O projeto utilizará:

- 2.200 colaboradores na massa sintética principal;
- 90 cargos canônicos;
- aproximadamente 130 títulos e aliases de origem;
- 12 famílias profissionais;
- cerca de 120 itens distribuídos entre qualificações, autorizações e treinamentos;
- entre 8.000 e 14.000 vínculos de qualificação;
- cinco bases/localizações;
- oito operações futuras;
- uma massa de 3.000 pessoas para testes de desempenho;
- uma fixture pequena e determinística para testes rápidos.

Esses números são premissas de projeto, não afirmações sobre o cadastro interno real da Tequaly.

## 4. Estratégia de dados

O desenvolvimento será **synthetic-first, real-data-ready**.

A PoC funcionará integralmente com dados fictícios e reproduzíveis. A entrada posterior de dados reais ocorrerá por contratos XLSX/CSV com preview, mapeamento, validação, dry-run e commit transacional. Nenhuma regra, tela ou modelo de otimização dependerá de nomes de colunas particulares de uma planilha simulada.

O sistema distinguirá:

| Conceito | Responsabilidade |
|---|---|
| Família profissional | Agrupamento analítico de cargos |
| Cargo canônico | Papel estável no cadastro interno |
| Alias de cargo | Título bruto vindo de RH ou planilha |
| Função operacional | Papel exigido por uma operação específica |
| Qualificação | Competência ou certificação verificável |
| Autorização | Permissão contextual por cliente, local ou equipamento |
| Capacitação | Ação que concede, renova ou amplia uma qualificação |

O `EmployeeProfileVector` será um DTO de leitura montado a partir do modelo relacional. Sua ordem serializada e visual começará obrigatoriamente por `cargo_funcao_principal`, `nome` e `qualificacoes`, seguida pelos demais campos definidos na SPEC. O DTO não será a fonte de verdade e não será persistido como um único JSON.

## 5. Arquitetura

O sistema será um monólito modular em um único repositório:

```text
Next.js/React
    -> FastAPI HTTP Adapter
       -> Application Services
          -> Pure Eligibility Rules
          -> OR-Tools Optimizer
          -> Training and Fragility Services
          -> Decision Audit
          -> Repositories
             -> PostgreSQL

Copilot -> AI Orchestrator -> Tool Registry -> Application Services
Claude  -> MCP Adapter     -> Tool Registry -> Application Services
```

O backend será um único processo FastAPI em produção. O servidor MCP será um entrypoint separado, mas importará a mesma camada de aplicação. O frontend não acessará o PostgreSQL e não conterá regras essenciais.

### 5.1 Módulos

- `workforce`: colaboradores, cargos, aliases, qualificações, autorizações, disponibilidade, alocações e custos;
- `operations`: operações, demandas e requisitos;
- `eligibility`: regras puras, reason codes, gaps e candidate pools;
- `optimization`: construção do modelo CP-SAT, objetivos e diagnósticos;
- `training`: gaps de uma operação e investimento preventivo;
- `fragility`: cobertura, redundância, vencimentos e pontos únicos de falha;
- `decisions`: runs, seleção humana, outcomes e sugestões de recalibração;
- `imports`: contratos, mapeamento, dry-run e transação;
- `ai`: provider, tool registry, confirmação e orquestração;
- `audit`: eventos imutáveis de mudança e execução;
- `auth`: login local e papéis mínimos.

## 6. Modelo de dados

As tabelas obrigatórias da SPEC serão preservadas. Serão acrescentadas apenas relações necessárias para normalização de títulos e compatibilidade operacional:

- `role_families`;
- `role_aliases`;
- `operation_role_compatible_roles`.

As qualificações terão definição canônica, categoria e regras de validade. Os vínculos do colaborador registrarão emissão, vencimento, carga horária, provedor, identificador externo e observação. Método, nível ou escopo serão atributos estruturados quando afetarem elegibilidade; não serão codificados apenas no nome.

Autorizações permanecerão separadas de qualificações porque podem depender de cliente, unidade, equipamento ou janela temporal. Capacitações serão ligadas à qualificação concedida ou renovada e às sessões disponíveis.

Snapshots de `DecisionRun` guardarão os dados determinantes e hashes necessários para auditoria. Prompts de LLM nunca serão fonte de verdade da decisão.

## 7. Motor de elegibilidade

`EligibilityService` receberá colaborador, operação, demanda de função e intervalo de referência. As regras serão funções puras e testáveis.

Ordem de avaliação:

1. colaborador ativo;
2. compatibilidade de cargo/função;
3. disponibilidade no intervalo;
4. conflitos de alocação;
5. qualificações obrigatórias;
6. validade durante o intervalo exigido;
7. autorizações aplicáveis;
8. experiência mínima;
9. restrições operacionais;
10. capacitação disponível e concluída antes do prazo.

Cada falha terá `reason_code`, mensagem legível e campos estruturados. A resposta separará fatos, regras, cálculo e resultado. `TRAINABLE` somente será retornado quando todas as lacunas puderem ser resolvidas dentro do prazo e sem violar restrições.

O candidate pool será reduzido deterministicamente antes do solver por cargo compatível, período, localização quando obrigatória e elegibilidade/treinabilidade. Isso evita enviar os 2.200 colaboradores ao CP-SAT sem necessidade.

## 8. Otimização

O `OptimizationService` construirá um modelo comum de restrições e aplicará três objetivos.

### 8.1 Restrições duras

- cobrir a quantidade exigida por demanda;
- selecionar somente elegíveis ou treináveis no prazo;
- impedir alocações simultâneas incompatíveis;
- incluir capacitações necessárias ao selecionar um treinável;
- respeitar disponibilidade, autorizações e intervalo de validade;
- não relaxar requisito obrigatório.

### 8.2 Objetivos

**Menor custo:** minimizar custos incrementais existentes nos dados, com desempate por `team_ready_at` e quantidade de treinamentos. Salário fixo não entra por padrão.

**Mais rápido:** minimizar o maior `ready_at` da equipe, com desempate por treinamentos e custo.

**Aproveitamento interno:** aplicar otimização lexicográfica para maximizar preenchimento interno, internos já qualificados e capacidade subutilizada; depois minimizar treinamento e custo.

Cada cenário retornará status, assignments, treinamento, custo, `team_ready_at`, métricas internas, bloqueadores e runtime. `INFEASIBLE` será um resultado normal e explicável.

## 9. Capacitação e fragilidade

O modo operacional de treinamento converterá gaps treináveis em ações com pessoa, curso, sessão, conclusão, custo e impacto.

O modo estratégico receberá operações futuras, horizonte e orçamento. Ele maximizará `CoverageGain` usando pesos visíveis para operações confirmadas, prováveis e hipotéticas. Não haverá ML.

Fragilidade será calculada por função e requisito usando:

- `coverage_ratio`;
- `redundancy`;
- vencimentos antes do início e durante a operação;
- pessoas já alocadas ou indisponíveis;
- treináveis antes do prazo;
- ausência de turma viável;
- `single_point_of_failure`.

As classes de risco serão derivadas de limites configuráveis e sempre apresentarão os fatores que produziram a classificação.

## 10. Auditoria, outcome e recalibração

Toda execução de elegibilidade e solver será versionada. A seleção final exigirá ação humana e poderá incluir justificativa.

Após a execução real, o usuário registrará custo, prontidão, treinamentos, substituições e desvios. O sistema comparará previsto e realizado e gerará sugestões por estatística simples, como mediana por categoria e diferenças recorrentes.

Uma sugestão de recalibração conterá parâmetro, valor atual, valor proposto, amostra, motivo e base de confiança. Aplicação exigirá confirmação e novo evento de auditoria.

## 11. API e experiência web

O frontend será Next.js App Router, React, TypeScript e Tailwind CSS. A API pública interna será FastAPI/OpenAPI. Tipos do frontend serão gerados ou validados contra o contrato OpenAPI para reduzir divergência.

A navegação seguirá a SPEC: visão geral, colaboradores, qualificações, operações, planejador, capacitações, risco, auditoria e configurações.

O design será desktop-first, denso e acessível, com os tokens Tequaly fornecidos. Tabelas usarão paginação, busca e filtros no servidor. Estado crítico nunca será comunicado apenas por cor.

O fluxo principal da primeira fatia será:

1. abrir uma operação;
2. revisar demanda e requisitos;
3. executar elegibilidade;
4. explorar elegíveis, treináveis e bloqueados;
5. executar os três objetivos;
6. comparar cenários lado a lado;
7. selecionar um cenário com confirmação;
8. visualizar equipe, treinamento, risco e auditoria.

## 12. IA e MCP

O backend definirá `LLMProvider` e `OpenAICompatibleProvider`, com `base_url`, chave, modelo, timeout e suporte a tools configuráveis. Nenhuma credencial será enviada ao navegador.

O `ToolRegistry` será o catálogo único de ferramentas. Cada tool terá schema de entrada e saída, classificação read/write, autorização e política de confirmação. O copiloto e o MCP reutilizarão esse registro.

O LLM receberá somente contexto mínimo da tela e resultados estruturados. Não receberá `DATABASE_URL`, SQL ou dumps do banco. Se estiver indisponível, a aplicação exibirá o estado da IA e manterá todos os fluxos determinísticos disponíveis.

O MCP oferecerá stdio para desenvolvimento e Streamable HTTP autenticado quando ativado. O adaptador não possuirá repositórios nem consultas exclusivas.

## 13. Importação e exportação

Importações XLSX/CSV seguirão:

1. upload e detecção de planilha;
2. preview seguro;
3. mapeamento para campos canônicos;
4. normalização de aliases;
5. dry-run com erros por linha;
6. resumo de válidos, inválidos e duplicados;
7. confirmação;
8. commit transacional;
9. audit event.

Arquivos de exemplo serão gerados a partir do contrato canônico. Exportações respeitarão filtros e nunca incluirão secrets ou configuração de IA.

## 14. Segurança e privacidade

- secrets apenas no backend e fora do Git;
- autenticação local simples para a PoC;
- papéis `ADMIN`, `PLANNER` e `VIEWER`;
- autorização obrigatória para escrita;
- CORS restrito;
- ORM ou SQL parametrizado;
- logs sem tokens e sem payloads sensíveis completos;
- rate limit no copiloto quando exposto;
- autenticação do transporte MCP remoto;
- dados sintéticos sem nomes reais;
- minimização de dados pessoais na importação real.

## 15. Erros, execução e observabilidade

Erros HTTP terão código estável, mensagem acionável e `correlation_id`. Falhas de validação apontarão campo ou linha. Falhas do solver distinguirão timeout, `INFEASIBLE` e erro interno.

Execuções de elegibilidade, otimização e importação terão estado persistido e poderão ser consultadas pela interface. No MVP, o backend executará o trabalho de forma controlada sem broker externo. Uma fila só será introduzida se os testes de 3.000 pessoas demonstrarem necessidade.

Logs estruturados registrarão duração, contagens e versões, sem secrets. Métricas mínimas incluirão tempo de consulta, duração do solver, tamanho do candidate pool, quantidade de gaps e taxa de erro de importação.

No benchmark local documentado, com PostgreSQL e a massa de 3.000 pessoas, os alvos serão:

- listagem, busca e abertura de perfil com p95 de até 800 ms na API;
- execução completa de elegibilidade de uma operação em até 15 segundos;
- cada objetivo do solver em até 30 segundos, com limite duro e resultado `FEASIBLE`, `OPTIMAL`, `INFEASIBLE` ou timeout explícito;
- dry-run de importação de 3.000 colaboradores em até 30 segundos;
- nenhuma página principal carregando todos os colaboradores no navegador.

Os resultados serão registrados com hardware, versões, tamanho do candidate pool e parâmetros utilizados, para que os números sejam reproduzíveis.

## 16. Estratégia de testes

O backend usará pytest para domínio, serviços, repositórios, API, solver, importação, IA e MCP. O frontend terá testes de componentes e Playwright para fluxos críticos.

Testes obrigatórios cobrirão:

- validade, disponibilidade, conflito, autorização e treinamento no prazo;
- invariantes de que nenhum inelegível é alocado e toda solução viável cobre a demanda;
- diferenças entre os três objetivos;
- diagnóstico `INFEASIBLE` sem relaxamento;
- igualdade de resultado entre API e MCP para o mesmo serviço;
- confirmação e auditoria de tools de escrita;
- funcionamento do core sem LLM;
- dry-run, duplicidade, datas inválidas e transação;
- seed idempotente e migração limpa;
- volume de 3.000 pessoas e candidate pool pré-filtrado.

Testes que dependem de um provedor LLM externo serão separados dos testes determinísticos e não serão declarados como executados sem credenciais e evidência real.

## 17. Entregas incrementais

### Entrega 1 — Núcleo operacional

Estrutura do repositório, documentação, banco, migrações, seed de 2.200 pessoas, EmployeeProfileVector, operações, elegibilidade, candidate pool, três objetivos, API e comparação visual mínima.

### Entrega 2 — Inteligência operacional

Planejamento de treinamento, fragilidade, auditoria de decisão, seleção humana, outcome e sugestões de recalibração.

### Entrega 3 — Interfaces inteligentes

Provider OpenAI-compatible, tool registry, painel do copiloto, confirmação de escrita, MCP stdio/HTTP e testes de equivalência.

### Entrega 4 — Integração e qualidade

Importação/exportação, autenticação, E2E completo, acessibilidade, performance, screenshots, relatório de testes, guia de execução e limitações.

Cada entrega passará por build, lint, testes e revisão antes da próxima.

## 18. Critérios de conclusão

O projeto só será declarado completo quando:

- frontend e backend iniciarem pelas instruções documentadas;
- PostgreSQL migrar do zero e o seed for idempotente;
- elegibilidade e os três objetivos estiverem testados;
- o solver nunca violar hard constraints;
- importação possuir dry-run e commit transacional;
- copiloto degradar com segurança sem LLM;
- MCP reutilizar os mesmos serviços;
- auditoria, outcome e recalibração funcionarem;
- o fluxo crítico E2E passar;
- a massa de 3.000 pessoas atender aos limites de desempenho definidos no plano;
- documentação e limitações refletirem somente funcionalidades verificadas.

## 19. Decisões consolidadas

1. Fatias verticais serão preferidas a uma implementação completa por camada.
2. Dados simulados são suficientes para a PoC; dados reais poderão ser importados depois.
3. A massa principal terá 2.200 pessoas e a massa de desempenho terá 3.000.
4. Cargos canônicos, aliases e funções operacionais são conceitos separados.
5. Qualificações, autorizações e treinamentos permanecem separados.
6. PostgreSQL é a fonte de verdade; o DTO consolidado não substitui o modelo relacional.
7. Regras e solver são independentes do LLM.
8. API, copiloto e MCP reutilizam Application Services e Tool Registry.
9. Infraestrutura adicional só será adotada mediante evidência de necessidade.
10. Todos os dados de demonstração serão fictícios.
