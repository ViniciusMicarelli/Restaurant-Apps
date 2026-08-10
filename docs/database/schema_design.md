# 📊 Design de Schema — Tabelas, Índices e Particionamento

> Complementa [`DATABASE.md`](../DATABASE.md). Fecha a lacuna apontada na auditoria de
> 2026-08-04 (link presente no índice do README sem conteúdo correspondente).

## Colunas base (todo modelo, via `restaurant_database.BaseDBModel`)

| Coluna | Tipo | Descrição |
|---|---|---|
| `id` | `GUID` (UUIDv7) | PK, ordenável no tempo (`restaurant_core.ids.generate_uuid7`) |
| `tenant_id` | `GUID` | Presente em todo `TenantAwareModel`, indexado, `NOT NULL` |
| `created_at` / `updated_at` | `TIMESTAMPTZ` | Preenchidos automaticamente em UTC |
| `deleted_at` | `TIMESTAMPTZ NULL` | Soft delete — `NULL` = registro ativo |
| `version_id` | `INTEGER` | Lock Otimista (`__mapper_args__ = {"version_id_col": version_id}`) |

`GUID` (`restaurant_database.guid.GUID`) é um `TypeDecorator` agnóstico de
dialeto: usa `UUID` nativo no PostgreSQL (produção) e `CHAR(32)` hex em
outros dialetos — permite testar repositórios contra SQLite em memória sem
sacrificar o tipo nativo em produção.

## Índices obrigatórios

- `tenant_id` — `btree` em toda tabela (herdado de `TenantAwareModel`).
- Colunas de busca operacional (`pg_trgm`): `unaccent(name) gin_trgm_ops` em
  `inventory_items.name`, `users.phone`; `tsvector` em `orders`/`audit_logs`
  para busca textual de backoffice (ver `ADR-006`).
- Chaves estrangeiras entre agregados do mesmo serviço sempre indexadas
  (ex.: `order_items.order_id`).

## Particionamento

Diferido para a Fase 4/5 do `ROADMAP.md` (volume ainda não justifica). Quando
necessário, o candidato natural é particionamento por `tenant_id` (hash) em
tabelas de altíssimo volume (`orders`, `order_items`, `audit_logs`), mantendo
compatibilidade com a política RLS existente.

## Migrations

Cada serviço mantém seu próprio diretório `alembic/` (uma migration history
por banco — Database-per-Service). Convenção: a primeira migration
(`0001_initial_schema`) cria todas as tabelas do domínio do serviço; nenhuma
migration usa `DROP TABLE`/`DROP COLUMN` destrutivo sem uma etapa de
depreciação prévia documentada no `CHANGELOG.md`.

## Concorrência

- **Optimistic Locking** (`version_id`): usado por padrão em toda entidade
  (`SQLAlchemyRepository.save()` traduz `StaleDataError` em
  `OptimisticLockException` → HTTP 409).
- **Pessimistic Locking / Redis Redlock**: reservado para operações de caixa
  (`payment-service`) e baixa concorrente de estoque (`inventory-service`),
  onde um conflito deve bloquear em vez de falhar e pedir novo retry ao
  usuário.
