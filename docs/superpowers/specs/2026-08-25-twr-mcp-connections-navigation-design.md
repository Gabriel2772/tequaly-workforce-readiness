# Tequaly Workforce Readiness — conexões MCP individuais e nova navegação

**Data:** 25 de agosto de 2026
**Status:** substituído em 25 de agosto de 2026 por `2026-08-25-twr-user-mcp-registry-visual-design.md`
**Base:** `docs/superpowers/specs/2026-08-10-twr-product-design.md`

## 1. Objetivo

Substituir o copiloto conversacional interno por uma área de conexões MCP na qual cada usuário autenticado do TWR possa autorizar a própria conta Claude ou ChatGPT a consultar dados do Workforce Readiness. A mesma entrega redesenha a sidebar com ícones vetoriais consistentes e um símbolo próprio para o produto.

O TWR permanece a fonte de dados e regras. Claude e ChatGPT são clientes externos que chamam ferramentas somente leitura por MCP; eles não se tornam fontes de verdade e não recebem autorização para executar decisões ou alterar registros.

## 2. Escopo aprovado

### Incluído

- nova rota `/conexoes-ia`;
- item `Claude & ChatGPT` na sidebar;
- servidor MCP remoto por Streamable HTTP;
- autorização OAuth 2.1 individual, baseada no usuário TWR;
- conexão assistida com Claude e ChatGPT;
- visualização e revogação de autorizações por usuário;
- catálogo inicial com cinco ferramentas somente leitura;
- manutenção do MCP local por stdio;
- substituição das siglas da sidebar por ícones SVG;
- novo símbolo vetorial do Workforce Readiness;
- estados responsivos, ativos, hover e foco acessível;
- testes unitários, integração, segurança e E2E.

### Excluído

- chat ou histórico de conversas dentro do TWR;
- uso da assinatura pessoal ChatGPT/Claude como API dentro do TWR;
- configuração de modelos, endpoints OpenAI-compatible ou chaves de LLM;
- ferramentas MCP de escrita, simulação, solver, seleção, outcome, importação ou calibração;
- publicação automática em diretórios públicos de aplicativos;
- SSO corporativo nesta entrega;
- RAG, memória conversacional, anexos ou gerenciamento genérico de documentos.

## 3. Princípios de produto

1. **Conectar o TWR ao cliente, não incorporar o cliente ao TWR.** O usuário conversa no Claude ou ChatGPT e concede acesso ao TWR.
2. **Autorização individual e revogável.** Cada conexão possui dono, cliente, escopo, expiração, último uso e status.
3. **Somente leitura.** O catálogo remoto é explicitamente limitado; decisões críticas continuam nos fluxos web autenticados.
4. **Sem promessa falsa em localhost.** Claude/ChatGPT na nuvem exigem um endereço público HTTPS; o ambiente local apenas mostra configuração e diagnóstico.
5. **Fonte única de regras.** MCP delega aos mesmos serviços determinísticos usados pela aplicação.
6. **Segredos fora do navegador.** Nenhuma chave OpenAI/Anthropic será solicitada, armazenada ou exibida pelo TWR.

## 4. Experiência do usuário

### 4.1 Sidebar

A sidebar mantém a estrutura e os rótulos atuais, mas cada item recebe um ícone SVG de 20 px, traço uniforme e significado reconhecível:

| Destino | Ícone conceitual |
|---|---|
| Visão geral | painel com quatro quadrantes |
| Colaboradores | grupo de pessoas |
| Qualificações | medalha/certificação |
| Operações | capacete industrial |
| Planejador de equipe | nós conectados/calendário |
| Capacitações | livro com seta de progresso |
| Risco e cobertura | escudo com pulso |
| Auditoria | prancheta com verificação |
| Configurações | controles deslizantes |
| Claude & ChatGPT | plugue com nós de IA |

O item `Claude & ChatGPT` é uma rota normal, não abre painel flutuante. A sidebar recolhida preserva `aria-label`, tooltip nativo e indicação ativa que não depende apenas de cor.

### 4.2 Símbolo do produto

O antigo bloco com a letra `T` será substituído por um símbolo vetorial original do produto: monograma geométrico `T/W` combinado com três nós e um sinal de prontidão. O símbolo não tenta reproduzir nem substituir a marca corporativa oficial da Tequaly. O texto `Tequaly / Workforce Readiness` continua ao lado em telas amplas.

### 4.3 Página `/conexoes-ia`

A página possui quatro áreas:

1. **Introdução e postura de segurança:** explica que Claude/ChatGPT consultam dados por ferramentas somente leitura.
2. **Cartões Claude e ChatGPT:** mostram compatibilidade, estado, última autorização e ação principal.
3. **Configuração da conexão:** URL MCP pública, status HTTPS, ferramentas disponibilizadas e instruções específicas para o cliente.
4. **Conexões autorizadas:** cliente, data de criação, último uso, expiração e ação de revogação com confirmação.

Estados obrigatórios:

- ambiente local sem URL pública;
- servidor MCP remoto disponível;
- cliente ainda não autorizado;
- autorização ativa;
- autorização expirada;
- autorização revogada;
- configuração externa bloqueada por plano ou administrador do cliente;
- falha de diagnóstico sem afetar o restante do TWR.

Os botões `Conectar ao Claude` e `Conectar ao ChatGPT` não afirmam instalar uma integração automaticamente. Eles abrem a superfície oficial de configuração quando houver URL estável suportada e sempre exibem a URL MCP exata e instruções copiáveis. O retorno ao TWR ocorre somente pelo fluxo OAuth padronizado iniciado pelo cliente.

## 5. Arquitetura

```text
Claude / ChatGPT
       |
       | Streamable HTTP + OAuth 2.1
       v
   POST /mcp
       |
       v
validação de token e usuário ativo
       |
       v
ToolRegistry READ
       |
       v
serviços determinísticos do TWR
       |
       v
PostgreSQL / SQLite de teste
```

O processo FastAPI continuará como monólito modular. O adaptador MCP não terá SQL ou regras próprias. O transporte stdio existente continuará disponível para desenvolvimento local e usará o mesmo registro de ferramentas.

### 5.1 Configuração

Novas configurações do backend:

- `TWR_PUBLIC_BASE_URL`: origem pública HTTPS usada como recurso/audience;
- `TWR_MCP_REMOTE_ENABLED`: desativado por padrão;
- `TWR_MCP_ACCESS_TOKEN_MINUTES`: vida curta do access token, padrão de 15 minutos;
- `TWR_MCP_REFRESH_TOKEN_DAYS`: validade máxima do refresh token, padrão de 30 dias;
- `TWR_MCP_OAUTH_SECRET`: segredo dedicado, diferente do segredo da sessão;
- `TWR_MCP_ALLOWED_REDIRECT_HOSTS`: allowlist para clientes pré-configurados e registros dinâmicos.

Em produção, segredos devem vir de cofre. Em desenvolvimento, somente valores sintéticos são aceitos.

## 6. OAuth e identidade

O servidor remoto seguirá o perfil OAuth 2.1 do MCP para transportes HTTP:

- descoberta de recurso protegido;
- descoberta do authorization server;
- Authorization Code com PKCE `S256`;
- `state` obrigatório;
- `resource`/audience vinculado à URL canônica do MCP;
- redirect URI exata;
- códigos de autorização de uso único e curta duração;
- access tokens curtos;
- refresh tokens rotativos;
- revogação por grant;
- resposta `401` com metadata adequada quando não autorizado.

Endpoints previstos:

- `GET /.well-known/oauth-protected-resource/mcp`, derivado da URL canônica `/mcp` segundo RFC 9728;
- `GET /.well-known/oauth-authorization-server/oauth`, localização canônica do issuer `/oauth`;
- `GET /.well-known/oauth-authorization-server`, alias de compatibilidade com a URL originalmente documentada;
- `POST /oauth/register` para clientes compatíveis com registro dinâmico;
- `GET /oauth/authorize`;
- `GET /oauth/consent/{request_id}` para carregar o consentimento autenticado;
- `POST /oauth/consent`;
- `POST /oauth/token`;
- `POST /oauth/revoke`;
- `POST /mcp` para mensagens JSON-RPC;
- `GET /mcp` apenas se o SDK precisar manter SSE; caso contrário responde `405` conforme o transporte;
- `DELETE /mcp` apenas se forem habilitadas sessões de transporte.

O MVP usa transporte Streamable HTTP sem estado sempre que a compatibilidade dos clientes permitir. O backend deve delegar enquadramento, negociação de versão e respostas JSON-RPC ao SDK MCP oficial já adotado pelo projeto, em vez de reimplementar o protocolo.

Respostas `401` do recurso incluem `WWW-Authenticate` com a URL `resource_metadata`. O documento de recurso declara a URL canônica completa `/mcp`, o authorization server e o escopo `twr:read`.

Endpoints autenticados usados pela página do TWR:

- `GET /mcp-management/info`: disponibilidade, URL canônica, HTTPS e catálogo público de ferramentas;
- `GET /mcp-management/connections`: grants pertencentes ao usuário da sessão;
- `DELETE /mcp-management/connections/{grant_id}`: revoga somente um grant pertencente ao usuário.

O único escopo inicial é `twr:read`. O fluxo usa a sessão TWR existente para identificar o resource owner. Usuário não autenticado é encaminhado à tela de login e retorna ao pedido de autorização por um identificador opaco de solicitação salvo no servidor — nunca por uma URL de retorno fornecida diretamente pelo navegador. A tela de consentimento mostra cliente, escopo, cinco ferramentas e duração antes de autorizar.

`POST /oauth/consent` exige token CSRF vinculado à sessão e à solicitação de autorização. `state`, `redirect_uri`, `client_id`, `resource`, challenge PKCE e escopo são revalidados antes de emitir o código. Sucesso ou erro só redireciona para uma URI exata registrada para o cliente.

O registro dinâmico aceita apenas clientes públicos com `token_endpoint_auth_method=none`, PKCE obrigatório e redirect URIs permitidas pela configuração. Clientes oficiais também podem ser cadastrados previamente. O endpoint aplica rate limit, valida esquema/host e não busca URLs fornecidas pelo cliente, evitando que o registro se torne vetor de SSRF.

Cada token contém ou referencia:

- `sub`: identificador do usuário TWR;
- `aud`: URL canônica do MCP;
- `client_id`;
- `grant_id`;
- escopos;
- emissão e expiração;
- identificador único para auditoria.

Mesmo com token válido, cada chamada revalida que usuário e grant permanecem ativos. Tokens recebidos do Claude/ChatGPT nunca são repassados a serviços externos.

## 7. Modelo de dados

### `mcp_oauth_clients`

- `id`/`client_id`;
- nome e URI do cliente;
- redirect URIs exatas;
- tipo de aplicação;
- método de autenticação;
- data de criação e status.

### `mcp_authorization_codes`

- hash do código de uso único;
- usuário, cliente e resource;
- redirect URI;
- challenge PKCE e método;
- escopos e expiração;
- instante de consumo.

### `mcp_authorization_requests`

- identificador opaco de curta duração;
- cliente, resource, redirect URI, state, escopo e challenge PKCE;
- expiração, instante de decisão e usuário que decidiu;
- token CSRF armazenado somente como hash.

### `mcp_authorization_grants`

- usuário e cliente;
- escopos concedidos;
- criado, último uso, expiração e revogação;
- revogado por e justificativa opcional.

### `mcp_refresh_tokens`

- somente hash do token;
- grant e família de rotação;
- emissão, expiração, consumo e revogação.

Access tokens serão assinados, de curta duração e vinculados ao grant; o valor bruto não será persistido. Códigos e refresh tokens nunca serão armazenados em texto puro.

## 8. Ferramentas expostas

Catálogo inicial remoto e local:

1. `get_readiness_overview`;
2. `get_operation`;
3. `get_employee_profile`, sem custos individuais;
4. `get_operational_fragility`;
5. `get_decision_run`.

Todas recebem anotações `readOnlyHint=true`, `destructiveHint=false`, `idempotentHint=true` e `openWorldHint=false`. Argumentos extras são proibidos. O servidor não oferece ferramenta genérica para chamar URLs, endpoints ou SQL.

O papel mínimo é `viewer`. A camada MCP usa o `sub` do token como ator, não um usuário global como `mcp-local-viewer`.

Cada ferramenta aplica os mesmos limites de visibilidade do usuário na aplicação web. No modelo atual, isso corresponde aos dados que um `viewer` autenticado pode consultar; custos individuais continuam removidos do perfil. Se futuramente houver unidade, contrato ou tenant no RBAC, o filtro deverá entrar nos serviços compartilhados antes de ampliar o MCP.

## 9. Remoção do copiloto interno

Serão removidos do produto e da navegação:

- botão flutuante `IA`;
- `CopilotPanel`;
- rota frontend ou componente de chat;
- endpoints `/copilot/health` e `/copilot/chat`;
- provedor OpenAI e orquestrador conversacional;
- configurações de LLM não utilizadas;
- dependência `openai`, caso nenhum outro módulo a utilize.

O `ToolRegistry` e as ferramentas de leitura permanecem, movidos para um namespace neutro se necessário, porque atendem ao MCP.

## 10. Segurança

- MCP remoto desativado por padrão;
- HTTPS obrigatório fora de desenvolvimento;
- validação estrita do cabeçalho `Origin` no transporte HTTP, incluindo rejeição de origens inesperadas;
- CORS não concede acesso ao endpoint MCP; clientes usam autenticação própria;
- rate limit por usuário, cliente e IP;
- tamanho máximo de payload e timeout explícitos;
- redirect URIs exatas, nunca prefix matching;
- PKCE obrigatório para clientes públicos;
- consentimento explícito antes da primeira conexão;
- tokens curtos e refresh rotation;
- detecção de reutilização de refresh token revoga a família;
- audit trail sem armazenar token, código ou conteúdo secreto;
- endpoint MCP rejeita tokens sem audience correta;
- ferramentas continuam sem escrita;
- revogação individual e revogação administrativa;
- logs nunca registram cabeçalho `Authorization`.

O MVP não implementará um provedor de identidade corporativo próprio. Antes de produção, o authorization server poderá ser substituído ou federado ao IdP/SSO corporativo sem mudar o contrato MCP.

## 11. Compatibilidade e limitações

- Claude e ChatGPT na nuvem precisam alcançar `TWR_PUBLIC_BASE_URL` por HTTPS;
- `localhost` atende somente testes e clientes locais;
- disponibilidade de custom apps/conectores depende do plano, região, papel e política administrativa do Claude/ChatGPT;
- o botão do TWR não pode contornar essas políticas;
- publicação em diretório público é um projeto separado;
- a integração não concede ao TWR acesso à conta ou às conversas do usuário no Claude/ChatGPT;
- o usuário controla e revoga apenas o acesso do cliente externo às ferramentas TWR.

## 12. Estratégia de testes

### Unidade

- PKCE, audience, expiração, assinatura e rotação;
- redirect URI exata;
- hashes de código/refresh token;
- catálogo contém somente ferramentas `READ`;
- ícones e estados acessíveis da sidebar.

### Integração

- metadata OAuth/MCP;
- fluxo authorization code completo;
- login/consentimento por usuário;
- `401` sem token, com token inválido, expirado, audience incorreta ou grant revogado;
- revalidação de usuário desativado;
- usuário A não lista/revoga grants do usuário B;
- MCP remoto e stdio retornam resultados equivalentes;
- nenhuma ferramenta adicional aparece no catálogo.

### Frontend

- item `Claude & ChatGPT` ativo;
- ausência do botão flutuante;
- cartões e estados de conexão;
- cópia da URL MCP;
- revogação exige confirmação e atualiza a lista;
- sidebar expandida e recolhida com nomes acessíveis.

### E2E

- usuário entra, abre conexões, inicia autorização simulada e concede acesso;
- cliente de teste troca código com PKCE;
- cliente chama uma ferramenta MCP e recebe dados;
- usuário revoga o grant;
- chamada seguinte falha com `401`;
- aplicação operacional continua funcionando com MCP remoto desativado.

## 13. Critérios de aceite

1. Não existe chat ou botão flutuante de IA no TWR.
2. A sidebar usa ícones vetoriais consistentes e novo símbolo do produto.
3. `/conexoes-ia` explica e gerencia as conexões do usuário.
4. O endpoint MCP remoto implementa Streamable HTTP e as cinco ferramentas de leitura.
5. Claude/ChatGPT podem descobrir o authorization server e iniciar OAuth 2.1 com PKCE.
6. Um grant pertence a exatamente um usuário e um cliente.
7. Revogação invalida novas chamadas e refreshes.
8. Nenhum segredo aparece em Git, banco em texto puro, resposta pública ou log.
9. Local stdio permanece funcional e equivalente.
10. Backend, frontend, build e E2E ficam verdes.

## 14. Referências

- MCP Authorization: <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- MCP Streamable HTTP: <https://modelcontextprotocol.io/specification/2025-06-18/basic/transports>
- OAuth Protected Resource Metadata (RFC 9728): <https://www.rfc-editor.org/rfc/rfc9728>
- OpenAI Apps no ChatGPT: <https://help.openai.com/en/articles/11487775-connectors-in>
- Anthropic MCP: <https://docs.anthropic.com/en/docs/mcp>
- Odysseus — backends e MCP: <https://github.com/apexEvan/odysseus>
