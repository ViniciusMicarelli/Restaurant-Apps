# 𛄢 Mapeamento e Arquitetura de Banco de Dados — Restaurant Apps Platform

## 1. Visão Geral da Camada de Dados em Microsserviços

A **Restaurant Apps Platform** adota o padrão **Database-per-Service** (ou **Schema-per-Service** no mesmo cluster PostgreSQL 16+ para eficiência de recursos na fase inicial).

Cada microsserviço é o **único dono exclusivo do seu banco de dados**. É estritamente proibido um microsserviço realizar queries diretas na tabela de outro microsserviço. Toda comunicação inter-serviços ocorre via APIs gRPC/REST ou Eventos assíncronos (RabbitMQ / Redis PubSub).

---

## 2. Distribuição de Bancos de Dados por Microsserviço

| Microsserviço | Banco Relacional (PostgreSQL) | Cache & Estado Transitório (Redis) | Motor de Busca (Search Engine) |
|---|---|---|---|
| `auth-service` | `auth_db` (Users, Employees, Roles) | Redis DB 0 (Tokens & Sessions) | Postgres `pg_trgm` |
| `restaurant-service` | `restaurant_db` (Tenants, Settings) | Redis DB 1 (Tenant Config Cache) | - |
| `menu-service` | `menu_db` (Categories, Products, Combos) | Redis DB 2 (Cardápio Cache) | **Meilisearch** (FTS Inteligente) |
| `dining-service` | `dining_db` (Tables, Commands, Queue) | Redis DB 3 (Estado de Mesas RT) | Postgres `pg_trgm` |
| `order-service` | `orders_db` (Orders, OrderItems, Sagas) | Redis DB 4 (Idempotency Keys) | Postgres `tsvector` |
| `kitchen-service` | `kitchen_db` (KDS Stations, KDS Items) | Redis DB 5 (PubSub KDS) | - |
| `inventory-service` | `inventory_db` (Insumos, Recipes, Stock) | Redis DB 6 (Stock Lock) | Postgres `pg_trgm` |
| `payment-service` | `payments_db` (Caixa, Payments, Split) | Redis DB 7 (Locks de Caixa) | - |
| `notification-service`| `notifications_db` (Templates, Logs) | Redis DB 8 (Fila de Disparos) | - |
| `analytics-service` | `analytics_db` (Audit Logs, Relatórios) | Redis DB 9 (Analytics Aggregates)| Postgres `tsvector` (Audit FTS) |

---

## 3. Full-Text Search (FTS) & Índices de Busca Inteligente

### 3.1 Índices Trigramas no PostgreSQL (`pg_trgm` + `unaccent`)
Para os microsserviços de backoffice (`dining-service`, `inventory-service`, `auth-service`), habilitamos as extensões navais do PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

-- Exemplo de índice GIN trigrâmico para busca ultra-rápida por nome de insumo ou cliente
CREATE INDEX idx_inventory_items_search_trgm 
ON inventory_items USING gin (unaccent(name) gin_trgm_ops);

CREATE INDEX idx_customers_phone_trgm 
ON users USING gin (phone gin_trgm_ops);
```

### 3.2 Sincronização do Meilisearch no `menu-service`
Quando um produto é cadastrado/atualizado no `menu-service`:
1. A gravação relacional ocorre no `menu_db`.
2. Um handler pós-commit dispara a indexação no **Meilisearch** com o documento JSON:
```json
{
  "id": "019124a5-99df-7f22-92bc-90a1f0a12b45",
  "tenant_id": "019124a1-7c2a-71b3-810a-3199d0c64921",
  "name": "Hambúrguer Artesanal Smash Bacon",
  "description": "Pão brioche, duas carnes smash de 90g, queijo cheddar fatiado e bacon crocante.",
  "category": "Lanches",
  "price": 32.90,
  "tags": ["smash", "cheddar", "bacon", "artesanal"],
  "available": true
}
```

---

## 4. Estratégia de Concorrência e Transações Distribuídas (Saga Pattern)

Como cada microsserviço tem seu banco de dados, transações atômicas ACID de banco de dados só acontecem **dentro do próprio microsserviço**.

Para operações que envolvem múltiplos microsserviços (ex: Criar Pedido -> Reservar Estoque -> Efetuar Pagamento -> Enviar para a Cozinha):
* Utilizaremos o **Padrão Saga por Coreografia**.
* Se o serviço de pagamentos rejeitar o cartão, ele publica o evento `PaymentFailedEvent`.
* O `order-service` escuta o evento e dispara as **Ações de Compensação** (Cancela o pedido e libera o estoque reservado no `inventory-service`).
