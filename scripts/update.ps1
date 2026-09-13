$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    if (!(Test-Path '.env')) { throw 'Run scripts/install.ps1 first.' }
    $python = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } else { 'python' }
    New-Item -ItemType Directory -Force 'data/deployment' | Out-Null
    & $python scripts/deployment_manager.py stop
    if ($LASTEXITCODE -ne 0) { throw 'Unable to stop deployment manager.' }
    $config = Get-Content '.env' -Raw
    if ($config -match 'docker-compose.images.yml') { docker compose pull } else { docker compose build --pull }
    if ($LASTEXITCODE -ne 0) { throw 'Image preparation failed.' }
    docker compose up -d --no-build
    if ($LASTEXITCODE -ne 0) { throw 'Update failed. Existing volumes were retained.' }
    docker compose ps
    & $python scripts/deployment_manager.py start
    if ($LASTEXITCODE -ne 0) { throw 'Deployment manager did not restart.' }
} finally { Pop-Location }
