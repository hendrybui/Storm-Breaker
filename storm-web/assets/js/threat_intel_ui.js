/**
 * Storm-Breaker Threat Intelligence UI
 * Frontend for OSINT, IP analysis, email intel, tech fingerprinting
 */
const ThreatIntelUI = {
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
        $(document).on('click', '#btn-intel-ip', () => this.analyzeIP());
        $(document).on('click', '#btn-intel-email', () => this.analyzeEmail());
        $(document).on('click', '#btn-intel-social', () => this.discoverSocial());
        $(document).on('click', '#btn-intel-tech', () => this.fingerprintTech());
        $(document).on('click', '#btn-intel-full', () => this.fullReport());
        $(document).on('click', '.btn-delete-intel', function() {
            ThreatIntelUI.deleteRecord($(this).data('id'));
        });
    },

    render() {
        const container = $('#threat-intel-dashboard');
        if (!container.length) return;
        container.html(`
            <div class="space-y-5">
                <!-- Analysis Tools -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-globe text-blue-400 mr-2"></i>IP Intelligence</h4>
                        <input type="text" id="intel-ip-input" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white mb-2" placeholder="Enter IP address...">
                        <button id="btn-intel-ip" class="w-full px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-search mr-1"></i>Analyze IP
                        </button>
                    </div>
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-envelope text-green-400 mr-2"></i>Email Intelligence</h4>
                        <input type="text" id="intel-email-input" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white mb-2" placeholder="Enter email address...">
                        <button id="btn-intel-email" class="w-full px-3 py-2 bg-green-600 hover:bg-green-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-search mr-1"></i>Analyze Email
                        </button>
                    </div>
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-users text-purple-400 mr-2"></i>Social Discovery</h4>
                        <input type="text" id="intel-social-input" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white mb-2" placeholder="Enter username...">
                        <button id="btn-intel-social" class="w-full px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-search mr-1"></i>Discover Profiles
                        </button>
                    </div>
                </div>

                <!-- Full Report Builder -->
                <div class="bg-slate-800/60 rounded-lg border border-cyan-700/50 p-4">
                    <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-file-alt text-cyan-400 mr-2"></i>Full Threat Report</h4>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
                        <input type="text" id="intel-report-ip" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="IP (optional)">
                        <input type="text" id="intel-report-email" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="Email (optional)">
                        <input type="text" id="intel-report-user" class="bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white" placeholder="Username (optional)">
                    </div>
                    <button id="btn-intel-full" class="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-shield-alt mr-2"></i>Build Full Report
                    </button>
                </div>

                <!-- Results -->
                <div id="intel-result" class="hidden bg-slate-900 rounded-xl border border-cyan-800 p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 id="intel-result-title" class="text-sm font-bold text-white"><i class="fas fa-chart-bar text-cyan-400 mr-2"></i>Analysis Result</h3>
                        <button onclick="$('#intel-result').hide()" class="text-slate-500 hover:text-white text-xs"><i class="fas fa-times"></i></button>
                    </div>
                    <div id="intel-result-visual" class="mb-3"></div>
                    <pre id="intel-result-raw" class="text-xs text-slate-300 bg-slate-950 rounded-lg p-4 overflow-auto max-h-[350px] font-mono"></pre>
                </div>

                <!-- History -->
                <div>
                    <h3 class="text-sm font-bold text-white mb-3"><i class="fas fa-history text-amber-400 mr-2"></i>Intelligence History</h3>
                    <div id="intel-history-list" class="space-y-2 max-h-[300px] overflow-y-auto"></div>
                </div>
            </div>
        `);
    },

    async analyzeIP() {
        const ip = $('#intel-ip-input').val().trim();
        if (!ip) { Swal.fire('Error', 'Enter an IP address', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/threat-intel/ip', method: 'POST', contentType: 'application/json', data: JSON.stringify({ ip }) });
            this.showResult(res, `IP Intel: ${ip}`, this.renderIPVisual(res));
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Analysis failed', 'error'); }
    },

    async analyzeEmail() {
        const email = $('#intel-email-input').val().trim();
        if (!email) { Swal.fire('Error', 'Enter an email', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/threat-intel/email', method: 'POST', contentType: 'application/json', data: JSON.stringify({ email }) });
            this.showResult(res, `Email Intel: ${email}`, this.renderEmailVisual(res));
            this.loadHistory();
        } catch(e) { Swal.fire('Error', 'Analysis failed', 'error'); }
    },

    async discoverSocial() {
        const username = $('#intel-social-input').val().trim();
        if (!username) { Swal.fire('Error', 'Enter a username', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/threat-intel/social', method: 'POST', contentType: 'application/json', data: JSON.stringify({ username }) });
            this.showResult(res, `Social Discovery: @${username}`, this.renderSocialVisual(res));
        } catch(e) { Swal.fire('Error', 'Discovery failed', 'error'); }
    },

    async fullReport() {
        const ip = $('#intel-report-ip').val().trim();
        const email = $('#intel-report-email').val().trim();
        const username = $('#intel-report-user').val().trim();
        if (!ip && !email && !username) { Swal.fire('Error', 'Provide at least one input', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/threat-intel/report', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ ip, email, username }) });
            this.showResult(res, `Full Report — Threat: ${res.overall_threat_level} (${res.overall_threat_score}%)`, this.renderReportVisual(res));
            this.loadHistory();
            GrowlNotification.notify({ title: 'Threat Report', description: `Threat level: ${res.overall_threat_level}`, type: 'info', position: 'top-right' });
        } catch(e) { Swal.fire('Error', 'Report failed', 'error'); }
    },

    renderIPVisual(res) {
        const badges = [];
        if (res.is_vpn) badges.push('<span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">🔒 VPN</span>');
        if (res.is_proxy) badges.push('<span class="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs">🔄 Proxy</span>');
        if (res.is_tor) badges.push('<span class="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs">🧅 Tor</span>');
        if (res.is_datacenter) badges.push('<span class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">🏢 Datacenter</span>');
        const tlColor = { critical: 'red', high: 'orange', medium: 'yellow', low: 'green', none: 'slate' }[res.threat_level] || 'slate';
        return `<div class="flex flex-wrap gap-2 mb-2">${badges.join('')}</div>
            <div class="text-sm text-white">Threat Score: <span class="text-${tlColor}-400 font-bold">${res.threat_score}/100</span> (${res.threat_level})</div>`;
    },

    renderEmailVisual(res) {
        const badges = [];
        if (res.is_disposable) badges.push('<span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">🗑️ Disposable</span>');
        if (res.is_privacy_provider) badges.push('<span class="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded text-xs">🔒 Privacy</span>');
        if (res.is_corporate) badges.push('<span class="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs">🏢 Corporate</span>');
        return `<div class="flex flex-wrap gap-2 mb-2">${badges.join('')}</div>
            <div class="text-sm text-white">Intel Score: <span class="font-bold text-cyan-400">${res.intelligence_score}/100</span></div>`;
    },

    renderSocialVisual(res) {
        let html = '<div class="grid grid-cols-3 md:grid-cols-4 gap-2">';
        for (const p of (res.profiles || [])) {
            html += `<a href="${p.profile_url}" target="_blank" class="bg-slate-800 rounded-lg p-2 text-center hover:bg-slate-700 transition-colors">
                <div class="text-lg">${p.icon}</div>
                <div class="text-xs text-white">${p.platform}</div>
            </a>`;
        }
        return html + '</div>';
    },

    renderReportVisual(res) {
        const score = res.overall_threat_score || 0;
        const color = score >= 75 ? 'red' : score >= 50 ? 'orange' : score >= 25 ? 'yellow' : 'green';
        return `<div class="flex items-center gap-4">
            <div class="text-center">
                <div class="text-4xl font-bold text-${color}-400">${score}</div>
                <div class="text-xs text-slate-400">Threat Score</div>
            </div>
            <div class="flex-1">
                <div class="w-full bg-slate-800 rounded-full h-3">
                    <div class="bg-${color}-500 h-3 rounded-full transition-all" style="width: ${score}%"></div>
                </div>
                <div class="text-xs text-slate-400 mt-1">${res.overall_threat_level}</div>
            </div>
            <div class="text-xs text-slate-400">${Object.keys(res.sections || {}).length} sections analyzed</div>
        </div>`;
    },

    showResult(data, title, visualHtml) {
        $('#intel-result').removeClass('hidden').show();
        $('#intel-result-title').html(`<i class="fas fa-chart-bar text-cyan-400 mr-2"></i>${title}`);
        $('#intel-result-visual').html(visualHtml || '');
        $('#intel-result-raw').text(JSON.stringify(data, null, 2));
    },

    async loadHistory() {
        try {
            const res = await $.getJSON('/api/threat-intel/history');
            const list = $('#intel-history-list');
            if (!res.records || !res.records.length) { list.html('<p class="text-slate-600 text-sm text-center py-4">No intelligence records</p>'); return; }
            let html = '';
            for (const r of res.records.slice(0, 20)) {
                const typeIcon = { ip: '🌐', email: '📧', full_report: '📋' }[r.intel_type] || '📊';
                const lvlColor = { critical: 'red', high: 'orange', medium: 'yellow', low: 'green' }[r.threat_level] || 'slate';
                html += `<div class="flex items-center justify-between bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
                    <div>
                        <span class="text-sm">${typeIcon} <span class="font-bold text-white">${r.target ? r.target.substring(0, 40) : 'N/A'}</span></span>
                        <span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-${lvlColor}-500/20 text-${lvlColor}-400">${r.threat_level} (${r.threat_score})</span>
                        <div class="text-xs text-slate-500 mt-1">${r.intel_type} • ${new Date(r.created_at).toLocaleString()}</div>
                    </div>
                    <button class="btn-delete-intel text-red-400 hover:text-red-300 text-xs" data-id="${r.id}"><i class="fas fa-trash"></i></button>
                </div>`;
            }
            list.html(html);
        } catch(e) { console.error(e); }
    },

    async deleteRecord(id) {
        await $.ajax({ url: `/api/threat-intel/${id}`, method: 'DELETE' });
        this.loadHistory();
    }
};
