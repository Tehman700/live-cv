# Run this script once to register the CV watcher to start at Windows login.
# Right-click -> "Run with PowerShell"

$ErrorActionPreference = "Stop"

$dir    = Split-Path -Parent $MyInvocation.MyCommand.Definition
$script = Join-Path $dir "watch.py"

# Find pythonw.exe
$pythonCmd = Get-Command "pythonw.exe" -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $exe = $pythonCmd.Source
} else {
    $pythonPath = (Get-Command "python.exe").Source
    $exe = Join-Path (Split-Path $pythonPath) "pythonw.exe"
}

if (-not (Test-Path $exe)) {
    Write-Host "ERROR: pythonw.exe not found."
    Read-Host "Press Enter to exit"
    exit 1
}

# Remove old Task Scheduler entry if present (ignore errors if no permission)
try { schtasks /delete /tn "CV Auto-Deploy Watcher" /f 2>$null } catch {}

# Write a VBS launcher to the Startup folder (no console flash, runs at login)
$startupFolder = [Environment]::GetFolderPath("Startup")
$vbsPath = Join-Path $startupFolder "CV-Watcher.vbs"

$line1 = 'Set WshShell = CreateObject("WScript.Shell")'
$line2 = 'WshShell.Run Chr(34) & "' + $exe + '" & Chr(34) & " " & Chr(34) & "' + $script + '" & Chr(34), 0, False'
$vbsContent = $line1 + "`r`n" + $line2

Set-Content -Path $vbsPath -Value $vbsContent -Encoding ASCII

Write-Host ""
Write-Host "Startup entry created: $vbsPath"
Write-Host ""

# Stop any old watcher, start the fixed one right now
Get-Process pythonw -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 600
Start-Process -FilePath $exe -ArgumentList ('"' + $script + '"') -WindowStyle Hidden

Write-Host "Watcher is running now."
Write-Host "Save Tehman CV.docx and a terminal window should pop up."
Write-Host ""
Read-Host "Press Enter to close"
