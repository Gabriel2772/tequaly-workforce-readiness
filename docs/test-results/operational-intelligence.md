# Evidências do gate de inteligência operacional

Data: 2026-08-24

Branch: `feat/twr-core`

## Escopo verificado

- plano de capacitação por operação e priorização de investimento;
- conflitos de agenda, capacidade de turma e prazo de mobilização;
- mapa de fragilidade com explicações;
- dashboard com análise pendente explícita;
- seleção humana, resultado previsto versus realizado e linha do tempo;
- sugestão robusta e aplicação supervisionada de parâmetro;
- preflight CORS das escritas feitas pelo navegador.

## Backend

Executado em `backend`:

| Comando | Resultado |
|---|---|
| `uv run pytest` | 109 passed, 1 skipped, 60,64 s |
| `uv run ruff check .` | sem achados |
| `uv run mypy app` | sem achados em 72 arquivos |

O skip é o round-trip PostgreSQL, condicionado a `TWR_TEST_DATABASE_URL`. A suíte inclui seed de 2.200 pessoas executado duas vezes e confirma ausência de duplicação, além de cinco outcomes e um parâmetro histórico sintético.

## Frontend

Executado em `frontend` com Node.js 22.23.0:

| Comando | Resultado |
|---|---|
| `vitest run` | 17 arquivos e 19 testes passaram; 159,39 s |
| `tsc --noEmit` | exit 0 |
| `eslint .` | exit 0 |
| `next build` | sucesso; 12 rotas, incluindo `/health` |
| `playwright test` | 2 passed; execução total 2,5 min |

O Playwright usou Microsoft Edge, aplicou as migrações `0001` a `0008` em SQLite limpo e semeou 300 pessoas. O primeiro fluxo recalculou elegibilidade e gerou os três objetivos. O segundo escolheu uma operação viável, inspecionou capacitação e fragilidade, selecionou o cenário, registrou resultado com a sexta observação, obteve mediana de R$ 325,00 e aplicou `v2`.

## Regressões encontradas e corrigidas pelo gate

- seleção persistia, mas a página não atualizava para exibir o formulário de resultado;
- escritas diretas de auditoria/calibração falhavam no preflight CORS;
- o health check do frontend consultava o dashboard e podia bloquear o SQLite antes da preparação do E2E;
- módulos de teste homônimos colidiam no modo legado de importação do pytest;
- o E2E inicialmente escolhia o cenário sintético intencionalmente inviável.

## Limitações não aprovadas

- PostgreSQL 18 não foi exercitado neste ambiente;
- dados, custos e parâmetros são sintéticos e não representam histórico Tequaly;
- SSO, importação real e conectores corporativos ainda não fazem parte deste gate;
- não há integração com LMS nem evidência documental anexada aos outcomes;
- calibração suporta custo de treinamento, deslocamento e prazo; regras produtivas ainda exigem governança da Tequaly.
