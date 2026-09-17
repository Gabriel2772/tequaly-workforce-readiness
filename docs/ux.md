# UX entregue

## Shell desktop

O shell usa sidebar de 248 px, recolhida para 72 px abaixo de 1280 px, e topbar de 64 px. A navegação apresenta Visão geral, Colaboradores, Qualificações, Operações, Planejador de equipe, Capacitações, Risco, Auditoria, Configurações e Conexões MCP com dez ícones SVG rotulados.

As rotas principais estão funcionais. Configurações concentra qualidade, importação e exportações; Auditoria concentra seleção, outcome e calibração; Capacitações e Risco expõem os resultados operacionais correspondentes.

## Tokens

Fundo `#0B0C12`; superfícies `#12131A`, `#191821`, `#23212D`; borda `#302D3A`; texto `#F6F4F7`/`#BBB6C2`; marca `#6C0775`/`#84108E`; roxo noturno `#303779`; risco `#E80F2B`; sucesso `#70AD47`; informação `#5B9BD5`; aviso `#FFB175`. Não há gradientes ou animação decorativa.

## Planejador

O usuário seleciona uma operação, recalcula elegibilidade e gera um cenário por objetivo. A tela mostra:

- contagens elegível/treinável/inelegível e motivos textuais;
- custo, equipe pronta, aproveitamento interno, já qualificados e treinamento;
- status do solver e tempo de execução;
- blockers com número de vagas descobertas;
- tabela da equipe proposta.

Estados não dependem apenas de cor. Ações longas anunciam progresso/sucesso/erro via regiões de status; inviabilidade usa `role="alert"`; tabs, tabelas e navegação têm nomes acessíveis; existe skip link.

## Conexões MCP

A rota `/conexoes-mcp` oferece CRUD, validação estrutural, cópia sem segredos, busca e filtros. Diálogos possuem nomes acessíveis, resultados usam região live e a exclusão exige confirmação. Os cards de destino deixam claro que a configuração acontece fora do TWR.

Não há campo de autenticação, conversa ou execução de ferramenta nessa página.

## Responsividade e limites

A experiência é desktop-first. Em larguras menores a sidebar recolhe; no mobile ela vira gaveta off-canvas com backdrop e fechamento por clique ou mudança de rota. Cards e formulários passam para a largura útil. Não há aplicativo móvel especializado nem funcionamento offline.
