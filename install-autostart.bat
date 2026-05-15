@echo off
:: Launches the PowerShell installer with the right execution policy.
:: Right-click this file -> "Run as administrator"

PowerShell -ExecutionPolicy Bypass -File "%~dp0install-autostart.ps1"
