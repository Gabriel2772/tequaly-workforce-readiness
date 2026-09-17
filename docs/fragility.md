# Fragilidade operacional

## O que o mapa mede

Cada c�lula representa uma demanda de cargo/turno em uma opera��o futura. A base � a �ltima elegibilidade conclu�da para a opera��o e os indicadores s�o reproduz�veis:

- cobertura: pessoas eleg�veis versus quantidade exigida;
- redund�ncia: eleg�veis al�m da quantidade exigida;
- trein�veis: pessoas que podem fechar uma lacuna antes do prazo;
- vencimentos: pessoas eleg�veis cuja qualifica��o exigida vence at� a mobiliza��o;
- press�o de aloca��o: eleg�veis j� comprometidos em per�odo concorrente;
- aus�ncia de turma: lacunas trein�veis sem sess�o vi�vel.

Sem execu��o de elegibilidade, os dados n�o s�o convertidos em falsa cobertura. O dashboard executivo marca a an�lise como pendente e o mapa s� usa runs conclu�dos.

## Severidade explic�vel

As regras atuais s�o determin�sticas:

- `critical`: cobertura eleg�vel abaixo da quantidade exigida;
- `high`: cobertura exata, sem redund�ncia, ou aloca��es concorrentes derrubam a cobertura efetiva;
- `medium`: vencimento antes da mobiliza��o ou treinamento sem turma vi�vel;
- `low`: nenhuma das condi��es anteriores.

Uma c�lula recebe a maior severidade aplic�vel e mant�m todos os c�digos, limiares, valores observados e mensagens que contribu�ram para o resultado. O risco n�o � produzido por LLM e n�o substitui an�lise de seguran�a ou autoriza��o formal.

## Limita��es

- severidade ainda n�o incorpora criticidade contratual espec�fica do cliente;
- aus�ncias, f�rias e escalas reais dependem da qualidade das janelas de disponibilidade;
- correla��es entre requisitos e riscos sist�micos n�o s�o inferidas;
- o horizonte � configur�vel, mas n�o existe proje��o probabil�stica de admiss�es ou desligamentos;
- os limiares devem ser calibrados com hist�rico real antes de decis�o produtiva.

