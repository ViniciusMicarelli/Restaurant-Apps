#!/usr/bin/env bash
# Prepara o ambiente de desenvolvimento local do zero:
#   1. Cria `.env.dev` a partir do exemplo, se ainda não existir.
#   2. Sincroniza o workspace `uv` inteiro (packages/* + services/*).
# Uso: `bash infra/scripts/bootstrap.sh` a partir de qualquer diretório.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f .env.dev ]]; then
  cp .env.dev.example .env.dev
  echo "==> Criado .env.dev a partir de .env.dev.example (ajuste se necessário)."
else
  echo "==> .env.dev já existe, mantido como está."
fi

echo "==> Sincronizando workspace uv (packages/* + services/*)..."
uv sync --all-packages

echo "==> Pronto. Próximos passos:"
echo "    docker compose -f infra/docker/docker-compose.dev.yml up -d --build"
echo "    bash infra/scripts/test-all.sh"
