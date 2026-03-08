@echo off
echo ========================================
echo AI Content Agent - Windows Setup
echo ========================================
echo.

REM Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Check Node.js
echo [2/6] Checking Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
node --version
echo.

REM Check PostgreSQL
echo [3/6] Checking PostgreSQL installation...
psql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: PostgreSQL is not installed or not in PATH
    echo.
    echo Please install PostgreSQL:
    echo 1. Download from: https://www.postgresql.org/download/windows/
    echo 2. Run the installer
    echo 3. Remember your postgres password
    echo 4. After installation, create database:
    echo    psql -U postgres
    echo    CREATE DATABASE ai_content_agent;
    echo.
    echo After installing PostgreSQL, run this script again.
    pause
    exit /b 1
)
psql --version
echo.

REM Setup Backend
echo [4/6] Setting up backend...
cd backend

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

echo Initializing database...
python init_db.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Database initialization failed!
    echo Please check:
    echo 1. PostgreSQL is running
    echo 2. Database 'ai_content_agent' exists
    echo 3. Connection details in .env file are correct
    echo.
    pause
    exit /b 1
)

cd ..
echo Backend setup complete!
echo.

REM Setup Frontend
echo [5/6] Setting up frontend...
cd frontend

if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo ERROR: npm install failed!
        pause
        exit /b 1
    )
)

cd ..
echo Frontend setup complete!
echo.

REM Final Instructions
echo [6/6] Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo Terminal 1 - Backend:
echo   cd backend
echo   venv\Scripts\activate
echo   start.bat
echo.
echo Terminal 2 - Frontend:
echo   cd frontend
echo   start.bat
echo.
echo Then open: http://localhost:5173
echo.
echo ========================================
pause
