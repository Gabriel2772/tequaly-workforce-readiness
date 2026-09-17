# Modelo de dados implementado

## Identidade e unidades

Chaves primárias são UUID. Matrículas e códigos de catálogo são chaves naturais únicas. Dinheiro é armazenado em centavos inteiros e o solver trabalha com minutos inteiros. Datas operacionais usam campos timezone-aware.

## Normalização de cargos e escala

`role_families`, `roles` e `role_aliases` separam família, cargo canônico e título de origem. O seed principal contém 12 famílias, 90 cargos e 130 aliases. `operation_role_compatible_roles` permite que uma demanda aceite mais de um cargo sem fragmentar a taxonomia.

A escala sintética padrão é de 2.200 colaboradores; o benchmark gera 3.000. O número real de colaboradores, títulos e qualificações da Tequaly deve ser confirmado por exportações oficiais antes da carga real.

## Workforce

As tabelas entregues são:

- `employees` e `employee_role_history`;
- `qualifications` e `employee_qualifications`;
- `authorizations` e `employee_authorizations`;
- `employee_availability`, `employee_assignments` e `employee_cost_profiles`;
- `technical_competencies` e `employee_competencies`;
- `operational_restrictions` e `employee_operational_restrictions`;
- `training_catalog`, `training_sessions` e `employee_training_plans`.

O seed cria 72 qualificações, 24 autorizações e 24 itens de capacitação, totalizando 120 itens de prontidão. Não existe entidade `Evidence` nem armazenamento de documentos nesta entrega.

## Operações e elegibilidade

`operations`, `operation_role_demands`, `operation_requirements`, `requirement_qualification_map` e `operation_role_compatible_roles` definem a necessidade operacional.

`eligibility_runs` persiste versão das regras, hash de entrada, horários, contagens e runtime. `eligibility_results` guarda classificação, motivos estruturados, lacunas, treinamentos necessários, prontidão e custo incremental por colaborador/demanda.

## Decisões

`decision_runs` guarda objetivo, versão do solver/regras, hash e snapshot dos candidatos, status, métricas e ator. `decision_assignments` e `decision_training_actions` guardam a proposta. `decision_outcomes`, `calibration_parameters` e `audit_events` já existem no schema para evolução auditável, embora a UI do core não registre outcome ou recalibração.

## EmployeeProfileVector

O DTO de leitura é montado das tabelas normalizadas, nesta ordem: cargo principal, nome, qualificações, competências, autorizações, disponibilidade, base, senioridade, alocações, custos, capacitações, restrições, prontidão e `updated_at`. Ele não é fonte de verdade persistida.

## Índices importantes

Há índices para colaborador ativo/cargo, base/ativo, expiração de qualificações e autorizações, janelas de disponibilidade/alocação, vigência de custos, período/status de operação, resultados por run/classificação e decisões por operação/data.
