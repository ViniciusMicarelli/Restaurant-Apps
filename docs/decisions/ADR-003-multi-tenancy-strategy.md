# ADR-003: Estratégia de Isolamento Multi-Tenancy (SaaS)

* **Status**: Aprovado
* **Data**: 2026-08-04
* **Decisores**: Arquiteto de Software Sênior

---

## Contexto e Problema

Como uma plataforma SaaS voltada para restaurantes, precisamos garantir o isolamento absoluto de dados entre estabelecimentos concorrentes. O vazamento de dados de pedidos, clientes ou faturamento entre restaurantes seria uma falha gravíssima e inaceitável.

---

## Opções Consideradas

1. **Database-per-Tenant (Um Banco de Dados isolado por restaurante)**:
   * *Prós*: Isolamento físico completo.
   * *Contras*: Custo operacional e financeiro proibitivo para centenas/milhares de pequenos restaurantes; migrações de esquema complexas.
2. **Schema-per-Tenant (Um PostgreSQL Schema por restaurante no mesmo banco)**:
   * *Prós*: Isolamento lógico forte no banco; facilidade de backup individual.
   * *Contras*: Overhead de manutenção de conexões e pool de banco; limite de schemas no Postgres em escala massiva.
3. **Row-Level Isolation / Discriminator Column (`tenant_id` mandatory in all tables)**:
   * *Prós*: Alta performance, custo-efetivo, excelente utilização do pool de conexões, migrações simplificadas.
   * *Contras*: Exige garantias absolutas na camada do ORM para que NENHUMA query seja executada sem o filtro do `tenant_id`.

---

## Decisão

Decidimos adotar a **Row-Level Isolation (Discriminator Column `tenant_id`)** combinada com **SQLAlchemy Event Listeners no ORM** e **PostgreSQL Row Level Security (RLS)** como camada dupla de proteção.

---

## Mecanismo de Garantia
1. Todas as tabelas no PostgreSQL derivam de uma classe base `TenantAwareModel` que inclui a coluna `tenant_id: Mapped[UUID]`.
2. Um Middleware no FastAPI (`TenantContextMiddleware`) extrai o `tenant_id` do Token JWT assinado ou Subdomínio e registra no contexto assíncrono da requisição (`ContextVar`).
3. O SQLAlchemy automaticamente injeta `WHERE tenant_id = :current_tenant_id` em 100% das consultas de leitura e escrita.
4. No banco de dados PostgreSQL, aplicamos políticas RLS (`CREATE POLICY tenant_isolation_policy ON ... USING (tenant_id = current_setting('app.current_tenant_id'))`).
