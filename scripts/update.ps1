$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    if (!(Test-Path '.env')) { throw 'Run scripts/install.ps1 first.' }
    $config = Get-Content '.env' -Raw
    if ($config -match 'docker-compose.images.yml') { docker compose pull } else { docker compose build --pull }
    if ($LASTEXITCODE -ne 0) { throw 'Image preparation failed.' }
    docker compose up -d --no-build
    if ($LASTEXITCODE -ne 0) { throw 'Update failed. Existing volumes were retained.' }
    docker compose ps
} finally { Pop-Location }
