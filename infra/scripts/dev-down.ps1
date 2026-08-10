# Derruba a stack de desenvolvimento.
# Uso: `powershell -File infra/scripts/dev-down.ps1` (adicione `-v` para
# tambem apagar os volumes de dados: `powershell -File infra/scripts/dev-down.ps1 -v`)
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

docker compose --env-file .env.dev -f infra/docker/docker-compose.dev.yml down @args
