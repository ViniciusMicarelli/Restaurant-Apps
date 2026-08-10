# 🛡️ Arquitetura Detalhada de Segurança

> Complementa [`SECURITY.md`](../SECURITY.md) com o desenho técnico efetivamente
> implementado em `packages/security` e `packages/database`. Fecha a lacuna apontada
> na auditoria de 2026-08-04 (link presente no índice do README sem conteúdo
> correspondente).

## Isolamento de Tenants (Row-Level Isolation — ADR-003)

Três camadas independentes, nenhuma delas opcional:

1. **Aplicação**: `restaurant_security.TenantContextMiddleware` extrai o `tenant_id`
   do JWT (claim `tenant_id`) ou do header `X-Tenant-Id` (rotas públicas
   pré-login, ex.: cardápio via QR Code) e o publica em um `ContextVar` por
   requisição.
2. **Repositório**: `restaurant_database.SQLAlchemyRepository` recebe o
   `tenant_id` corrente no construtor e injeta `WHERE tenant_id = :tenant_id`
   em toda leitura/escrita — nenhum método do repositório aceita bypass.
3. **Banco de dados**: `TenantAwareModel.tenant_id` é indexado e `NOT NULL`
   em toda tabela operacional; a política RLS do PostgreSQL (`CREATE POLICY
   tenant_isolation_policy ON <tabela> USING (tenant_id =
   current_setting('app.current_tenant_id'))`) é a rede de segurança final
   caso a camada de aplicação falhe.

## Gestão de Segredos

- Nenhum segredo em código-fonte: 100% via `pydantic-settings` +
  `.env`/`.env.dev`/`.env.prod` (nunca commitados — ver `.gitignore`).
- `SecretStr` em toda credencial (`DB__PASSWORD`, `JWT_SECRET_KEY`,
  `MEILI_MASTER_KEY`, `RABBITMQ_PASS`) para nunca vazar em logs/`repr()`.
- Falha rápida: se uma variável obrigatória faltar, o container não sobe
  (`pydantic-settings` levanta `ValidationError` na importação de `config.py`).
- Produção: `DB__*` aponta para uma instância PostgreSQL gerenciada externa
  (não roda em container) — ver `docs/deploy/infrastructure_strategy.md`.

## Autenticação e Tokens (JWT)

Implementado em `restaurant_security.jwt`:

- Algoritmo `HS256`, segredo simétrico compartilhado entre todos os
  microsserviços (permite cada serviço validar o token localmente sem chamar
  o `auth-service` a cada requisição).
- Claims: `sub` (user_id), `tenant_id`, `role`, `jti` (único por token,
  permite revogação), `iat`, `exp`.
- Access token: 15 min. Refresh token: 7 dias, entregue via cookie
  `HttpOnly; Secure; SameSite=Strict` (nunca em `localStorage`).
- Hash de senha/PIN: Argon2id (`restaurant_security.hash`), parâmetros OWASP
  (`time_cost=3`, `memory_cost=65536`, `parallelism=4`).

## RBAC/ABAC

`restaurant_security.rbac` fornece `build_get_current_user(jwt_secret_key)` e
`require_role(*roles)` como dependencies FastAPI. Papéis: `SUPER_ADMIN`,
`RESTAURANT_OWNER`, `MANAGER`, `CASHIER`, `WAITER`, `KITCHEN_STAFF`,
`CUSTOMER` (`docs/SECURITY.md §3`). Regras ABAC finas (ex.: garçom só fecha
comanda de mesa atribuída a ele) são resolvidas no `application/use_cases/`
de cada serviço, não no middleware genérico.

## Erros e Auditoria

- Toda exceção de domínio (`restaurant_core.exceptions.BaseDomainException`)
  vira uma resposta RFC 7807 (`restaurant_common.problem_details`) — nunca um
  stack trace cru.
- Ações sensíveis (cancelamento de pedido, sangria de caixa, alteração de
  preço, concessão de desconto) publicam um evento de auditoria
  (`packages/events`) consumido pelo `analytics-service`, que persiste em
  `audit_logs` (imutável, ver `docs/SECURITY.md §4`).
