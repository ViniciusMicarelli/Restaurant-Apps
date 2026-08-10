# Sobe os 4 apps de frontend (admin-web, customer-web, waiter-mobile,
# customer-mobile) cada um na sua própria janela de terminal, apontando pro
# backend do docker-compose.dev.yml em localhost. NÃO sobe o backend em si
# — rode `powershell -File infra/scripts/dev-up.ps1` antes (uma vez só).
#
# Uso:
#   powershell -File infra/scripts/apps-up.ps1              # os 4 apps
#   powershell -File infra/scripts/apps-up.ps1 -WebOnly      # só admin-web/customer-web (pula os Flutter, mais lentos pra buildar)
#
# Cada app fica numa janela própria (`-NoExit`) pra você ver os logs e
# reiniciar um de cada vez sem derrubar os outros — pra parar todos, feche as
# janelas ou dê Ctrl+C em cada uma.
param(
    [switch]$WebOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

Write-Host "=============================================================="
Write-Host "==> Checando se o backend (docker-compose.dev.yml) esta no ar..."
Write-Host "=============================================================="
try {
    $null = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/auth/health" -UseBasicParsing -TimeoutSec 3
    Write-Host "OK - auth-service respondeu em localhost:8000."
} catch {
    Write-Host "AVISO: backend nao respondeu em localhost:8000." -ForegroundColor Yellow
    Write-Host "       Os apps vao subir mesmo assim, mas vao ficar travados em" -ForegroundColor Yellow
    Write-Host "       tela de carregamento ate voce rodar:" -ForegroundColor Yellow
    Write-Host "       powershell -File infra/scripts/dev-up.ps1" -ForegroundColor Yellow
}

function Start-AppWindow {
    param(
        [string]$Title,
        [string]$WorkDir,
        [string]$Command
    )
    $fullCommand = "`$host.UI.RawUI.WindowTitle = '$Title'; Set-Location '$WorkDir'; $Command"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $fullCommand | Out-Null
    Write-Host "==> Iniciado: $Title"
}

Write-Host ""
Write-Host "=============================================================="
Write-Host "==> Subindo os apps..."
Write-Host "=============================================================="

Start-AppWindow -Title "admin-web (3001)" `
    -WorkDir (Join-Path $RepoRoot "apps/admin-web") `
    -Command "npm run dev"

Start-AppWindow -Title "customer-web (3000)" `
    -WorkDir (Join-Path $RepoRoot "apps/customer-web") `
    -Command "npm run dev"

if (-not $WebOnly) {
    Start-AppWindow -Title "waiter-mobile (5001)" `
        -WorkDir (Join-Path $RepoRoot "apps/waiter-mobile") `
        -Command ("flutter run -d web-server --web-port=5001 --web-hostname=0.0.0.0 " +
            "--dart-define=AUTH_SERVICE_URL=http://localhost:8000 " +
            "--dart-define=RESTAURANT_SERVICE_URL=http://localhost:8001 " +
            "--dart-define=DINING_SERVICE_URL=http://localhost:8003 " +
            "--dart-define=MENU_SERVICE_URL=http://localhost:8002 " +
            "--dart-define=ORDER_SERVICE_URL=http://localhost:8005")

    Start-AppWindow -Title "customer-mobile (5002)" `
        -WorkDir (Join-Path $RepoRoot "apps/customer-mobile") `
        -Command ("flutter run -d web-server --web-port=5002 --web-hostname=0.0.0.0 " +
            "--dart-define=RESTAURANT_SERVICE_URL=http://localhost:8001 " +
            "--dart-define=MENU_SERVICE_URL=http://localhost:8002")
}

Write-Host ""
Write-Host "=============================================================="
Write-Host "==> Apps subindo em janelas separadas. URLs (podem levar alguns"
Write-Host "    segundos/minutos pra compilar, principalmente os Flutter):"
Write-Host "=============================================================="
Write-Host "  Painel do Gestor (admin-web)....... http://localhost:3001"
Write-Host "  Cardapio Digital (customer-web)..... http://localhost:3000"
Write-Host "    (o cardapio exige um QR valido - gere um pelo admin-web: Mesas -> icone da mesa)"
if (-not $WebOnly) {
    Write-Host "  App do Garcom (waiter-mobile)....... http://localhost:5001"
    Write-Host "  App do Cliente (customer-mobile)..... http://localhost:5002"
}
Write-Host ""
Write-Host "Pra parar tudo: feche as janelas abertas ou Ctrl+C em cada uma."
