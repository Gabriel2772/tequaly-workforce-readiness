# Cadastro de conex�es e MCP local

> Status: implementado.

## Duas superf�cies separadas

`/conexoes-mcp` � um cadastro de configura��es individuais, n�o um cliente MCP. Exige sess�o TWR e cada opera��o deriva o propriet�rio do cookie autenticado; o navegador nunca envia `user_id`. O Claude ou ChatGPT recebe a configura��o fora do TWR, conforme plano e permiss�es administrativas do cliente escolhido.

O servidor local � uma superf�cie t�cnica separada:

```text
Cliente MCP -> stdio -> adaptador MCP -> ToolRegistry -> servi�os da aplica��o
```

Ele � iniciado em `backend` com:

```powershell
uv run python -m app.mcp_server
```

## Schema persistido

A migra��o `0010_user_mcp_connections` cria `user_mcp_connections` com `id`, `user_id`, `name`, `client_type`, `endpoint_url`, `transport`, `notes`, `enabled`, `last_validated_at`, `created_at` e `updated_at`. A constraint `uq_user_mcp_connection_name` impede nome repetido para o mesmo usu�rio e destino. N�o existe coluna de segredo.

## API autenticada

- `GET /mcp-connections`: lista somente registros do ator;
- `POST /mcp-connections`: cria um registro para o ator;
- `PATCH /mcp-connections/{id}`: edita ou ativa/desativa um registro do ator;
- `POST /mcp-connections/{id}/validate`: valida estrutura e atualiza `last_validated_at`;
- `DELETE /mcp-connections/{id}`: exclui um registro do ator;
- `GET /mcp-connections/catalog`: lista as cinco ferramentas locais somente leitura.

Registro inexistente e registro de outro usu�rio retornam o mesmo `404`. Duplicidade da constraint nominal retorna `409`; outros erros de integridade n�o s�o mascarados.

## Valida��o e seguran�a

- remoto exige HTTPS; HTTP � aceito apenas para `localhost` em desenvolvimento;
- userinfo, fragmentos, authorities malformadas e chaves de query de credencial s�o rejeitados;
- `monkey`, `author` e `hockey` s�o chaves leg�timas e n�o s�o falsos positivos;
- nenhum request de rede � feito durante a valida��o;
- auditoria cont�m apenas `client_type`, `transport` e `enabled`, sem URL ou notas;
- a configura��o copi�vel cont�m somente nome, URL e transporte.

## Cat�logo local

As cinco ferramentas descritas em `docs/ai-tools.md` s�o de leitura, idempotentes e sem acesso externo. N�o h� ferramentas de solver, sele��o, outcome, importa��o, calibra��o ou qualquer escrita. O perfil profissional omite custos individuais.

N�o h� transporte MCP HTTP hospedado pelo TWR nesta entrega. Um endpoint remoto cadastrado pertence a um servidor confi�vel administrado fora da aplica��o.
