# Autentica��o e perfis

O backend emite uma sess�o assinada em cookie `HttpOnly`, com dura��o padr�o de oito horas. Senhas s�o armazenadas com `scrypt`, o usu�rio ativo e o perfil s�o revalidados a cada a��o protegida e mensagens de login n�o revelam se uma conta existe.

## Perfis

- `viewer`: consultas e exporta��es;
- `planner`: a��es operacionais, elegibilidade, otimiza��o, sele��o e registro de resultados;
- `admin`: tudo que o planejador executa, al�m das importa��es controladas.

O seed cria tr�s contas exclusivamente para apresenta��o: `viewer.demo`, `planner.demo` e `admin.demo`. A senha sint�tica comum � `TequalyDemo!2026`. Essas contas n�o devem ser usadas em produ��o.

## Modos

`TWR_AUTH_REQUIRED=false` preserva o modo local de demonstra��o e aceita os cabe�alhos legados apenas para testes e execu��o local. Com `TWR_AUTH_REQUIRED=true`, esses cabe�alhos s�o ignorados: � obrigat�rio apresentar cookie ou `Bearer` assinado. Ambientes n�o classificados como desenvolvimento tamb�m exigem a troca de `TWR_SESSION_SECRET`.

Em produ��o, configure:

```text
TWR_AUTH_REQUIRED=true
TWR_SESSION_SECRET=<segredo-longo-e-aleat�rio>
TWR_SECURE_COOKIES=true
```

O mecanismo atual � adequado para o artefato demonstr�vel e pode ser substitu�do por SSO/OIDC corporativo sem alterar as regras do n�cleo.
