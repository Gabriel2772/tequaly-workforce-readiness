# Importação, exportação e higiene de dados

## Contratos de importação

O sistema aceita quatro contratos versionados (`v1.0`): colaboradores, qualificações por colaborador, operações/demandas e catálogo de treinamentos. Cabeçalhos canônicos e aliases em português são normalizados, mas duas colunas não podem apontar para o mesmo campo.

O fluxo é sempre:

1. leitura segura de CSV UTF-8 ou XLSX;
2. mapeamento e normalização;
3. preview com erros por linha;
4. confirmação humana;
5. commit transacional e evento de auditoria.

O preview não altera entidades de domínio. Arquivos possuem limite de 5 MB e 5.000 linhas; XLSM, macros, fórmulas, formato não suportado e XLSX inválido são rejeitados. O conteúdo original não é retido como evidência. O lote guarda hash, mapeamento, linhas normalizadas, erros, ator e expiração de 30 minutos.

## Política de atualização

- colaboradores: upsert por matrícula;
- qualificações: upsert por matrícula, código da qualificação e data de emissão;
- operações/demandas: operação por código e demanda por operação, cargo e turno;
- treinamentos: upsert por código do catálogo.

Uma linha inválida impede o commit do lote inteiro. Repetir o commit do mesmo token é idempotente. Somente o papel administrativo pode fazer preview ou commit.

## Exportações

Estão disponíveis CSV e XLSX para colaboradores, prontidão, gaps, cenários, capacitações, risco e decisões auditadas. Os arquivos incluem horário UTC, ator, filtros, versão de contrato e fuso.

Textos iniciados por `=`, `+`, `-` ou `@` são escapados contra injeção de fórmula. Segredos, tokens, configuração de IA e custo-hora individual não fazem parte dos datasets. O limite atual é 10.000 linhas por exportação.

## Higiene de dados

A tela de Configurações mede perfis ativos incompletos, pessoas sem qualificação, pessoas com qualificação vencida, ausência de perfil de custo e operações sem elegibilidade concluída. Cada pendência informa uma ação sugerida. Isso é um indicador operacional, não certificação da origem; o seed aparece explicitamente como sintético.

## Amostras

`samples/` contém CSVs e XLSXs válidos, além de um CSV deliberadamente inválido. `scripts/generate_samples.mjs` regenera e verifica os artefatos com preservação de Unicode e visual profissional básico.

