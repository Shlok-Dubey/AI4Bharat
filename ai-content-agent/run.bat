@echo off
echo ========================================
echo AI Content Agent - Quick Run
echo ========================================
echo.
echo This script will start both backend and frontend.
echo Make sure you have completed the setup first!
echo.
echo If you haven't run setup yet:
echo   1. Install PostgreSQL
echo   2. Create database: ai_content_agent
echo   3. Run: setup.bat
echo.
pause
echo.

echo Starting Backend...
start "AI Content Agent - Backend" cmd /k "cd backend && venv\Scripts\activate && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo Starting Frontend...
start "AI Content Agent - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo Both servers are starting...
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to stop all servers...
echo ========================================
pause >nul

echo.
echo Stopping servers...
taskkill /FI "WINDOWTITLE eq AI Content Agent - Backend*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq AI Content Agent - Frontend*" /F >nul 2>&1
echo Servers stopped.
