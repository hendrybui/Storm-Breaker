@echo off
:: Cleanup Script - Remove All Backdoor Components
:: Use this for testing or authorized cleanup

echo ============================================
echo Storm-Breaker Backdoor Removal Tool
echo ============================================
echo.
echo WARNING: This will remove all backdoor components
echo.
pause

echo.
echo [1] Killing PowerShell processes...
taskkill /F /IM powershell.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] PowerShell processes terminated
) else (
    echo     [!] No PowerShell processes found
)

echo.
echo [2] Removing scheduled tasks...
schtasks /delete /tn "ZoomUpdateService" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] Removed: ZoomUpdateService
) else (
    echo     [!] Task not found: ZoomUpdateService
)

schtasks /delete /tn "ZoomUpdateCheck" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] Removed: ZoomUpdateCheck
) else (
    echo     [!] Task not found: ZoomUpdateCheck
)

echo.
echo [3] Removing registry entries...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZoomUpdate" /f >nul 2>&1
if %errorlevel% equ 0 (
    echo     [✓] Removed: Registry startup entry
) else (
    echo     [!] Registry entry not found
)

echo.
echo [4] Deleting files...
if exist "%APPDATA%\Microsoft\Windows\ZoomService.ps1" (
    del "%APPDATA%\Microsoft\Windows\ZoomService.ps1" >nul 2>&1
    echo     [✓] Deleted: ZoomService.ps1
) else (
    echo     [!] File not found: ZoomService.ps1
)

if exist "%APPDATA%\Microsoft\Windows\ZoomUpdate.vbs" (
    del "%APPDATA%\Microsoft\Windows\ZoomUpdate.vbs" >nul 2>&1
    echo     [✓] Deleted: ZoomUpdate.vbs
) else (
    echo     [!] File not found: ZoomUpdate.vbs
)

echo.
echo ============================================
echo Cleanup Complete
echo ============================================
echo.
echo All backdoor components have been removed.
echo.
pause
