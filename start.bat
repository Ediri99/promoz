@echo off
echo Starting PromoZ Server...
start "PromoZ Server" python "%~dp0server.py"
timeout /t 2 /nobreak >nul
start "" "http://localhost:8080/home.html"
