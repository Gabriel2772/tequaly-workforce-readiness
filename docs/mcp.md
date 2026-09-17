# Cadastro de conexões e MCP local

> Status: implementado.

## Duas superfícies separadas

`/conexoes-mcp` é um cadastro de configurações individuais, não um cliente MCP. Exige sessão TWR e cada operação deriva o proprietário do cookie autenticado; o navegador nunca envia `user_id`. O Claude ou ChatGPT recebe a configuração fora do TWR, conforme plano e permissões administrativas do cliente escolhido.

O servidor local é uma superfície técnica separada:

```text
Cliente MCP -> stdio -> adaptador MCP -> ToolRegistry -> serviços da aplicação
```

Ele é iniciado em `backend` com:

```powershell
uv run python -m app.mcp_server
```

## Schema persistido

A migração `0010_user_mcp_connections` cria `user_mcp_connections` com `id`, `user_id`, `name`, `client_type`, `endpoint_url`, `transport`, `notes`, `enabled`, `last_validated_at`, `created_at` e `updated_at`. A constraint `uq_user_mcp_connection_name` impede nome repetido para o mesmo usuário e destino. Não existe coluna de segredo.

## API autenticada

- `GET /mcp-connections`: lista somente registros do ator;
- `POST /mcp-connections`: cria um registro para o ator;
- `PATCH /mcp-connections/{id}`: edita ou ativa/desativa um registro do ator;
- `POST /mcp-connections/{id}/validate`: valida estrutura e atualiza `last_validated_at`;
- `DELETE /mcp-connections/{id}`: exclui um registro do ator;
- `GET /mcp-connections/catalog`: lista as cinco ferramentas locais somente leitura.

Registro inexistente e registro de outro usuário retornam o mesmo `404`. Duplicidade da constraint nominal retorna `409`; outros erros de integridade não são mascarados.

## Validação e segurança

- remoto exige HTTPS; HTTP é aceito apenas para `localhost` em desenvolvimento;
- userinfo, fragmentos, authorities malformadas e chaves de query de credencial são rejeitados;
- `monkey`, `author` e `hockey` são chaves legítimas e não são falsos positivos;
- nenhum request de rede é feito durante a validação;
- auditoria contém apenas `client_type`, `transport` e `enabled`, sem URL ou notas;
- a configuração copiável contém somente nome, URL e transporte.

## Catálogo local

As cinco ferramentas descritas em `docs/ai-tools.md` são de leitura, idempotentes e sem acesso externo. Não há ferramentas de solver, seleção, outcome, importação, calibração ou qualquer escrita. O perfil profissional omite custos individuais.

Não há transporte MCP HTTP hospedado pelo TWR nesta entrega. Um endpoint remoto cadastrado pertence a um servidor confiável administrado fora da aplicação.
