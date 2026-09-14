@echo off
title Salom CRM - Development Server
cd /d "%~dp0"

echo ========================================================
echo          Salom CRM - Ishga tushirish (Dev)
echo ========================================================
echo.

:: 1. Virtual environment tekshirish
if not exist "venv\Scripts\python.exe" (
    echo [XATOLIK] Python virtual muhiti topilmadi: venv\Scripts\python.exe
    echo Iltimos, venv yarating yoki administratorga murojaat qiling.
    echo.
    pause
    exit /b 1
)

:: 2. Root node_modules tekshirish
if not exist "node_modules" (
    echo [OGOHLANTIRISH] Asosiy node_modules topilmadi. Kutubxonalar o'rnatilmoqda...
    call npm install
)

:: 3. Frontend node_modules tekshirish
if not exist "frontend\node_modules" (
    echo [OGOHLANTIRISH] Frontend node_modules topilmadi. Kutubxonalar o'rnatilmoqda...
    cd frontend && call npm install && cd ..
)

echo [OK] Loyiha tayyor!
echo   - Backend:  http://127.0.0.1:8000
echo   - Frontend: http://localhost:3000
echo.
echo ========================================================
echo   Backend va Frontend serverlari ishga tushirilmoqda...
echo   To'xtatish uchun: Ctrl + C bosing
echo ========================================================
echo.

call npm run dev

pause

