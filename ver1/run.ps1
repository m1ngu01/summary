$ErrorActionPreference = 'Stop'
python (Join-Path $PSScriptRoot 'app.py')
exit $LASTEXITCODE
