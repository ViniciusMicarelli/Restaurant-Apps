#!/usr/bin/env bash
# Roda automaticamente pelo entrypoint oficial da imagem `postgres` (montado em
# /docker-entrypoint-initdb.d/) na PRIMEIRA inicialização do volume de dados.
#
# Cria um banco PostgreSQL por microsserviço dentro do mesmo cluster
# (Database-per-Service, ver docs/DATABASE.md), já que o `POSTGRES_DB` da
# imagem oficial só cria um único banco por padrão.
set -euo pipefail

SERVICE_DATABASES=(
  "${AUTH_DB_NAME:-auth_db}"
  "${RESTAURANT_DB_NAME:-restaurant_db}"
  "${MENU_DB_NAME:-menu_db}"
  "${DINING_DB_NAME:-dining_db}"
  "${KITCHEN_DB_NAME:-kitchen_db}"
  "${ORDERS_DB_NAME:-orders_db}"
  "${INVENTORY_DB_NAME:-inventory_db}"
  "${PAYMENTS_DB_NAME:-payments_db}"
  "${DELIVERY_DB_NAME:-delivery_db}"
  "${MARKETING_DB_NAME:-marketing_db}"
  "${NOTIFICATIONS_DB_NAME:-notifications_db}"
  "${ANALYTICS_DB_NAME:-analytics_db}"
)

for db_name in "${SERVICE_DATABASES[@]}"; do
  echo "==> Garantindo existência do banco '${db_name}'"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
    -tc "SELECT 1 FROM pg_database WHERE datname = '${db_name}'" | grep -q 1 \
    || psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
      -c "CREATE DATABASE \"${db_name}\" OWNER \"$POSTGRES_USER\";"

  echo "==> Habilitando extensões de busca em '${db_name}' (pg_trgm, unaccent)"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db_name" \
    -c "CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS unaccent;"
done
