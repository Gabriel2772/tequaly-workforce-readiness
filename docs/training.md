# Planejamento de capacitação

## Objetivo

Transformar lacunas treináveis da elegibilidade em ações executáveis, ligadas a pessoa, qualificação, curso, turma, prazo, custo e posições liberadas. O módulo não trata treinamento como recomendação genérica: uma ação só é proposta quando existe turma compatível e concluída até a mobilização.

## Plano por operação

O serviço usa a última execução de elegibilidade concluída ou o snapshot associado a um cenário. Para cada par pessoa–qualificação em estado `TRAINABLE`, ele procura uma turma ativa e verifica:

- conclusão até o prazo de mobilização;
- capacidade restante da turma;
- ausência de conflito com alocações operacionais;
- ausência de conflito com treinamentos já cadastrados;
- ausência de conflito com outra ação criada no mesmo plano.

Quando nenhuma turma satisfaz as regras, o plano preserva um bloqueador explicável em vez de considerar a pessoa apta. Ao materializar um cenário, as ações são persistidas em `decision_training_actions` e passam a fazer parte do snapshot auditável.

## Priorização de investimento

O planejador de investimento analisa operações no horizonte informado e escolhe um conjunto de ações sob orçamento. O modelo respeita orçamento, capacidade das turmas e incompatibilidade de horários para a mesma pessoa. O benefício é uma contagem ponderada de demandas potencialmente liberadas, conforme o status da operação (`confirmed`, `planning/probable` ou hipotética).

O campo “Ganho potencial ponderado” não é receita, economia nem garantia de cobertura. Ele é uma pontuação comparativa; a cobertura final continua dependente de elegibilidade, disponibilidade e decisão operacional.

## Limitações e dados reais necessários

- custos, turmas, capacidades e equivalências do seed são sintéticos;
- não há integração com LMS, presença, fornecedor ou emissão de certificado;
- pesos de prioridade precisam de validação da Tequaly;
- turmas multi-etapa, pré-requisitos de curso e tempo de deslocamento ainda não são modelados;
- antes de uso real, RH/SSMA deve validar catálogo, validade, carga horária e regras de equivalência.

