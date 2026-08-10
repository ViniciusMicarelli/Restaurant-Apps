#!/usr/bin/env bash
# Sobe a stack completa de desenvolvimento (Postgres/Redis/RabbitMQ/Meilisearch
# + os 12 microsserviços + os 3 processos de `workers/`) e aplica as
# migrations Alembic pendentes.
#
# IMPORTANTE: `docker compose` só lê `.env` automaticamente — como este
# projeto usa `.env.dev`/`.env.prod` (nunca um `.env` genérico, ver ADR-005),
# é obrigatório passar `--env-file` explicitamente. Rodar o comando "na mão"
# sem essa flag faz toda variável `${VAR}` do compose resolver para uma
# string vazia (sintoma: dezenas de "variable is not set" e falha ao subir
# o Postgres com "no port specified"). Use este script para nunca esquecer.
#
# Uso: `bash infra/scripts/dev-up.sh` a partir de qualquer diretório.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

COMPOSE_FILE="infra/docker/docker-compose.dev.yml"
ENV_FILE=".env.dev"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "==> $ENV_FILE não existe — criando a partir de .env.dev.example."
  cp .env.dev.example "$ENV_FILE"
fi

echo "=============================================================="
echo "==> Subindo a stack de desenvolvimento (build + up -d)..."
echo "=============================================================="
docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" up -d --build

echo
echo "=============================================================="
echo "==> Aplicando migrations Alembic pendentes..."
echo "=============================================================="
bash infra/scripts/migrate.sh

echo
echo "=============================================================="
echo "==> Stack no ar. Health checks:"
echo "=============================================================="
# shellcheck disable=SC1090
source "$ENV_FILE"
for pair in \
  "auth-service:${AUTH_SERVICE_PORT}:/api/v1/auth/health" \
  "restaurant-service:${RESTAURANT_SERVICE_PORT}:/api/v1/restaurants/health/check" \
  "menu-service:${MENU_SERVICE_PORT}:/api/v1/menu/health/check" \
  "dining-service:${DINING_SERVICE_PORT}:/api/v1/dining/health/check" \
  "kitchen-service:${KITCHEN_SERVICE_PORT}:/api/v1/kitchen/health/check" \
  "order-service:${ORDER_SERVICE_PORT}:/api/v1/orders/health/check" \
  "inventory-service:${INVENTORY_SERVICE_PORT}:/api/v1/inventory/health/check" \
  "payment-service:${PAYMENT_SERVICE_PORT}:/api/v1/payments/health/check" \
  "delivery-service:${DELIVERY_SERVICE_PORT}:/api/v1/deliveries/health/check" \
  "marketing-service:${MARKETING_SERVICE_PORT}:/api/v1/marketing/health/check" \
  "notification-service:${NOTIFICATION_SERVICE_PORT}:/api/v1/notifications/health/check" \
  "analytics-service:${ANALYTICS_SERVICE_PORT}:/api/v1/analytics/health/check"; do
  name="${pair%%:*}"
  rest="${pair#*:}"
  port="${rest%%:*}"
  path="${rest#*:}"
  echo "  http://localhost:${port}${path}  (${name})"
done
echo
echo "==> Para derrubar a stack: bash infra/scripts/dev-down.sh"
