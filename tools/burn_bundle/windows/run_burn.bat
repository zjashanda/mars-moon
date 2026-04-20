@echo off
chcp 65001 >nul
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0burn.ps1" %*
set ERR=%ERRORLEVEL%
if "%~1"=="" pause
exit /b %ERR%
