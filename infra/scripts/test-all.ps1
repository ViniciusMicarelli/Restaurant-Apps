# Roda a suite Pytest de cada package/servico Python de forma independente,
# agregando o resultado final. Uso: `powershell -File infra/scripts/test-all.ps1`
# a partir de qualquer diretorio.
$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $RepoRoot

$Passed = @()
$Failed = @()

$Dirs = @(Get-ChildItem -Path "packages", "services" -Directory) + @(Get-Item "workers")
foreach ($dir in $Dirs) {
    $pyproject = Join-Path $dir.FullName "pyproject.toml"
    if (-not (Test-Path $pyproject)) { continue }

    Write-Host "=============================================================="
    Write-Host "==> Testando: $($dir.Name)"
    Write-Host "=============================================================="

    Push-Location $dir.FullName
    try {
        uv run pytest -q
        if ($LASTEXITCODE -eq 0) { $Passed += $dir.Name } else { $Failed += $dir.Name }
    } catch {
        $Failed += $dir.Name
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "=============================================================="
Write-Host "Resumo"
Write-Host "=============================================================="
Write-Host "Passou ($($Passed.Count)): $($Passed -join ', ')"
Write-Host "Falhou ($($Failed.Count)): $($Failed -join ', ')"

if ($Failed.Count -gt 0) { exit 1 }
