# Elegibilidade e otimização

## Pipeline

1. O banco pré-filtra colaboradores ativos por cargo compatível e, quando aplicável, base.
2. Regras determinísticas classificam cada candidato/demanda como `ELIGIBLE`, `TRAINABLE` ou `INELIGIBLE`.
3. O run e seus motivos são persistidos com versão e hash.
4. O solver recebe somente candidatos elegíveis/treináveis e fatos normalizados.
5. Cada cenário é persistido como `DecisionRun` e pode ser consultado novamente.

As regras cobrem situação do colaborador, compatibilidade de cargo, disponibilidade contínua, conflitos de alocação, qualificações e validade, capacitação antes do prazo, autorizações, experiência, restrições e prazo de mobilização.

## Modelo CP-SAT

`x[e,d]` indica a alocação do colaborador `e` na demanda `d`; `y[e,t]` ativa uma capacitação necessária. Cobertura exata, unicidade, conflitos, treinamentos obrigatórios e deadline são restrições rígidas. Dinheiro é centavo inteiro e tempo é minuto inteiro.

O solver nunca enfraquece uma restrição para produzir resposta. Pré-checagens e matching retornam vagas descobertas, demanda afetada e requisitos bloqueadores quando o problema é inviável.

## Objetivos lexicográficos

- `MIN_COST`: custo incremental, depois prontidão e quantidade de capacitações;
- `FASTEST_READY`: menor instante em que toda a equipe está pronta, depois capacitações e custo;
- `MAX_INTERNAL`: maior aproveitamento interno e já qualificado, depois horas de capacitação e custo.

Cada prioridade é otimizada, fixada como restrição e só então a próxima é resolvida. Não há soma de pesos arbitrários.

## Saída e limites

Os status possíveis são `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `TIMEOUT`, `TIMEOUT_FEASIBLE` e `ERROR`. A saída inclui assignments, ações de capacitação, custo, `ready_at`, uso interno, posições já qualificadas, horas de treinamento, blockers, versões e runtime.

Cada objetivo tem limite de 30 segundos. O teste de desempenho com 3.000 pessoas exige elegibilidade abaixo de 15 segundos e todos os três cenários abaixo de 30 segundos cada.
