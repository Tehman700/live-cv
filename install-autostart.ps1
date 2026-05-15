# Run this script once to register the CV watcher as a Windows startup task.
# Right-click -> "Run with PowerShell" (or run from an admin terminal).

$ErrorActionPreference = "Stop"

$dir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$script = Join-Path $dir "watch.py"

# Find pythonw.exe (runs Python with no console window)
$pythonCmd = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $exe = $pythonCmd.Source
} else {
    $pythonPath = (Get-Command "python.exe").Source
    $exe = Join-Path (Split-Path $pythonPath) "pythonw.exe"
}

if (-not (Test-Path $exe)) {
    Write-Host "ERROR: pythonw.exe not found at $exe"
    Write-Host "Make sure Python is installed."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Python : $exe"
Write-Host "Script : $script"
Write-Host ""

$action   = New-ScheduledTaskAction -Execute $exe -Argument "`"$script`""
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit 0 -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName "CV Auto-Deploy Watcher" `
    -Action   $action `
    -Trigger  $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force | Out-Null

Write-Host "Done! The watcher is now registered."
Write-Host "It will start automatically every time you log into Windows."
Write-Host ""
Write-Host "Starting it right now..."
Start-Process -FilePath $exe -ArgumentList "`"$script`"" -WindowStyle Hidden

Write-Host "Watcher is running in the background."
Write-Host "Check 'watcher.log' in the Live CV folder to see its activity."
Write-Host ""
Read-Host "Press Enter to close"
