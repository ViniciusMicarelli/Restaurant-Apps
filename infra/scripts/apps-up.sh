#!/usr/bin/env bash
# Sobe os 4 apps de frontend (admin-web, customer-web, waiter-mobile,
# customer-mobile) em segundo plano, apontando pro backend do
# docker-compose.dev.yml em localhost. NÃO sobe o backend em si — rode
# `bash infra/scripts/dev-up.sh` antes (uma vez só).
#
# Uso:
#   bash infra/scripts/apps-up.sh              # os 4 apps
#   bash infra/scripts/apps-up.sh --web-only    # só admin-web/customer-web (pula os Flutter, mais lentos pra buildar)
#
# Cada app roda em background com o log redirecionado pra
# infra/scripts/.apps-logs/<app>.log (já no .gitignore via infra/**/*.log).
# Pra acompanhar: `tail -f infra/scripts/.apps-logs/admin-web.log`.
# Pra parar tudo: `kill $(cat infra/scripts/.apps-logs/apps.pids.log)`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

WEB_ONLY=false
if [[ "${1:-}" == "--web-only" ]]; then
    WEB_ONLY=true
fi

LOG_DIR="infra/scripts/.apps-logs"
mkdir -p "$LOG_DIR"
PID_FILE="$LOG_DIR/apps.pids.log"
: > "$PID_FILE"

echo "=============================================================="
echo "==> Checando se o backend (docker-compose.dev.yml) esta no ar..."
echo "=============================================================="
if curl -s -o /dev/null -m 3 "http://localhost:8000/api/v1/auth/health"; then
    echo "OK - auth-service respondeu em localhost:8000."
else
    echo "AVISO: backend nao respondeu em localhost:8000."
    echo "       Os apps vao subir mesmo assim, mas vao ficar travados em"
    echo "       tela de carregamento ate voce rodar:"
    echo "       bash infra/scripts/dev-up.sh"
fi

start_app() {
    local name="$1" workdir="$2"
    shift 2
    (cd "$workdir" && "$@" > "$REPO_ROOT/$LOG_DIR/$name.log" 2>&1 &
     echo $! >> "$REPO_ROOT/$PID_FILE")
    echo "==> Iniciado: $name (log em $LOG_DIR/$name.log)"
}

echo ""
echo "=============================================================="
echo "==> Subindo os apps..."
echo "=============================================================="

start_app "admin-web" "apps/admin-web" npm run dev
start_app "customer-web" "apps/customer-web" npm run dev

if [[ "$WEB_ONLY" == false ]]; then
    start_app "waiter-mobile" "apps/waiter-mobile" flutter run -d web-server --web-port=5001 --web-hostname=0.0.0.0 \
        --dart-define=AUTH_SERVICE_URL=http://localhost:8000 \
        --dart-define=RESTAURANT_SERVICE_URL=http://localhost:8001 \
        --dart-define=DINING_SERVICE_URL=http://localhost:8003 \
        --dart-define=MENU_SERVICE_URL=http://localhost:8002 \
        --dart-define=ORDER_SERVICE_URL=http://localhost:8005

    start_app "customer-mobile" "apps/customer-mobile" flutter run -d web-server --web-port=5002 --web-hostname=0.0.0.0 \
        --dart-define=RESTAURANT_SERVICE_URL=http://localhost:8001 \
        --dart-define=MENU_SERVICE_URL=http://localhost:8002
fi

echo ""
echo "=============================================================="
echo "==> Apps subindo em segundo plano. URLs (podem levar alguns"
echo "    segundos/minutos pra compilar, principalmente os Flutter):"
echo "=============================================================="
echo "  Painel do Gestor (admin-web)....... http://localhost:3001"
echo "  Cardapio Digital (customer-web)..... http://localhost:3000"
echo "    (o cardapio exige um QR valido - gere um pelo admin-web: Mesas -> icone da mesa)"
if [[ "$WEB_ONLY" == false ]]; then
    echo "  App do Garcom (waiter-mobile)....... http://localhost:5001"
    echo "  App do Cliente (customer-mobile)..... http://localhost:5002"
fi
echo ""
echo "Logs em $LOG_DIR/*.log — pra parar tudo: kill \$(cat $PID_FILE)"
