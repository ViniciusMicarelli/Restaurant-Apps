#!/usr/bin/env bash
# Derruba a stack de desenvolvimento. Uso: `bash infra/scripts/dev-down.sh`
# (adicione `-v` para também apagar os volumes de dados: `bash infra/scripts/dev-down.sh -v`)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

docker compose --env-file .env.dev -f infra/docker/docker-compose.dev.yml down "$@"
