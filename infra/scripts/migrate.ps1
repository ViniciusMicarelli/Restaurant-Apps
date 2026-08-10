# Roda `alembic upgrade head` em todo microsservico que tenha um diretorio
# `alembic/` (servicos sem persistencia real ainda sao ignorados silenciosamente).
#
# Roda no HOST (fora dos containers), entao precisa mapear as MESMAS
# variaveis por servico que `docker-compose.dev.yml` injeta em cada
# container (`DB__NAME`, `REDIS__DB`, etc.), mas apontando `DB__HOST`/
# `REDIS__HOST`/`RABBITMQ__HOST` para `localhost` em vez do hostname de rede
# Docker, que so resolve de DENTRO dos containers.
#
# Uso:
#   powershell -File infra/scripts/migrate.ps1
#   powershell -File infra/scripts/migrate.ps1 -Target order-service
param(
    [string]$Target = ""
)
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$EnvValues = @{}
Get-Content ".env.dev" | ForEach-Object {
    if ($_ -match '^\s*([A-Z_][A-Z0-9_]*)=(.*)$') {
        $EnvValues[$Matches[1]] = $Matches[2]
    }
}

$DbNameVar = @{
    "auth-service" = "AUTH_DB_NAME"; "restaurant-service" = "RESTAURANT_DB_NAME"
    "menu-service" = "MENU_DB_NAME"; "dining-service" = "DINING_DB_NAME"
    "order-service" = "ORDERS_DB_NAME"; "kitchen-service" = "KITCHEN_DB_NAME"
    "inventory-service" = "INVENTORY_DB_NAME"; "payment-service" = "PAYMENTS_DB_NAME"
    "delivery-service" = "DELIVERY_DB_NAME"; "marketing-service" = "MARKETING_DB_NAME"
    "notification-service" = "NOTIFICATIONS_DB_NAME"; "analytics-service" = "ANALYTICS_DB_NAME"
}
$RedisDbVar = @{
    "auth-service" = "AUTH_REDIS_DB"; "restaurant-service" = "RESTAURANT_REDIS_DB"
    "menu-service" = "MENU_REDIS_DB"; "dining-service" = "DINING_REDIS_DB"
    "order-service" = "ORDERS_REDIS_DB"; "kitchen-service" = "KITCHEN_REDIS_DB"
    "inventory-service" = "INVENTORY_REDIS_DB"; "payment-service" = "PAYMENTS_REDIS_DB"
    "delivery-service" = "DELIVERY_REDIS_DB"; "marketing-service" = "MARKETING_REDIS_DB"
    "notification-service" = "NOTIFICATIONS_REDIS_DB"; "analytics-service" = "ANALYTICS_REDIS_DB"
}

Get-ChildItem -Path "services" -Directory | ForEach-Object {
    $name = $_.Name
    if ($Target -and $name -ne $Target) { return }
    if (-not (Test-Path (Join-Path $_.FullName "alembic"))) { return }

    Write-Host "=============================================================="
    Write-Host "==> Rodando migrations: $name"
    Write-Host "=============================================================="

    Push-Location $_.FullName
    try {
        $env:DB__HOST = "localhost"
        $env:DB__PORT = $EnvValues["DB__PORT"]
        $env:DB__USER = $EnvValues["DB__USER"]
        $env:DB__PASSWORD = $EnvValues["DB__PASSWORD"]
        $env:DB__NAME = $EnvValues[$DbNameVar[$name]]
        $env:REDIS__HOST = "localhost"
        $env:REDIS__PORT = $EnvValues["REDIS_PORT"]
        $env:REDIS__DB = $EnvValues[$RedisDbVar[$name]]
        $env:MEILISEARCH_MASTER_KEY = $EnvValues["MEILI_MASTER_KEY"]
        $env:RABBITMQ__HOST = "localhost"
        $env:RABBITMQ__PORT = $EnvValues["RABBITMQ_PORT"]
        $env:RABBITMQ__USER = $EnvValues["RABBITMQ_USER"]
        $env:RABBITMQ__PASSWORD = $EnvValues["RABBITMQ_PASS"]

        uv run alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw "alembic upgrade head falhou em $name (exit $LASTEXITCODE)." }
    } finally {
        Remove-Item Env:\DB__HOST, Env:\DB__PORT, Env:\DB__USER, Env:\DB__PASSWORD, Env:\DB__NAME, `
            Env:\REDIS__HOST, Env:\REDIS__PORT, Env:\REDIS__DB, Env:\MEILISEARCH_MASTER_KEY, `
            Env:\RABBITMQ__HOST, Env:\RABBITMQ__PORT, Env:\RABBITMQ__USER, Env:\RABBITMQ__PASSWORD `
            -ErrorAction SilentlyContinue
        Pop-Location
    }
}

Write-Host "==> Migrations concluidas."
