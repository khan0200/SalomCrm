@echo off
title Salom CRM - Multi Window Launcher
cd /d "%~dp0"

echo ========================================================
echo   Salom CRM (Alohida oynalarda ochish)
echo ========================================================
echo.

start "Salom CRM - Backend (Django)" cmd /k "cd /d \"%~dp0\" && venv\Scripts\python backend/manage.py runserver 127.0.0.1:8000"
start "Salom CRM - Frontend (Vite)" cmd /k "cd /d \"%~dp0frontend\" && npm run dev"

echo [OK] Backend va Frontend alohida oynalarda ishga tushirildi!
timeout /t 3 >nul
exit
