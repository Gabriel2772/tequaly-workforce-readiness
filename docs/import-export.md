# Importa��o, exporta��o e higiene de dados

## Contratos de importa��o

O sistema aceita quatro contratos versionados (`v1.0`): colaboradores, qualifica��es por colaborador, opera��es/demandas e cat�logo de treinamentos. Cabe�alhos can�nicos e aliases em portugu�s s�o normalizados, mas duas colunas n�o podem apontar para o mesmo campo.

O fluxo � sempre:

1. leitura segura de CSV UTF-8 ou XLSX;
2. mapeamento e normaliza��o;
3. preview com erros por linha;
4. confirma��o humana;
5. commit transacional e evento de auditoria.

O preview n�o altera entidades de dom�nio. Arquivos possuem limite de 5 MB e 5.000 linhas; XLSM, macros, f�rmulas, formato n�o suportado e XLSX inv�lido s�o rejeitados. O conte�do original n�o � retido como evid�ncia. O lote guarda hash, mapeamento, linhas normalizadas, erros, ator e expira��o de 30 minutos.

## Pol�tica de atualiza��o

- colaboradores: upsert por matr�cula;
- qualifica��es: upsert por matr�cula, c�digo da qualifica��o e data de emiss�o;
- opera��es/demandas: opera��o por c�digo e demanda por opera��o, cargo e turno;
- treinamentos: upsert por c�digo do cat�logo.

Uma linha inv�lida impede o commit do lote inteiro. Repetir o commit do mesmo token � idempotente. Somente o papel administrativo pode fazer preview ou commit.

## Exporta��es

Est�o dispon�veis CSV e XLSX para colaboradores, prontid�o, gaps, cen�rios, capacita��es, risco e decis�es auditadas. Os arquivos incluem hor�rio UTC, ator, filtros, vers�o de contrato e fuso.

Textos iniciados por `=`, `+`, `-` ou `@` s�o escapados contra inje��o de f�rmula. Segredos, tokens, configura��o de IA e custo-hora individual n�o fazem parte dos datasets. O limite atual � 10.000 linhas por exporta��o.

## Higiene de dados

A tela de Configura��es mede perfis ativos incompletos, pessoas sem qualifica��o, pessoas com qualifica��o vencida, aus�ncia de perfil de custo e opera��es sem elegibilidade conclu�da. Cada pend�ncia informa uma a��o sugerida. Isso � um indicador operacional, n�o certifica��o da origem; o seed aparece explicitamente como sint�tico.

## Amostras

`samples/` cont�m CSVs e XLSXs v�lidos, al�m de um CSV deliberadamente inv�lido. `scripts/generate_samples.mjs` regenera e verifica os artefatos com preserva��o de Unicode e visual profissional b�sico.

