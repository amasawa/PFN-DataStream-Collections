@echo off
start "RDP Keepalive" /min powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0rdp-keepalive.ps1"
