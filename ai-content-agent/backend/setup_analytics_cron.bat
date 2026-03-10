@echo off
REM Setup Windows Task Scheduler for Analytics Job
REM Runs analytics_job.py every 12 hours

echo Setting up analytics fetch job...

REM Create task to run every 12 hours
schtasks /create /tn "AI_Content_Analytics_Fetch" /tr "python %~dp0analytics_job.py" /sc daily /mo 1 /st 08:00 /f
schtasks /create /tn "AI_Content_Analytics_Fetch_Evening" /tr "python %~dp0analytics_job.py" /sc daily /mo 1 /st 20:00 /f

echo.
echo ✅ Analytics fetch job scheduled!
echo.
echo Jobs will run at:
echo   - 8:00 AM daily
echo   - 8:00 PM daily
echo.
echo To view scheduled tasks:
echo   schtasks /query /tn "AI_Content_Analytics_Fetch"
echo.
echo To delete scheduled tasks:
echo   schtasks /delete /tn "AI_Content_Analytics_Fetch" /f
echo   schtasks /delete /tn "AI_Content_Analytics_Fetch_Evening" /f
echo.
pause
