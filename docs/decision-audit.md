# Decisão, resultado e calibração auditável

## Trilha da decisão

Cada cenário persiste objetivo, versões do solver e das regras, hash do snapshot de entrada, candidatos considerados, métricas, equipe, capacitações, autor e horário. A seleção exige confirmação humana e aceita uma justificativa. Uma nova seleção não apaga a anterior: ela a marca como superada e registra um evento de auditoria.

Somente um cenário selecionado aceita resultado. O registro compara:

- custo previsto e realizado, incluindo variação absoluta e percentual;
- prontidão prevista e real, incluindo minutos de avanço ou atraso;
- treinamentos planejados e realizados;
- substituições de pessoas em relação ao snapshot.

O resultado é único por cenário e não pode ser silenciosamente sobrescrito.

## Calibração supervisionada

Observações de custo de treinamento, deslocamento ou prazo de mobilização podem acompanhar um resultado quando há evidência do realizado. Uma sugestão exige pelo menos cinco observações comparáveis da mesma categoria.

O estimador usa mediana e intervalo interquartil para reduzir a influência de valores extremos. A aplicação exige confirmação explícita, cria uma versão imutável (`v1`, `v2`, ...) e registra quem aplicou, quando e com qual justificativa. Não existe autoaplicação.

O seed contém cinco observações históricas sintéticas na categoria `seguranca`: 300, 310, 320, 330 e 1.000 reais. O último valor é um outlier deliberado para demonstrar robustez estatística. Esses registros são identificados como `demo-seed` e não representam dados da Tequaly.

## Controles ainda necessários para produção

- autenticação SSO e autorização associada a identidades reais;
- política de retenção, LGPD e segregação por perfil;
- anexos ou referências da evidência que sustenta cada valor realizado;
- fluxo de revisão em quatro olhos para parâmetros críticos;
- catálogo formal de parâmetros e impacto das versões nos cenários futuros.

