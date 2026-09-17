# Modelo de dados implementado

## Identidade e unidades

Chaves prim�rias s�o UUID. Matr�culas e c�digos de cat�logo s�o chaves naturais �nicas. Dinheiro � armazenado em centavos inteiros e o solver trabalha com minutos inteiros. Datas operacionais usam campos timezone-aware.

## Normaliza��o de cargos e escala

`role_families`, `roles` e `role_aliases` separam fam�lia, cargo can�nico e t�tulo de origem. O seed principal cont�m 12 fam�lias, 90 cargos e 130 aliases. `operation_role_compatible_roles` permite que uma demanda aceite mais de um cargo sem fragmentar a taxonomia.

A escala sint�tica padr�o � de 2.200 colaboradores; o benchmark gera 3.000. O n�mero real de colaboradores, t�tulos e qualifica��es da Tequaly deve ser confirmado por exporta��es oficiais antes da carga real.

## Workforce

As tabelas entregues s�o:

- `employees` e `employee_role_history`;
- `qualifications` e `employee_qualifications`;
- `authorizations` e `employee_authorizations`;
- `employee_availability`, `employee_assignments` e `employee_cost_profiles`;
- `technical_competencies` e `employee_competencies`;
- `operational_restrictions` e `employee_operational_restrictions`;
- `training_catalog`, `training_sessions` e `employee_training_plans`.

O seed cria 72 qualifica��es, 24 autoriza��es e 24 itens de capacita��o, totalizando 120 itens de prontid�o. N�o existe entidade `Evidence` nem armazenamento de documentos nesta entrega.

## Opera��es e elegibilidade

`operations`, `operation_role_demands`, `operation_requirements`, `requirement_qualification_map` e `operation_role_compatible_roles` definem a necessidade operacional.

`eligibility_runs` persiste vers�o das regras, hash de entrada, hor�rios, contagens e runtime. `eligibility_results` guarda classifica��o, motivos estruturados, lacunas, treinamentos necess�rios, prontid�o e custo incremental por colaborador/demanda.

## Decis�es

`decision_runs` guarda objetivo, vers�o do solver/regras, hash e snapshot dos candidatos, status, m�tricas e ator. `decision_assignments` e `decision_training_actions` guardam a proposta. `decision_outcomes`, `calibration_parameters` e `audit_events` j� existem no schema para evolu��o audit�vel, embora a UI do core n�o registre outcome ou recalibra��o.

## EmployeeProfileVector

O DTO de leitura � montado das tabelas normalizadas, nesta ordem: cargo principal, nome, qualifica��es, compet�ncias, autoriza��es, disponibilidade, base, senioridade, aloca��es, custos, capacita��es, restri��es, prontid�o e `updated_at`. Ele n�o � fonte de verdade persistida.

## �ndices importantes

H� �ndices para colaborador ativo/cargo, base/ativo, expira��o de qualifica��es e autoriza��es, janelas de disponibilidade/aloca��o, vig�ncia de custos, per�odo/status de opera��o, resultados por run/classifica��o e decis�es por opera��o/data.
