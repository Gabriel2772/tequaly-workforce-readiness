# Fragilidade operacional

## O que o mapa mede

Cada célula representa uma demanda de cargo/turno em uma operação futura. A base é a última elegibilidade concluída para a operação e os indicadores são reproduzíveis:

- cobertura: pessoas elegíveis versus quantidade exigida;
- redundância: elegíveis além da quantidade exigida;
- treináveis: pessoas que podem fechar uma lacuna antes do prazo;
- vencimentos: pessoas elegíveis cuja qualificação exigida vence até a mobilização;
- pressão de alocação: elegíveis já comprometidos em período concorrente;
- ausência de turma: lacunas treináveis sem sessão viável.

Sem execução de elegibilidade, os dados não são convertidos em falsa cobertura. O dashboard executivo marca a análise como pendente e o mapa só usa runs concluídos.

## Severidade explicável

As regras atuais são determinísticas:

- `critical`: cobertura elegível abaixo da quantidade exigida;
- `high`: cobertura exata, sem redundância, ou alocações concorrentes derrubam a cobertura efetiva;
- `medium`: vencimento antes da mobilização ou treinamento sem turma viável;
- `low`: nenhuma das condições anteriores.

Uma célula recebe a maior severidade aplicável e mantém todos os códigos, limiares, valores observados e mensagens que contribuíram para o resultado. O risco não é produzido por LLM e não substitui análise de segurança ou autorização formal.

## Limitações

- severidade ainda não incorpora criticidade contratual específica do cliente;
- ausências, férias e escalas reais dependem da qualidade das janelas de disponibilidade;
- correlações entre requisitos e riscos sistêmicos não são inferidas;
- o horizonte é configurável, mas não existe projeção probabilística de admissões ou desligamentos;
- os limiares devem ser calibrados com histórico real antes de decisão produtiva.

