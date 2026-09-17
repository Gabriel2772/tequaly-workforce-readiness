# Tequaly Workforce Readiness — cadastro individual de MCP e navegação visual

**Data:** 25 de agosto de 2026  
**Status:** implementado; evidências de verificação registradas no handoff
**Substitui:** `2026-08-25-twr-mcp-connections-navigation-design.md`

## 1. Objetivo

Remover o copiloto conversacional e todo o fluxo OAuth planejado anteriormente. O TWR passa a oferecer uma área simples para cada usuário autenticado registrar e organizar as próprias configurações de servidores MCP destinadas ao Claude ou ao ChatGPT. A mesma entrega moderniza a sidebar, seus ícones e o símbolo do produto.

O TWR não incorpora modelos de IA, não hospeda conversas e não utiliza assinatura pessoal ou chave de API de provedores de IA.

## 2. Escopo

### Incluído

- rota autenticada `/conexoes-mcp`;
- item `Conexões MCP` na sidebar;
- cadastro, edição, ativação, desativação e exclusão de conexões;
- isolamento das conexões pelo usuário autenticado;
- destinos `Claude` e `ChatGPT`;
- endpoint MCP remoto HTTPS e transporte `Streamable HTTP` ou `SSE`;
- validação estrutural da configuração;
- instruções específicas e configuração copiável para cada destino;
- catálogo somente leitura das ferramentas MCP locais já existentes;
- manutenção do servidor MCP local por `stdio`;
- remoção integral do frontend e backend do copiloto;
- remoção das estruturas OAuth MCP criadas durante a implementação interrompida;
- sidebar com ícones SVG consistentes;
- novo símbolo vetorial original do Workforce Readiness;
- layout responsivo, acessível e adequado para apresentação;
- testes de API, isolamento entre usuários, componentes, navegação e fluxo E2E.

### Excluído

- chat, histórico ou janela de conversas dentro do TWR;
- OAuth, OIDC, PKCE, consentimento, authorization code, refresh token ou login em Claude/ChatGPT;
- execução de modelos de IA dentro do TWR;
- chaves OpenAI, Anthropic ou de outras APIs de modelos;
- armazenamento de senhas, bearer tokens ou segredos pertencentes aos MCPs cadastrados;
- proxy genérico de chamadas MCP;
- teste de rede do backend para URLs arbitrárias;
- ferramentas MCP de escrita;
- publicação automática em diretórios Claude ou ChatGPT.

## 3. Decisão de arquitetura

O recurso é um **cadastro individual de configurações**, não um cliente MCP embutido. Cada registro documenta como um MCP confiável deve ser configurado no Claude ou ChatGPT. A conversa e a execução das ferramentas acontecem no cliente escolhido pelo usuário.

Essa separação evita três problemas:

1. sem OAuth, o TWR não pode identificar com segurança o usuário que chega de um cliente remoto;
2. testar URLs arbitrárias a partir do backend abriria risco de SSRF;
3. guardar tokens de MCP aumentaria o risco operacional sem trazer valor ao fluxo sem chat.

O botão `Validar configuração` verifica formato, compatibilidade e campos obrigatórios, mas não afirma que o servidor remoto está online. O teste funcional final é realizado no próprio Claude ou ChatGPT ao importar a configuração.

## 4. Modelo de dados

Nova entidade `UserMcpConnection`:

- `id`: UUID;
- `user_id`: dono da conexão, com chave estrangeira para `app_users`;
- `name`: nome de exibição definido pelo usuário;
- `client_type`: `claude` ou `chatgpt`;
- `endpoint_url`: URL do servidor MCP;
- `transport`: `streamable_http` ou `sse`;
- `notes`: observação opcional, limitada e tratada como texto;
- `enabled`: estado local ativo/inativo;
- `created_at` e `updated_at`;
- `last_validated_at`: instante da última validação estrutural bem-sucedida.

Não haverá coluna de segredo. URLs com `userinfo`, fragmento ou credenciais aparentes serão rejeitadas. Para conexões remotas, HTTPS é obrigatório, exceto localhost durante desenvolvimento.

Índice e restrição de unicidade impedem nomes duplicados para o mesmo usuário e destino. Usuários diferentes podem usar o mesmo nome e endpoint.

## 5. API autenticada

Endpoints sob `/mcp-connections`:

- `GET /`: lista somente conexões do usuário atual;
- `POST /`: cria conexão para o usuário atual;
- `PATCH /{connection_id}`: altera somente uma conexão pertencente ao usuário atual;
- `POST /{connection_id}/validate`: executa validação estrutural, sem acesso de rede;
- `DELETE /{connection_id}`: exclui somente uma conexão pertencente ao usuário atual;
- `GET /catalog`: retorna o catálogo público das ferramentas MCP somente leitura do TWR.

Regras obrigatórias:

- nunca aceitar `user_id` enviado pelo navegador;
- filtrar todas as operações pelo ator autenticado;
- retornar `404` tanto para identificador inexistente quanto para registro de outro usuário;
- usar esquemas de entrada e saída explícitos;
- registrar alterações relevantes na auditoria existente sem incluir notas completas ou URLs sensíveis;
- limitar nome, URL e notas para evitar abuso de armazenamento.

## 6. Experiência da página `/conexoes-mcp`

A página terá:

1. cabeçalho explicando que o TWR organiza configurações MCP e não contém chat;
2. dois cartões de destino, `Claude` e `ChatGPT`, com disponibilidade e limitações conhecidas;
3. lista das conexões do usuário com busca e filtros por destino/estado;
4. formulário em modal ou painel lateral para criar e editar;
5. ação `Validar configuração` com resultado claro: válida, incompleta ou incompatível;
6. ação `Copiar configuração`, que gera um exemplo sem segredos;
7. instruções passo a passo para levar a URL ao cliente escolhido;
8. confirmação antes de excluir.

Estados visuais:

- vazio com chamada para cadastrar o primeiro MCP;
- carregando;
- erro recuperável;
- conexão ativa/inativa;
- configuração estruturalmente válida;
- configuração que exige correção;
- ambiente local, com aviso de que clientes em nuvem normalmente exigem URL pública;
- recurso externo indisponível por plano ou permissão administrativa.

O ChatGPT será descrito como dependente da disponibilidade de apps MCP e das permissões do workspace. O Claude será descrito como compatível com conectores MCP remotos, respeitando as regras do plano do usuário. A interface não promete abrir sessão nem instalar o conector automaticamente.

## 7. Sidebar, ícones e identidade

A sidebar manterá os destinos atuais, substituindo abreviações por ícones SVG de traço uniforme, área de clique adequada e rótulos acessíveis. `Conexões MCP` usará um símbolo de plugue e nós conectados.

O bloco com a letra `T` será substituído por um símbolo vetorial original `T/W` com nós de conexão e sinal de prontidão. Ele não tenta reproduzir uma marca corporativa oficial da Tequaly.

Comportamentos obrigatórios:

- indicação ativa que não dependa somente de cor;
- foco de teclado visível;
- tooltip ou `aria-label` na sidebar recolhida;
- navegação compacta em telas médias;
- menu móvel funcional sem sobrepor o conteúdo;
- ausência total do botão flutuante e do painel do copiloto.

## 8. Remoção do escopo anterior

Serão retirados de forma controlada:

- modelos, migração, repositório, provider e primitivas de OAuth MCP;
- configurações de segredo, issuer, redirect hosts e duração de tokens;
- testes exclusivos do OAuth MCP;
- rotas de consentimento e autorização ainda não integradas;
- backend `app/ai`, seus endpoints e configurações de provedor;
- componente, testes, estilos e E2E do copiloto;
- referências de documentação que afirmem existir chat ou OAuth.

O registro compartilhado de ferramentas determinísticas e o servidor MCP local por `stdio` serão preservados e desacoplados de `app/ai` quando necessário.

## 9. Testes e aceitação

### Backend

- CRUD completo da entidade;
- isolamento entre dois usuários;
- rejeição de URL insegura ou com credenciais;
- localhost permitido apenas em desenvolvimento;
- limites de tamanho e enumerações;
- catálogo somente leitura;
- ausência de rotas e configurações OAuth/copiloto.

### Frontend

- renderização dos estados da página;
- criação, edição, validação, cópia, ativação e exclusão;
- mensagens de erro e confirmação;
- ícones, rótulos e foco acessíveis;
- sidebar desktop, recolhida e móvel;
- ausência do launcher/painel do copiloto.

### E2E

Um usuário cria uma conexão Claude, valida, copia a configuração, desativa, reativa e exclui. Uma conexão criada por outro usuário não aparece nem pode ser alterada. A navegação pela sidebar funciona nas larguras desktop e móvel.

## 10. Compatibilidade e limites assumidos

- o cadastro pode ser usado sem OAuth porque o TWR não autentica nem executa o servidor remoto cadastrado;
- a configuração não contém segredos; autenticação eventualmente exigida pelo MCP é concluída no próprio Claude ou ChatGPT;
- MCP remoto depende de endpoint alcançável pelo cliente escolhido;
- o ChatGPT pode restringir criação de apps MCP por plano, função ou administrador;
- o Claude pode exigir configuração pelo proprietário em organizações Team/Enterprise;
- o servidor MCP local `stdio` continua voltado ao uso técnico e desenvolvimento.

## 11. Critério de conclusão

A entrega está pronta quando o usuário consegue gerenciar suas configurações MCP sem visualizar qualquer chat ou fluxo OAuth, a sidebar está visualmente consistente e responsiva, a suíte completa passa e a documentação/pacote de continuidade descrevem apenas o comportamento realmente entregue.
