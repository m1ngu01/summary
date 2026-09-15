$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $repoPath '.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $venvPython) {
    & $venvPython (Join-Path $PSScriptRoot 'app.py')
} else {
    python (Join-Path $PSScriptRoot 'app.py')
}
exit $LASTEXITCODE
