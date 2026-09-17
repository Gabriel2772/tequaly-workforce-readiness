# Decis�o, resultado e calibra��o audit�vel

## Trilha da decis�o

Cada cen�rio persiste objetivo, vers�es do solver e das regras, hash do snapshot de entrada, candidatos considerados, m�tricas, equipe, capacita��es, autor e hor�rio. A sele��o exige confirma��o humana e aceita uma justificativa. Uma nova sele��o n�o apaga a anterior: ela a marca como superada e registra um evento de auditoria.

Somente um cen�rio selecionado aceita resultado. O registro compara:

- custo previsto e realizado, incluindo varia��o absoluta e percentual;
- prontid�o prevista e real, incluindo minutos de avan�o ou atraso;
- treinamentos planejados e realizados;
- substitui��es de pessoas em rela��o ao snapshot.

O resultado � �nico por cen�rio e n�o pode ser silenciosamente sobrescrito.

## Calibra��o supervisionada

Observa��es de custo de treinamento, deslocamento ou prazo de mobiliza��o podem acompanhar um resultado quando h� evid�ncia do realizado. Uma sugest�o exige pelo menos cinco observa��es compar�veis da mesma categoria.

O estimador usa mediana e intervalo interquartil para reduzir a influ�ncia de valores extremos. A aplica��o exige confirma��o expl�cita, cria uma vers�o imut�vel (`v1`, `v2`, ...) e registra quem aplicou, quando e com qual justificativa. N�o existe autoaplica��o.

O seed cont�m cinco observa��es hist�ricas sint�ticas na categoria `seguranca`: 300, 310, 320, 330 e 1.000 reais. O �ltimo valor � um outlier deliberado para demonstrar robustez estat�stica. Esses registros s�o identificados como `demo-seed` e n�o representam dados da Tequaly.

## Controles ainda necess�rios para produ��o

- autentica��o SSO e autoriza��o associada a identidades reais;
- pol�tica de reten��o, LGPD e segrega��o por perfil;
- anexos ou refer�ncias da evid�ncia que sustenta cada valor realizado;
- fluxo de revis�o em quatro olhos para par�metros cr�ticos;
- cat�logo formal de par�metros e impacto das vers�es nos cen�rios futuros.

