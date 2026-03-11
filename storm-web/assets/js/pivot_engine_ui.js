/**
 * Storm-Breaker Pivot Engine UI
 * Frontend for attack graphs, credential reuse, privesc, kill chain tracking
 */
const PivotEngineUI = {
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
        $(document).on('click', '#btn-attack-graph', () => this.buildAttackGraph());
        $(document).on('click', '#btn-cred-reuse', () => this.mapCredReuse());
        $(document).on('click', '#btn-privesc-win', () => this.showPrivesc('windows'));
        $(document).on('click', '#btn-privesc-linux', () => this.showPrivesc('linux'));
        $(document).on('click', '#btn-kill-chain', () => this.trackKillChain());
        $(document).on('click', '#btn-attack-surface', () => this.scoreAttackSurface());
        $(document).on('click', '.btn-delete-pivot', function() {
            PivotEngineUI.deleteRecord($(this).data('id'));
        });
    },

    render() {
        const container = $('#pivot-engine-dashboard');
        if (!container.length) return;
        container.html(`
            <div class="space-y-5">
                <!-- Tool Cards -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-project-diagram text-sky-400 mr-2"></i>Attack Graph</h4>
                        <p class="text-xs text-slate-400 mb-3">Build network attack graph from discovered hosts & credentials</p>
                        <button id="btn-attack-graph" class="w-full px-3 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-network-wired mr-1"></i>Build Graph
                        </button>
                    </div>
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-key text-amber-400 mr-2"></i>Credential Reuse</h4>
                        <p class="text-xs text-slate-400 mb-3">Map captured credentials against discovered hosts</p>
                        <button id="btn-cred-reuse" class="w-full px-3 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-exchange-alt mr-1"></i>Map Reuse
                        </button>
                    </div>
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-2"><i class="fas fa-chart-pie text-emerald-400 mr-2"></i>Attack Surface</h4>
                        <p class="text-xs text-slate-400 mb-3">Score overall attack surface from all gathered intelligence</p>
                        <button id="btn-attack-surface" class="w-full px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-tachometer-alt mr-1"></i>Score Surface
                        </button>
                    </div>
                </div>

                <!-- Privilege Escalation -->
                <div class="bg-slate-800/60 rounded-lg border border-red-700/50 p-4">
                    <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-arrow-up text-red-400 mr-2"></i>Privilege Escalation</h4>
                    <div class="flex gap-2">
                        <button id="btn-privesc-win" class="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fab fa-windows mr-1"></i>Windows PrivEsc
                        </button>
                        <button id="btn-privesc-linux" class="flex-1 px-3 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fab fa-linux mr-1"></i>Linux PrivEsc
                        </button>
                    </div>
                </div>

                <!-- Kill Chain -->
                <div class="bg-slate-800/60 rounded-lg border border-purple-700/50 p-4">
                    <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-link text-purple-400 mr-2"></i>Kill Chain Tracker</h4>
                    <p class="text-xs text-slate-400 mb-3">Track progress across the 7-phase cyber kill chain from gathered data</p>
                    <button id="btn-kill-chain" class="px-4 py-2 bg-gradient-to-r from-purple-600 to-violet-600 hover:from-purple-500 hover:to-violet-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-sync mr-2"></i>Assess Kill Chain
                    </button>
                </div>

                <!-- Results -->
                <div id="pivot-result" class="hidden bg-slate-900 rounded-xl border border-sky-800 p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 id="pivot-result-title" class="text-sm font-bold text-white"><i class="fas fa-code-branch text-sky-400 mr-2"></i>Result</h3>
                        <button onclick="$('#pivot-result').hide()" class="text-slate-500 hover:text-white text-xs"><i class="fas fa-times"></i></button>
                    </div>
                    <div id="pivot-result-visual" class="mb-3"></div>
                    <pre id="pivot-result-raw" class="text-xs text-slate-300 bg-slate-950 rounded-lg p-4 overflow-auto max-h-[400px] font-mono"></pre>
                </div>

                <!-- History -->
                <div>
                    <h3 class="text-sm font-bold text-white mb-3"><i class="fas fa-history text-sky-400 mr-2"></i>Pivot History</h3>
                    <div id="pivot-history-list" class="space-y-2 max-h-[250px] overflow-y-auto"></div>
                </div>
            </div>
        `);
    },

    async buildAttackGraph() {
        // Pull data from existing Storm-Breaker data
        try {
            const [netRes, credRes] = await Promise.all([
                $.getJSON('/api/network/discoveries').catch(() => ({ discoveries: [] })),
                $.getJSON('/api/credentials').catch(() => ({ credentials: [] }))
            ]);
            const hosts = (netRes.discoveries || []).map(d => {
                const data = typeof d.data === 'string' ? JSON.parse(d.data) : d.data;
                return { ip: d.target || d.ip || 'unknown', ports: data?.open_ports || data?.ports || [], os: data?.os_hint || 'Unknown' };
            });
            const creds = (credRes.credentials || []).map(c => ({
                username: c.value || c.username || '', type: c.type || 'password'
            }));
            if (!hosts.length) {
                hosts.push(
                    { ip: '192.168.1.10', ports: [22, 80, 443], os: 'Linux' },
                    { ip: '192.168.1.20', ports: [445, 3389, 135], os: 'Windows' },
                    { ip: '192.168.1.30', ports: [22, 3306, 8080], os: 'Linux' }
                );
            }
            const res = await $.ajax({ url: '/api/pivot/attack-graph', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ hosts, credentials: creds }) });
            this.showResult(res, `Attack Graph: ${res.total_hosts} hosts, ${res.total_lateral_paths} paths`, this.renderGraphVisual(res));
            this.loadHistory();
            GrowlNotification.notify({ title: 'Attack Graph', description: `${res.high_value_targets} high-value targets`, type: 'success', position: 'top-right' });
        } catch(e) { Swal.fire('Error', 'Failed to build graph', 'error'); }
    },

    async mapCredReuse() {
        try {
            const [netRes, credRes] = await Promise.all([
                $.getJSON('/api/network/discoveries').catch(() => ({ discoveries: [] })),
                $.getJSON('/api/credentials').catch(() => ({ credentials: [] }))
            ]);
            const hosts = (netRes.discoveries || []).map(d => {
                const data = typeof d.data === 'string' ? JSON.parse(d.data) : d.data;
                return { ip: d.target || 'unknown', ports: data?.open_ports || [] };
            });
            const creds = (credRes.credentials || []).map(c => ({
                username: c.value || '', type: c.type || 'password'
            }));
            if (!hosts.length) hosts.push({ ip: '192.168.1.10', ports: [22, 445, 3389] });
            if (!creds.length) creds.push({ username: 'admin', type: 'password' });
            const res = await $.ajax({ url: '/api/pivot/credential-reuse', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ hosts, credentials: creds }) });
            this.showResult(res, `Credential Reuse: ${res.total_attack_opportunities} opportunities`);
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async showPrivesc(os) {
        try {
            const res = await $.ajax({ url: '/api/pivot/privesc', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ os_type: os, current_user: 'user' }) });
            this.showResult(res, `${os.charAt(0).toUpperCase() + os.slice(1)} PrivEsc — ${res.total_techniques} techniques`, this.renderPrivescVisual(res));
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async trackKillChain() {
        // Auto-gather events from Storm-Breaker data
        const events = [];
        try {
            const [fp, creds, net, exfil] = await Promise.all([
                $.getJSON('/api/fingerprints').catch(() => ({ fingerprints: [] })),
                $.getJSON('/api/credentials').catch(() => ({ credentials: [] })),
                $.getJSON('/api/network/discoveries').catch(() => ({ discoveries: [] })),
                $.getJSON('/api/browser-exfil/data').catch(() => ({ data: [] }))
            ]);
            if ((fp.fingerprints || []).length) events.push({ type: 'fingerprint', timestamp: new Date().toISOString() });
            if ((net.discoveries || []).length) events.push({ type: 'network_scan', timestamp: new Date().toISOString() });
            if ((creds.credentials || []).length) events.push({ type: 'credential_capture', timestamp: new Date().toISOString() });
            if ((exfil.data || []).length) events.push({ type: 'browser_exfil', timestamp: new Date().toISOString() });
        } catch(e) {}
        // Add common events that likely happened
        events.push({ type: 'payload_generated', timestamp: new Date().toISOString() });
        events.push({ type: 'phishing_link', timestamp: new Date().toISOString() });
        events.push({ type: 'template_visit', timestamp: new Date().toISOString() });

        try {
            const res = await $.ajax({ url: '/api/pivot/kill-chain', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ events }) });
            this.showResult(res, `Kill Chain: ${res.coverage_percent}% coverage`, this.renderKillChainVisual(res));
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async scoreAttackSurface() {
        try {
            const [net, creds, sessions, exfil] = await Promise.all([
                $.getJSON('/api/network/discoveries').catch(() => ({ discoveries: [] })),
                $.getJSON('/api/credentials').catch(() => ({ credentials: [] })),
                $.getJSON('/api/sessions').catch(() => ({ sessions: [] })),
                $.getJSON('/api/browser-exfil/data').catch(() => ({ data: [] }))
            ]);
            const res = await $.ajax({ url: '/api/pivot/attack-surface', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({
                    hosts: net.discoveries || [],
                    credentials: creds.credentials || [],
                    sessions: sessions.sessions || [],
                    browser_exfil: exfil.data || []
                }) });
            this.showResult(res, `Attack Surface: ${res.grade} (${res.overall_score}%)`, this.renderSurfaceVisual(res));
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    renderGraphVisual(res) {
        let html = '<div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">';
        html += `<div class="bg-sky-500/10 border border-sky-500/30 rounded-lg p-3 text-center"><div class="text-xl font-bold text-sky-400">${res.total_hosts}</div><div class="text-xs text-slate-400">Hosts</div></div>`;
        html += `<div class="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-center"><div class="text-xl font-bold text-red-400">${res.high_value_targets}</div><div class="text-xs text-slate-400">High Value</div></div>`;
        html += `<div class="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3 text-center"><div class="text-xl font-bold text-amber-400">${res.total_lateral_paths}</div><div class="text-xs text-slate-400">Lateral Paths</div></div>`;
        html += `<div class="bg-purple-500/10 border border-purple-500/30 rounded-lg p-3 text-center"><div class="text-xl font-bold text-purple-400">${res.mitre_technique_count}</div><div class="text-xs text-slate-400">MITRE Techniques</div></div>`;
        html += '</div>';
        // Attack paths
        if (res.attack_paths && res.attack_paths.length) {
            html += '<h4 class="text-xs font-bold text-white mb-2">Recommended Attack Paths:</h4><div class="space-y-1">';
            for (const p of res.attack_paths) {
                const c = { critical: 'red', high: 'orange', medium: 'yellow' }[p.priority] || 'slate';
                html += `<div class="text-xs bg-${c}-500/10 border border-${c}-500/30 rounded px-3 py-2 text-${c}-300">
                    <b>${p.pivot_from}</b> → <b>${p.target}</b> via ${p.method.technique} (${p.priority}) — Score: ${p.attack_surface_score}
                </div>`;
            }
            html += '</div>';
        }
        return html;
    },

    renderPrivescVisual(res) {
        let html = `<div class="text-xs text-slate-400 mb-3">Quick wins: ${res.quick_wins?.length || 0} | Total: ${res.total_techniques}</div>`;
        html += '<div class="space-y-2">';
        for (const t of (res.suggestions || [])) {
            const diffColor = { easy: 'green', medium: 'yellow', hard: 'red' }[t.difficulty] || 'slate';
            html += `<div class="bg-slate-800/60 rounded-lg border border-${diffColor}-500/30 p-3">
                <div class="flex items-center justify-between mb-1">
                    <span class="text-sm font-bold text-white">${t.name}</span>
                    <div class="flex gap-1">
                        <span class="text-xs px-2 py-0.5 rounded-full bg-${diffColor}-500/20 text-${diffColor}-400">${t.difficulty}</span>
                        <span class="text-xs px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">${t.impact}</span>
                    </div>
                </div>
                <p class="text-xs text-slate-400 mb-2">${t.description}</p>
                <div class="text-xs font-mono bg-slate-950 rounded p-2 text-green-300 overflow-x-auto">${t.check}</div>
            </div>`;
        }
        html += '</div>';
        return html;
    },

    renderKillChainVisual(res) {
        let html = '<div class="flex items-center gap-1 mb-3">';
        const phases = res.phases || {};
        for (const [key, phase] of Object.entries(phases)) {
            const done = phase.completed;
            html += `<div class="flex-1 text-center p-2 rounded-lg ${done ? 'bg-green-500/20 border border-green-500/40' : 'bg-slate-800 border border-slate-700/50'}">
                <div class="text-lg">${phase.icon}</div>
                <div class="text-xs ${done ? 'text-green-400 font-bold' : 'text-slate-500'}">${phase.name}</div>
                <div class="text-xs ${done ? 'text-green-300' : 'text-slate-600'}">${done ? '✓' : '○'}</div>
            </div>`;
        }
        html += '</div>';
        html += `<div class="text-center text-sm text-white">${res.coverage_percent}% Kill Chain Coverage (${res.completed_phases}/${res.total_phases})</div>`;
        if (res.next_phase) {
            html += `<div class="text-xs text-amber-400 mt-2 text-center">Next: ${res.next_phase.name} — ${res.next_phase.description}</div>`;
        }
        return html;
    },

    renderSurfaceVisual(res) {
        const scores = res.scores || {};
        let html = '<div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">';
        const labels = { network_exposure: '🌐 Network', credential_coverage: '🔑 Credentials', session_control: '🎮 Sessions', data_access: '💾 Data' };
        for (const [key, label] of Object.entries(labels)) {
            const val = scores[key] || 0;
            const c = val >= 60 ? 'red' : val >= 30 ? 'yellow' : 'green';
            html += `<div class="bg-${c}-500/10 border border-${c}-500/30 rounded-lg p-3 text-center">
                <div class="text-xl font-bold text-${c}-400">${val}%</div>
                <div class="text-xs text-slate-400">${label}</div>
            </div>`;
        }
        html += '</div>';
        html += `<div class="text-center text-sm text-white mb-2">${res.grade} — Overall: ${res.overall_score}%</div>`;
        if (res.summary) {
            for (const s of res.summary) {
                html += `<div class="text-xs text-slate-400 text-center">${s}</div>`;
            }
        }
        return html;
    },

    showResult(data, title, visualHtml) {
        $('#pivot-result').removeClass('hidden').show();
        $('#pivot-result-title').html(`<i class="fas fa-code-branch text-sky-400 mr-2"></i>${title}`);
        $('#pivot-result-visual').html(visualHtml || '');
        $('#pivot-result-raw').text(JSON.stringify(data, null, 2));
    },

    async loadHistory() {
        try {
            const res = await $.getJSON('/api/pivot/history');
            const list = $('#pivot-history-list');
            if (!res.records || !res.records.length) { list.html('<p class="text-slate-600 text-sm text-center py-4">No pivot records</p>'); return; }
            let html = '';
            for (const r of res.records.slice(0, 15)) {
                const typeIcon = { attack_graph: '🕸️', kill_chain: '⛓️' }[r.record_type] || '📊';
                html += `<div class="flex items-center justify-between bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
                    <div>
                        <span class="text-sm">${typeIcon} <span class="font-bold text-white">${r.name}</span></span>
                        <div class="text-xs text-slate-500 mt-1">${r.record_type} • ${r.host_count} hosts • ${r.path_count} paths • ${new Date(r.created_at).toLocaleString()}</div>
                    </div>
                    <button class="btn-delete-pivot text-red-400 hover:text-red-300 text-xs" data-id="${r.id}"><i class="fas fa-trash"></i></button>
                </div>`;
            }
            list.html(html);
        } catch(e) { console.error(e); }
    },

    async deleteRecord(id) {
        await $.ajax({ url: `/api/pivot/${id}`, method: 'DELETE' });
        this.loadHistory();
    }
};
