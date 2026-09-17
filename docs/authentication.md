# Autenticação e perfis

O backend emite uma sessão assinada em cookie `HttpOnly`, com duração padrão de oito horas. Senhas são armazenadas com `scrypt`, o usuário ativo e o perfil são revalidados a cada ação protegida e mensagens de login não revelam se uma conta existe.

## Perfis

- `viewer`: consultas e exportações;
- `planner`: ações operacionais, elegibilidade, otimização, seleção e registro de resultados;
- `admin`: tudo que o planejador executa, além das importações controladas.

O seed cria três contas exclusivamente para apresentação: `viewer.demo`, `planner.demo` e `admin.demo`. A senha sintética comum é `TequalyDemo!2026`. Essas contas não devem ser usadas em produção.

## Modos

`TWR_AUTH_REQUIRED=false` preserva o modo local de demonstração e aceita os cabeçalhos legados apenas para testes e execução local. Com `TWR_AUTH_REQUIRED=true`, esses cabeçalhos são ignorados: é obrigatório apresentar cookie ou `Bearer` assinado. Ambientes não classificados como desenvolvimento também exigem a troca de `TWR_SESSION_SECRET`.

Em produção, configure:

```text
TWR_AUTH_REQUIRED=true
TWR_SESSION_SECRET=<segredo-longo-e-aleatório>
TWR_SECURE_COOKIES=true
```

O mecanismo atual é adequado para o artefato demonstrável e pode ser substituído por SSO/OIDC corporativo sem alterar as regras do núcleo.
