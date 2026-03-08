@echo off
echo ========================================
echo NUCLEAR OPTION - Complete Cache Clear
echo ========================================
echo.
echo This will:
echo 1. Stop all servers
echo 2. Clear all caches
echo 3. Rebuild frontend
echo 4. Restart servers
echo.
pause

echo.
echo [1/6] Stopping servers...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/6] Clearing frontend cache...
cd frontend
if exist node_modules\.cache rmdir /s /q node_modules\.cache
if exist dist rmdir /s /q dist
if exist .vite rmdir /s /q .vite

echo [3/6] Rebuilding frontend...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo [4/6] Starting backend...
cd ..\backend
start "Backend Server" cmd /k "venv\Scripts\activate && python -m uvicorn main:app --host 127.0.0.1 --port 8002"
timeout /t 3 /nobreak >nul

echo [5/6] Starting frontend...
cd ..\frontend
start "Frontend Server" cmd /k "npm run dev"
timeout /t 3 /nobreak >nul

echo [6/6] Opening test page...
start http://localhost:5173/test.html

echo.
echo ========================================
echo DONE!
echo ========================================
echo.
echo Backend: http://localhost:8002
echo Frontend: http://localhost:5173
echo Test Page: http://localhost:5173/test.html
echo.
echo IMPORTANT:
echo 1. Close ALL browser tabs
echo 2. Close browser completely
echo 3. Reopen browser
echo 4. Go to: http://localhost:5173
echo.
pause
