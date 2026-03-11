/**
 * Storm-Breaker Zero-Day Exploit Lab UI
 * Vulnerability scanning, shellcode generation, ROP chain builder,
 * smart fuzzing, and CVE intelligence dashboard
 */
const ZeroDayUI = {
    initialized: false,

    init() {
        if (!this.initialized) {
            this.bindEvents();
        }
        this.initialized = true;
        this.render();
    },

    bindEvents() {
        $(document).on('click', '#btn-zd-scan', () => this.scanTarget());
        $(document).on('click', '#btn-zd-shellcode', () => this.generateShellcode());
        $(document).on('click', '#btn-zd-rop', () => this.buildRopChain());
        $(document).on('click', '#btn-zd-fuzz', () => this.runFuzzer());
        $(document).on('click', '#btn-zd-cve-search', () => this.searchCVEs());
        $(document).on('click', '.zd-sub-tab', function() {
            const t = $(this).data('target');
            $('.zd-sub-tab').removeClass('bg-red-600 text-white').addClass('bg-slate-700 text-slate-300');
            $(this).removeClass('bg-slate-700 text-slate-300').addClass('bg-red-600 text-white');
            $('.zd-sub-panel').addClass('hidden');
            $(`#${t}`).removeClass('hidden');
        });
        $(document).on('click', '.zd-copy-btn', function() {
            const text = $(this).data('text') || $(this).closest('.zd-code-block').find('code').text();
            navigator.clipboard.writeText(text).then(() => {
                const o = $(this).html(); $(this).html('<i class="fas fa-check"></i>'); setTimeout(() => $(this).html(o), 1500);
            });
        });
    },

    render() {
        const c = $('#zeroday-dashboard');
        if (!c.length) return;
        c.html(`
            <div class="space-y-4">
                <div class="flex flex-wrap gap-1.5 p-1.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
                    <button class="zd-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-red-600 text-white" data-target="zd-panel-scan"><i class="fas fa-crosshairs mr-1"></i>Vuln Scanner</button>
                    <button class="zd-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="zd-panel-shellcode"><i class="fas fa-microchip mr-1"></i>Shellcode Gen</button>
                    <button class="zd-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="zd-panel-rop"><i class="fas fa-link mr-1"></i>ROP Builder</button>
                    <button class="zd-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="zd-panel-fuzz"><i class="fas fa-bug mr-1"></i>Smart Fuzzer</button>
                    <button class="zd-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="zd-panel-cve"><i class="fas fa-database mr-1"></i>CVE Intel</button>
                </div>

                <!-- Vuln Scanner -->
                <div id="zd-panel-scan" class="zd-sub-panel">
                    <div class="bg-slate-800/80 rounded-xl border border-red-500/30 p-4">
                        <h3 class="text-red-400 font-bold mb-3"><i class="fas fa-crosshairs mr-2"></i>Vulnerability Scanner</h3>
                        <p class="text-slate-400 text-xs mb-3">Full-spectrum vulnerability scan — port enumeration, CVE matching, OS fingerprinting, and risk assessment.</p>
                        <div class="flex gap-2">
                            <input id="zd-scan-target" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Target IP or hostname">
                            <select id="zd-scan-type" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="full">Full Scan (65535 ports)</option>
                                <option value="quick">Quick Scan (Top 1000)</option>
                            </select>
                            <button id="btn-zd-scan" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-radar mr-1"></i>Scan</button>
                        </div>
                        <div id="zd-scan-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Shellcode Generator -->
                <div id="zd-panel-shellcode" class="zd-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-red-500/30 p-4">
                        <h3 class="text-red-400 font-bold mb-3"><i class="fas fa-microchip mr-2"></i>Shellcode Generator</h3>
                        <p class="text-slate-400 text-xs mb-3">Generate platform-specific shellcode with multiple output formats — C, Python, raw hex, base64.</p>
                        <div class="grid grid-cols-3 gap-2 mb-3">
                            <select id="zd-sc-type" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="reverse_tcp_x64">Reverse TCP (x64 Linux)</option>
                                <option value="reverse_tcp_x86">Reverse TCP (x86 Linux)</option>
                                <option value="bind_tcp_x64">Bind TCP (x64 Linux)</option>
                                <option value="reverse_https_win">Reverse HTTPS (Windows)</option>
                                <option value="exec_command">Execute Command</option>
                                <option value="meterpreter_staged">Meterpreter Staged</option>
                                <option value="fileless_powershell">Fileless PowerShell</option>
                                <option value="macos_reverse">macOS Reverse Shell</option>
                            </select>
                            <input id="zd-sc-lhost" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="LHOST" value="0.0.0.0">
                            <input id="zd-sc-lport" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="LPORT" value="4444">
                        </div>
                        <button id="btn-zd-shellcode" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-cog mr-1"></i>Generate</button>
                        <div id="zd-shellcode-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- ROP Builder -->
                <div id="zd-panel-rop" class="zd-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-red-500/30 p-4">
                        <h3 class="text-red-400 font-bold mb-3"><i class="fas fa-link mr-2"></i>ROP Chain Builder</h3>
                        <p class="text-slate-400 text-xs mb-3">Automatically find ROP gadgets, build chains, and generate exploit code for binary exploitation.</p>
                        <div class="flex gap-2 mb-3">
                            <input id="zd-rop-binary" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Target binary" value="libc.so.6">
                            <input id="zd-rop-func" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Target function" value="system">
                        </div>
                        <button id="btn-zd-rop" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-wrench mr-1"></i>Build Chain</button>
                        <div id="zd-rop-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Smart Fuzzer -->
                <div id="zd-panel-fuzz" class="zd-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-red-500/30 p-4">
                        <h3 class="text-red-400 font-bold mb-3"><i class="fas fa-bug mr-2"></i>Smart Fuzzer Engine</h3>
                        <p class="text-slate-400 text-xs mb-3">Multi-vector fuzzing — buffer overflow, format string, SQLi, command injection, SSTI, XXE, and more.</p>
                        <div class="flex gap-2 mb-3">
                            <input id="zd-fuzz-target" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Target URL (e.g. http://target/api)">
                            <select id="zd-fuzz-type" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="smart">Smart (All Vectors)</option>
                                <option value="fast">Fast (Top Vectors)</option>
                            </select>
                        </div>
                        <button id="btn-zd-fuzz" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-play mr-1"></i>Start Fuzzing</button>
                        <div id="zd-fuzz-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- CVE Intelligence -->
                <div id="zd-panel-cve" class="zd-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-red-500/30 p-4">
                        <h3 class="text-red-400 font-bold mb-3"><i class="fas fa-database mr-2"></i>CVE Intelligence Database</h3>
                        <p class="text-slate-400 text-xs mb-3">Search and explore CVE database with severity and platform filters.</p>
                        <div class="flex gap-2 mb-3">
                            <input id="zd-cve-query" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Search CVEs (e.g. RCE, Windows, SSH)">
                            <select id="zd-cve-severity" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="all">All Severities</option>
                                <option value="critical">Critical</option>
                                <option value="high">High</option>
                            </select>
                        </div>
                        <button id="btn-zd-cve-search" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-search mr-1"></i>Search</button>
                        <div id="zd-cve-result" class="mt-3"></div>
                    </div>
                </div>
            </div>
        `);
    },

    scanTarget() {
        const target = $('#zd-scan-target').val();
        if (!target) return GrowlNotification.notify({title:'Error',description:'Enter a target',type:'error',position:'top-right',closeTimeout:3000});
        const scanType = $('#zd-scan-type').val();
        $('#zd-scan-result').html('<div class="text-red-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Scanning target...</div>');
        $.post('/api/zeroday/scan', {target, scan_type: scanType}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-4 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Open Ports</div><div class="text-xl font-bold text-cyan-400">${r.summary?.open_ports || 0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Critical CVEs</div><div class="text-xl font-bold text-red-400">${r.summary?.critical_vulns || 0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Exploitable</div><div class="text-xl font-bold text-orange-400">${r.summary?.exploitable || 0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Risk Score</div><div class="text-xl font-bold text-yellow-400">${r.risk_score || 0}</div></div>
                </div>
                <div class="bg-slate-700/50 rounded-lg p-3"><span class="text-xs text-slate-400">OS Fingerprint:</span> <span class="text-cyan-400 font-bold text-sm">${r.os_fingerprint || 'Unknown'}</span></div>`;
            if (r.open_ports?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">Open Ports</h4><div class="grid grid-cols-4 gap-1 text-xs">`;
                r.open_ports.forEach(p => { html += `<div class="bg-slate-800 rounded p-1.5"><span class="text-green-400">${p.port}</span>/<span class="text-slate-400">${p.service}</span> <span class="text-slate-500">${p.version || ''}</span></div>`; });
                html += `</div></div>`;
            }
            if (r.vulnerabilities?.length) {
                html += `<div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Vulnerabilities Found</h4><div class="space-y-1">`;
                r.vulnerabilities.forEach(v => {
                    html += `<div class="flex justify-between items-center text-xs bg-slate-800/50 rounded p-2"><span class="text-red-300 font-mono">${v.id}</span><span class="text-white">${v.name}</span><span class="text-yellow-400">CVSS ${v.cvss}</span><span class="${v.exploitable?'text-red-400':'text-slate-400'}">${v.exploitable?'EXPLOITABLE':'N/A'}</span></div>`;
                });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#zd-scan-result').html(html);
        }).fail(() => $('#zd-scan-result').html('<div class="text-red-400">Scan failed</div>'));
    },

    generateShellcode() {
        const type = $('#zd-sc-type').val();
        const lhost = $('#zd-sc-lhost').val() || '0.0.0.0';
        const lport = $('#zd-sc-lport').val() || '4444';
        $('#zd-shellcode-result').html('<div class="text-red-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Generating shellcode...</div>');
        $.post('/api/zeroday/shellcode', {type, lhost, lport}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-4 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Size</div><div class="text-sm font-bold text-cyan-400">${r.size} bytes</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Arch</div><div class="text-sm font-bold text-green-400">${r.arch}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Null Bytes</div><div class="text-sm font-bold ${r.null_bytes?'text-red-400':'text-green-400'}">${r.null_bytes}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Platform</div><div class="text-sm font-bold text-yellow-400">${r.platform}</div></div>
                </div>
                <div class="bg-slate-700/50 rounded-lg p-3"><div class="flex justify-between items-center mb-1"><span class="text-xs text-slate-400">MD5: ${r.md5}</span><span class="text-xs text-slate-400">SHA256: ${r.sha256?.substring(0,32)}...</span></div></div>`;
            if (r.formats) {
                if (r.formats.c_code) {
                    html += `<div class="bg-slate-900 rounded-lg p-3 zd-code-block"><div class="flex justify-between mb-1"><span class="text-xs text-green-400 font-bold">C Code</span><button class="zd-copy-btn text-xs text-slate-400 hover:text-white"><i class="fas fa-copy"></i></button></div><pre class="text-xs text-green-300 overflow-x-auto"><code>${this.escapeHtml(r.formats.c_code)}</code></pre></div>`;
                }
                if (r.formats.python) {
                    html += `<div class="bg-slate-900 rounded-lg p-3 zd-code-block"><div class="flex justify-between mb-1"><span class="text-xs text-blue-400 font-bold">Python</span><button class="zd-copy-btn text-xs text-slate-400 hover:text-white"><i class="fas fa-copy"></i></button></div><pre class="text-xs text-blue-300 overflow-x-auto"><code>${this.escapeHtml(r.formats.python)}</code></pre></div>`;
                }
                if (r.formats.base64) {
                    html += `<div class="bg-slate-900 rounded-lg p-3 zd-code-block"><div class="flex justify-between mb-1"><span class="text-xs text-yellow-400 font-bold">Base64</span><button class="zd-copy-btn text-xs text-slate-400 hover:text-white"><i class="fas fa-copy"></i></button></div><pre class="text-xs text-yellow-300 break-all"><code>${r.formats.base64}</code></pre></div>`;
                }
            }
            html += `</div>`;
            $('#zd-shellcode-result').html(html);
        });
    },

    buildRopChain() {
        const binary = $('#zd-rop-binary').val() || 'libc.so.6';
        const func = $('#zd-rop-func').val() || 'system';
        $('#zd-rop-result').html('<div class="text-red-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Finding gadgets...</div>');
        $.post('/api/zeroday/rop', {binary, target_function: func}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-3 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Base Address</div><div class="text-sm font-bold text-cyan-400 font-mono">${r.base_address}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Gadgets Found</div><div class="text-sm font-bold text-green-400">${r.gadgets_found}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Chain Length</div><div class="text-sm font-bold text-yellow-400">${r.chain_length}</div></div>
                </div>`;
            if (r.gadgets?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">Gadgets</h4><div class="space-y-1">`;
                r.gadgets.forEach(g => {
                    const qColor = g.quality === 'excellent' ? 'green' : g.quality === 'good' ? 'yellow' : 'orange';
                    html += `<div class="flex justify-between text-xs bg-slate-800 rounded p-1.5"><span class="text-green-300 font-mono">${g.address}</span><span class="text-white">${g.instruction}</span><span class="text-${qColor}-400">${g.quality}</span></div>`;
                });
                html += `</div></div>`;
            }
            if (r.chain?.length) {
                html += `<div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">ROP Chain</h4><div class="space-y-1">`;
                r.chain.forEach(s => { html += `<div class="flex items-center gap-2 text-xs"><span class="w-5 h-5 rounded-full bg-red-600 text-white flex items-center justify-center text-[10px]">${s.step}</span><span class="text-yellow-300 font-mono">${s.gadget}</span><span class="text-slate-400">${s.purpose}</span></div>`; });
                html += `</div></div>`;
            }
            if (r.exploit_code) {
                html += `<div class="bg-slate-900 rounded-lg p-3 zd-code-block"><div class="flex justify-between mb-1"><span class="text-xs text-green-400 font-bold">Exploit Code (Python)</span><button class="zd-copy-btn text-xs text-slate-400 hover:text-white"><i class="fas fa-copy"></i></button></div><pre class="text-xs text-green-300 overflow-x-auto"><code>${this.escapeHtml(r.exploit_code)}</code></pre></div>`;
            }
            if (r.notes?.length) {
                html += `<div class="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-1">Notes</h4><ul class="list-disc list-inside text-xs text-slate-300 space-y-0.5">`;
                r.notes.forEach(n => { html += `<li>${n}</li>`; });
                html += `</ul></div>`;
            }
            html += `</div>`;
            $('#zd-rop-result').html(html);
        });
    },

    runFuzzer() {
        const target = $('#zd-fuzz-target').val();
        if (!target) return GrowlNotification.notify({title:'Error',description:'Enter target URL',type:'error',position:'top-right',closeTimeout:3000});
        const fuzzType = $('#zd-fuzz-type').val();
        $('#zd-fuzz-result').html('<div class="text-red-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Fuzzing in progress...</div>');
        $.post('/api/zeroday/fuzz', {target, fuzz_type: fuzzType}, (d) => {
            if (!d.success) return;
            const r = d.result;
            const riskColor = {critical:'red',high:'orange',medium:'yellow',low:'green'}[r.risk_assessment] || 'slate';
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-4 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Tests</div><div class="text-xl font-bold text-cyan-400">${r.total_tests}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Crashes</div><div class="text-xl font-bold text-red-400">${r.crashes}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Anomalies</div><div class="text-xl font-bold text-yellow-400">${r.anomalies}</div></div>
                    <div class="bg-${riskColor}-900/20 border border-${riskColor}-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Risk</div><div class="text-xl font-bold text-${riskColor}-400">${(r.risk_assessment||'').toUpperCase()}</div></div>
                </div>`;
            if (r.findings?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Findings (${r.findings.length})</h4><div class="space-y-1 max-h-64 overflow-y-auto">`;
                r.findings.forEach(f => {
                    const c = f.severity === 'critical' ? 'red' : f.severity === 'high' ? 'orange' : 'yellow';
                    html += `<div class="bg-${c}-900/10 border border-${c}-500/20 rounded p-2 text-xs"><div class="flex justify-between"><span class="text-${c}-400 font-bold">${f.category}</span><span class="text-slate-400">${f.status} (HTTP ${f.response_code})</span></div><div class="text-slate-300 font-mono mt-1 truncate">${this.escapeHtml(f.vector)}</div></div>`;
                });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#zd-fuzz-result').html(html);
        });
    },

    searchCVEs() {
        const query = $('#zd-cve-query').val();
        const severity = $('#zd-cve-severity').val();
        $('#zd-cve-result').html('<div class="text-red-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Searching...</div>');
        $.get('/api/zeroday/cves', {query, severity}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3"><div class="text-xs text-slate-400 mb-2">Found ${r.total_results} results</div>`;
            if (r.results?.length) {
                html += `<div class="space-y-1">`;
                r.results.forEach(v => {
                    html += `<div class="bg-slate-700/50 rounded-lg p-3 flex justify-between items-center"><div><span class="text-red-400 font-mono font-bold text-sm">${v.id}</span><span class="text-white ml-2">${v.name}</span></div><div class="flex gap-2 items-center"><span class="text-xs text-slate-400">${v.platform}</span><span class="px-2 py-0.5 rounded bg-red-500/20 text-red-400 text-xs font-bold">CVSS ${v.cvss}</span>${v.public_exploit?'<span class="px-2 py-0.5 rounded bg-orange-500/20 text-orange-400 text-xs">Exploit Available</span>':''}</div></div>`;
                });
                html += `</div>`;
            } else {
                html += `<div class="text-slate-500 text-center py-4">No CVEs found</div>`;
            }
            html += `</div>`;
            $('#zd-cve-result').html(html);
        });
    },

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
};
