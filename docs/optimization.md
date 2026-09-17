# Elegibilidade e otimiza��o

## Pipeline

1. O banco pr�-filtra colaboradores ativos por cargo compat�vel e, quando aplic�vel, base.
2. Regras determin�sticas classificam cada candidato/demanda como `ELIGIBLE`, `TRAINABLE` ou `INELIGIBLE`.
3. O run e seus motivos s�o persistidos com vers�o e hash.
4. O solver recebe somente candidatos eleg�veis/trein�veis e fatos normalizados.
5. Cada cen�rio � persistido como `DecisionRun` e pode ser consultado novamente.

As regras cobrem situa��o do colaborador, compatibilidade de cargo, disponibilidade cont�nua, conflitos de aloca��o, qualifica��es e validade, capacita��o antes do prazo, autoriza��es, experi�ncia, restri��es e prazo de mobiliza��o.

## Modelo CP-SAT

`x[e,d]` indica a aloca��o do colaborador `e` na demanda `d`; `y[e,t]` ativa uma capacita��o necess�ria. Cobertura exata, unicidade, conflitos, treinamentos obrigat�rios e deadline s�o restri��es r�gidas. Dinheiro � centavo inteiro e tempo � minuto inteiro.

O solver nunca enfraquece uma restri��o para produzir resposta. Pr�-checagens e matching retornam vagas descobertas, demanda afetada e requisitos bloqueadores quando o problema � invi�vel.

## Objetivos lexicogr�ficos

- `MIN_COST`: custo incremental, depois prontid�o e quantidade de capacita��es;
- `FASTEST_READY`: menor instante em que toda a equipe est� pronta, depois capacita��es e custo;
- `MAX_INTERNAL`: maior aproveitamento interno e j� qualificado, depois horas de capacita��o e custo.

Cada prioridade � otimizada, fixada como restri��o e s� ent�o a pr�xima � resolvida. N�o h� soma de pesos arbitr�rios.

## Sa�da e limites

Os status poss�veis s�o `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `TIMEOUT`, `TIMEOUT_FEASIBLE` e `ERROR`. A sa�da inclui assignments, a��es de capacita��o, custo, `ready_at`, uso interno, posi��es j� qualificadas, horas de treinamento, blockers, vers�es e runtime.

Cada objetivo tem limite de 30 segundos. O teste de desempenho com 3.000 pessoas exige elegibilidade abaixo de 15 segundos e todos os tr�s cen�rios abaixo de 30 segundos cada.
