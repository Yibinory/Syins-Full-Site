$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'install.py'
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 $installer @args
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python $installer @args
} else {
    throw 'Install Python 3.9+ and Docker Desktop (Linux containers), then rerun.'
}
exit $LASTEXITCODE
