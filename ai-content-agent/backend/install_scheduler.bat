@echo off
echo ========================================
echo Installing Scheduler Dependencies
echo ========================================
echo.

echo Installing APScheduler...
pip install APScheduler==3.10.4

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo The scheduler will automatically start when you run the backend server.
echo.
echo To start the server:
echo   python main.py
echo.
echo To check scheduler status:
echo   Visit: http://localhost:8002/scheduler/status
echo.
pause
