$ErrorActionPreference = 'Stop'
$repoPath = Split-Path -Parent $PSScriptRoot
$pythonPath = (Get-Command pythonw.exe -ErrorAction Stop).Source
$watcherPath = Join-Path $PSScriptRoot 'auto_publish.py'
$statePath = Join-Path $repoPath '.auto-publish'
New-Item -ItemType Directory -Path $statePath -Force | Out-Null
$stopPath = Join-Path $statePath 'stop'
if (Test-Path -LiteralPath $stopPath) { Remove-Item -LiteralPath $stopPath }
$startupPath = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupPath 'Summary Auto Publish.lnk'
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonPath
$shortcut.Arguments = '"' + $watcherPath + '"'
$shortcut.WorkingDirectory = $repoPath
$shortcut.WindowStyle = 7
$shortcut.Description = 'Publish reading HTML to GitHub after saving'
$shortcut.Save()
Start-Process -FilePath $pythonPath -ArgumentList ('"' + $watcherPath + '"') -WorkingDirectory $repoPath -WindowStyle Hidden
Write-Output "Auto publish installed and started. Log: $statePath\publish.log"
