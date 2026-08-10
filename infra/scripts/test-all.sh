#!/usr/bin/env bash
# Roda a suíte Pytest de cada package/serviço Python de forma independente
# (cada um com seu próprio `pythonpath`/config — ver docs/testing/test_strategy.md),
# agregando o resultado final. Uso: `bash infra/scripts/test-all.sh` a partir
# da raiz do repositório.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

FAILED=()
PASSED=()

for dir in packages/*/ services/*/ workers/; do
  [[ -f "${dir}pyproject.toml" ]] || continue
  name="$(basename "$dir")"
  echo "=============================================================="
  echo "==> Testando: ${name}"
  echo "=============================================================="
  if (cd "$dir" && uv run pytest -q); then
    PASSED+=("$name")
  else
    FAILED+=("$name")
  fi
done

echo
echo "=============================================================="
echo "Resumo"
echo "=============================================================="
echo "Passou (${#PASSED[@]}): ${PASSED[*]:-nenhum}"
echo "Falhou (${#FAILED[@]}): ${FAILED[*]:-nenhum}"

if [[ ${#FAILED[@]} -gt 0 ]]; then
  exit 1
fi
