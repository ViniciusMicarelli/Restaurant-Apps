# Sobe a stack completa de desenvolvimento (Postgres/Redis/RabbitMQ/Meilisearch
# + os 12 microsservicos + os 3 processos de `workers/`) e aplica as
# migrations Alembic pendentes.
#
# IMPORTANTE: `docker compose` so le `.env` automaticamente - como este
# projeto usa `.env.dev`/`.env.prod` (nunca um `.env` generico, ver ADR-005),
# e obrigatorio passar `--env-file` explicitamente. Rodar o comando "na mao"
# sem essa flag faz toda variavel `${VAR}` do compose resolver para uma
# string vazia (sintoma: dezenas de "variable is not set" e falha ao subir
# o Postgres com "no port specified"). Use este script para nunca esquecer.
#
# Uso: `powershell -File infra/scripts/dev-up.ps1` a partir de qualquer diretorio.
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$ComposeFile = "infra/docker/docker-compose.dev.yml"
$EnvFile = ".env.dev"

if (-not (Test-Path $EnvFile)) {
    Write-Host "==> $EnvFile nao existe - criando a partir de .env.dev.example."
    Copy-Item ".env.dev.example" $EnvFile
}

Write-Host "=============================================================="
Write-Host "==> Subindo a stack de desenvolvimento (build + up -d)..."
Write-Host "=============================================================="
docker compose --env-file $EnvFile -f $ComposeFile up -d --build
if ($LASTEXITCODE -ne 0) { throw "docker compose up falhou (exit $LASTEXITCODE)." }

Write-Host ""
Write-Host "=============================================================="
Write-Host "==> Aplicando migrations Alembic pendentes..."
Write-Host "=============================================================="
powershell -File infra/scripts/migrate.ps1

Write-Host ""
Write-Host "=============================================================="
Write-Host "==> Stack no ar. Health checks:"
Write-Host "=============================================================="
$EnvValues = @{}
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)=(.*)$') {
        $EnvValues[$Matches[1]] = $Matches[2]
    }
}

$Checks = @(
    @{ Name = "auth-service"; Port = "AUTH_SERVICE_PORT"; Path = "/api/v1/auth/health" },
    @{ Name = "restaurant-service"; Port = "RESTAURANT_SERVICE_PORT"; Path = "/api/v1/restaurants/health/check" },
    @{ Name = "menu-service"; Port = "MENU_SERVICE_PORT"; Path = "/api/v1/menu/health/check" },
    @{ Name = "dining-service"; Port = "DINING_SERVICE_PORT"; Path = "/api/v1/dining/health/check" },
    @{ Name = "kitchen-service"; Port = "KITCHEN_SERVICE_PORT"; Path = "/api/v1/kitchen/health/check" },
    @{ Name = "order-service"; Port = "ORDER_SERVICE_PORT"; Path = "/api/v1/orders/health/check" },
    @{ Name = "inventory-service"; Port = "INVENTORY_SERVICE_PORT"; Path = "/api/v1/inventory/health/check" },
    @{ Name = "payment-service"; Port = "PAYMENT_SERVICE_PORT"; Path = "/api/v1/payments/health/check" },
    @{ Name = "delivery-service"; Port = "DELIVERY_SERVICE_PORT"; Path = "/api/v1/deliveries/health/check" },
    @{ Name = "marketing-service"; Port = "MARKETING_SERVICE_PORT"; Path = "/api/v1/marketing/health/check" },
    @{ Name = "notification-service"; Port = "NOTIFICATION_SERVICE_PORT"; Path = "/api/v1/notifications/health/check" },
    @{ Name = "analytics-service"; Port = "ANALYTICS_SERVICE_PORT"; Path = "/api/v1/analytics/health/check" }
)
foreach ($check in $Checks) {
    $port = $EnvValues[$check.Port]
    Write-Host "  http://localhost:$port$($check.Path)  ($($check.Name))"
}

Write-Host ""
Write-Host "==> Para derrubar a stack: powershell -File infra/scripts/dev-down.ps1"
