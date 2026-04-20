@echo off
chcp 65001 >nul
cd /d %~dp0
call "%~dp0run_burn.bat"
set ERR=%ERRORLEVEL%
pause
exit /b %ERR%
