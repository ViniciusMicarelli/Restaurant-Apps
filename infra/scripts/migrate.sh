#!/usr/bin/env bash
# Roda `alembic upgrade head` em todo microsserviço que tenha um diretório
# `alembic/` (serviços sem persistência real, ex: alguns serviços Tier B
# ainda em construção, são ignorados silenciosamente).
#
# Roda no HOST (fora dos containers), então precisa mapear as MESMAS
# variáveis por serviço que `docker-compose.dev.yml` injeta em cada
# container (`DB__NAME`, `REDIS__DB`, etc. — cada serviço tem seu próprio
# banco/índice Redis, "Database-per-Service"), mas apontando `DB__HOST`/
# `REDIS__HOST`/`RABBITMQ__HOST` para `localhost` em vez do hostname de rede
# Docker (`postgres-db`/`redis-cache`/`rabbitmq`), que só resolve de DENTRO
# dos containers.
#
# Uso:
#   bash infra/scripts/migrate.sh                 # todos os serviços com alembic/
#   bash infra/scripts/migrate.sh order-service    # um serviço específico
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

TARGET="${1:-}"

# shellcheck disable=SC1091
set -a && source .env.dev && set +a

# Nome do serviço -> variável de `.env.dev` com o nome do banco daquele serviço.
declare -A DB_NAME_VAR=(
  [auth-service]="AUTH_DB_NAME"
  [restaurant-service]="RESTAURANT_DB_NAME"
  [menu-service]="MENU_DB_NAME"
  [dining-service]="DINING_DB_NAME"
  [order-service]="ORDERS_DB_NAME"
  [kitchen-service]="KITCHEN_DB_NAME"
  [inventory-service]="INVENTORY_DB_NAME"
  [payment-service]="PAYMENTS_DB_NAME"
  [delivery-service]="DELIVERY_DB_NAME"
  [marketing-service]="MARKETING_DB_NAME"
  [notification-service]="NOTIFICATIONS_DB_NAME"
  [analytics-service]="ANALYTICS_DB_NAME"
)
# Nome do serviço -> variável de `.env.dev` com o índice do Redis (só os
# serviços que declaram `redis: RedisSettings` usam isso; para os demais, a
# variável extra é ignorada por `pydantic-settings` sem erro).
declare -A REDIS_DB_VAR=(
  [auth-service]="AUTH_REDIS_DB"
  [restaurant-service]="RESTAURANT_REDIS_DB"
  [menu-service]="MENU_REDIS_DB"
  [dining-service]="DINING_REDIS_DB"
  [order-service]="ORDERS_REDIS_DB"
  [kitchen-service]="KITCHEN_REDIS_DB"
  [inventory-service]="INVENTORY_REDIS_DB"
  [payment-service]="PAYMENTS_REDIS_DB"
  [delivery-service]="DELIVERY_REDIS_DB"
  [marketing-service]="MARKETING_REDIS_DB"
  [notification-service]="NOTIFICATIONS_REDIS_DB"
  [analytics-service]="ANALYTICS_REDIS_DB"
)

for dir in services/*/; do
  name="$(basename "$dir")"
  [[ -n "$TARGET" && "$name" != "$TARGET" ]] && continue
  [[ -d "${dir}alembic" ]] || continue

  echo "=============================================================="
  echo "==> Rodando migrations: ${name}"
  echo "=============================================================="

  db_name_var="${DB_NAME_VAR[$name]:-}"
  redis_db_var="${REDIS_DB_VAR[$name]:-}"

  (
    cd "$dir"
    export DB__HOST=localhost
    export DB__PORT="$DB__PORT"
    export DB__USER="$DB__USER"
    export DB__PASSWORD="$DB__PASSWORD"
    export DB__NAME="${!db_name_var:-}"
    export REDIS__HOST=localhost
    export REDIS__PORT="$REDIS_PORT"
    export REDIS__DB="${!redis_db_var:-0}"
    export MEILISEARCH_MASTER_KEY="$MEILI_MASTER_KEY"
    export RABBITMQ__HOST=localhost
    export RABBITMQ__PORT="$RABBITMQ_PORT"
    export RABBITMQ__USER="$RABBITMQ_USER"
    export RABBITMQ__PASSWORD="$RABBITMQ_PASS"
    uv run alembic upgrade head
  )
done

echo "==> Migrations concluídas."
