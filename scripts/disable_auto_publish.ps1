$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $repoPath '.auto-publish'
New-Item -ItemType Directory -Path $statePath -Force | Out-Null
New-Item -ItemType File -Path (Join-Path $statePath 'stop') -Force | Out-Null
$shortcutPath = Join-Path ([Environment]::GetFolderPath('Startup')) 'Summary Auto Publish.lnk'
if (Test-Path -LiteralPath $shortcutPath) {
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($shortcutPath)
    $watcherPath = Join-Path $PSScriptRoot 'auto_publish.py'
    if ($shortcut.Arguments -eq ('"' + $watcherPath + '"')) {
        Remove-Item -LiteralPath $shortcutPath
    }
}
Write-Output 'Legacy watcher stop requested and matching startup shortcut removed.'
