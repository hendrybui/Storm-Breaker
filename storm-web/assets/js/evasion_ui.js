/**
 * Storm-Breaker Evasion Framework UI
 * Frontend for anti-detection, traffic disguise, and fingerprint spoofing
 */
const EvasionUI = {
    profiles: {},
    initialized: false,

    init() {
        if (!this.initialized) {
            this.bindEvents();
        }
        this.initialized = true;
        this.loadProfiles();
    },

    async loadProfiles() {
        try {
            const res = await $.getJSON('/api/evasion/profiles');
            this.profiles = res;
            this.renderDashboard();
            this.loadSavedConfigs();
        } catch(e) {
            console.error('Evasion profiles load error:', e);
            this.profiles = { traffic_profiles: {}, ua_families: {}, encoding_options: [] };
            this.renderDashboard();
        }
    },

    bindEvents() {
        $(document).on('click', '#btn-gen-fingerprint', () => this.generateFingerprint());
        $(document).on('click', '#btn-gen-disguise', () => this.generateDisguise());
        $(document).on('click', '#btn-gen-beacon', () => this.generateBeacon());
        $(document).on('click', '#btn-gen-domains', () => this.generateDomains());
        $(document).on('click', '#btn-gen-decoy', () => this.generateDecoy());
        $(document).on('click', '#btn-build-config', () => this.buildConfig());
        $(document).on('click', '.btn-delete-evasion', function() {
            const id = $(this).data('id');
            EvasionUI.deleteConfig(id);
        });
    },

    renderDashboard() {
        const container = $('#evasion-dashboard');
        if (!container.length) return;

        // Traffic Profiles
        let trafficHtml = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">';
        for (const [key, p] of Object.entries(this.profiles.traffic_profiles || {})) {
            trafficHtml += `
                <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4 hover:border-violet-500/50 transition-all cursor-pointer traffic-profile-card" data-key="${key}">
                    <div class="flex items-center justify-between mb-2">
                        <span class="text-lg">${p.icon} ${p.name}</span>
                        <span class="text-xs px-2 py-0.5 rounded-full ${p.stealth_rating >= 85 ? 'bg-green-500/20 text-green-400' : p.stealth_rating >= 70 ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}">${p.stealth_rating}%</span>
                    </div>
                    <p class="text-xs text-slate-400 mb-2">${p.description}</p>
                    <div class="flex justify-between text-xs text-slate-500">
                        <span>Encoding: ${p.data_encoding}</span>
                        <span>Jitter: ${p.jitter_range[0]}-${p.jitter_range[1]}s</span>
                    </div>
                </div>`;
        }
        trafficHtml += '</div>';

        // Timing Profiles
        let timingHtml = '<div class="grid grid-cols-2 md:grid-cols-5 gap-2 mb-6">';
        for (const [key, t] of Object.entries(this.profiles.timing_profiles || {})) {
            timingHtml += `
                <div class="bg-slate-800/40 rounded-lg border border-slate-700/50 p-3 text-center timing-card" data-key="${key}">
                    <div class="text-2xl mb-1">${t.icon}</div>
                    <div class="text-xs font-bold text-white">${t.name}</div>
                    <div class="text-xs text-slate-500 mt-1">${t.base_interval}s base</div>
                </div>`;
        }
        timingHtml += '</div>';

        container.html(`
            <div class="space-y-5">
                <!-- Quick Actions -->
                <div class="grid grid-cols-2 md:grid-cols-5 gap-2">
                    <button id="btn-gen-fingerprint" class="px-3 py-2.5 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-fingerprint mr-1"></i>Spoof Fingerprint
                    </button>
                    <button id="btn-gen-disguise" class="px-3 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-mask mr-1"></i>Disguise Request
                    </button>
                    <button id="btn-gen-beacon" class="px-3 py-2.5 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-clock mr-1"></i>Beacon Schedule
                    </button>
                    <button id="btn-gen-domains" class="px-3 py-2.5 bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-globe mr-1"></i>Gen Domains
                    </button>
                    <button id="btn-build-config" class="px-3 py-2.5 bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white rounded-lg text-xs font-bold transition-all">
                        <i class="fas fa-cog mr-1"></i>Full Config
                    </button>
                </div>

                <!-- Traffic Profiles -->
                <div>
                    <h3 class="text-sm font-bold text-white mb-3"><i class="fas fa-network-wired text-violet-400 mr-2"></i>C2 Traffic Profiles</h3>
                    ${trafficHtml}
                </div>

                <!-- Timing Profiles -->
                <div>
                    <h3 class="text-sm font-bold text-white mb-3"><i class="fas fa-clock text-green-400 mr-2"></i>Timing Profiles</h3>
                    ${timingHtml}
                </div>

                <!-- Results Area -->
                <div id="evasion-result" class="hidden bg-slate-900 rounded-xl border border-violet-800 p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 class="text-sm font-bold text-white"><i class="fas fa-terminal text-violet-400 mr-2"></i>Result</h3>
                        <button onclick="$('#evasion-result').hide()" class="text-slate-500 hover:text-white text-xs"><i class="fas fa-times"></i></button>
                    </div>
                    <pre id="evasion-result-content" class="text-xs text-slate-300 bg-slate-950 rounded-lg p-4 overflow-auto max-h-[400px] font-mono"></pre>
                </div>

                <!-- Saved Configs -->
                <div>
                    <h3 class="text-sm font-bold text-white mb-3"><i class="fas fa-save text-amber-400 mr-2"></i>Saved Configurations</h3>
                    <div id="evasion-saved-list" class="space-y-2"></div>
                </div>
            </div>
        `);
    },

    async generateFingerprint() {
        const { value: device } = await Swal.fire({
            title: 'Spoof Fingerprint', input: 'select', inputOptions: { desktop: 'Desktop', mobile: 'Mobile', tablet: 'Tablet' },
            inputPlaceholder: 'Device class', background: '#1e293b', color: '#fff',
        });
        if (!device) return;
        try {
            const res = await $.ajax({ url: '/api/evasion/fingerprint', method: 'POST', contentType: 'application/json', data: JSON.stringify({ device_class: device }) });
            this.showResult(res, 'Spoofed Fingerprint');
        } catch(e) { Swal.fire('Error', 'Failed to generate fingerprint', 'error'); }
    },

    async generateDisguise() {
        const profiles = Object.keys(this.profiles.traffic_profiles || {});
        const opts = {}; profiles.forEach(p => opts[p] = this.profiles.traffic_profiles[p].name);
        const { value: profile } = await Swal.fire({
            title: 'Traffic Profile', input: 'select', inputOptions: opts,
            background: '#1e293b', color: '#fff',
        });
        if (!profile) return;
        try {
            const res = await $.ajax({ url: '/api/evasion/disguise', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ profile, payload: { cmd: 'heartbeat', ts: Date.now() } }) });
            this.showResult(res, 'Disguised Request');
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async generateBeacon() {
        try {
            const res = await $.ajax({ url: '/api/evasion/beacon-schedule', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ profile: 'office_hours', duration_hours: 24 }) });
            this.showResult(res, 'Beacon Schedule \u2014 ' + res.total_beacons + ' beacons, avg ' + res.avg_interval + 's');
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async generateDomains() {
        const { value: company } = await Swal.fire({
            title: 'Company Name', input: 'text', inputPlaceholder: 'e.g. AcmeCorp',
            background: '#1e293b', color: '#fff',
        });
        if (!company) return;
        try {
            const res = await $.ajax({ url: '/api/evasion/domains', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ category: 'business', company, count: 5 }) });
            this.showResult(res, 'Generated Domains');
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async generateDecoy() {
        try {
            const res = await $.ajax({ url: '/api/evasion/decoy', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ pattern: 'browsing', duration_minutes: 30 }) });
            this.showResult(res, 'Decoy Traffic \u2014 ' + res.total_requests + ' requests');
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    async buildConfig() {
        try {
            const res = await $.ajax({ url: '/api/evasion/config', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ options: { device_class: 'desktop', traffic_profile: 'cloud_sync', timing_profile: 'office_hours', domain_category: 'cloud', company_name: 'CloudCorp' } }) });
            this.showResult(res, 'Evasion Config \u2014 Stealth: ' + res.stealth_grade + ' (' + res.overall_stealth_score + '%)');
            this.loadSavedConfigs();
            GrowlNotification.notify({ title: 'Evasion Config Built', description: 'Grade: ' + res.stealth_grade, type: 'success', position: 'top-right' });
        } catch(e) { Swal.fire('Error', 'Failed', 'error'); }
    },

    showResult(data, title) {
        $('#evasion-result').removeClass('hidden').show();
        $('#evasion-result-content').text(JSON.stringify(data, null, 2));
        if (title) $('#evasion-result .text-white').first().html('<i class="fas fa-terminal text-violet-400 mr-2"></i>' + title);
    },

    async loadSavedConfigs() {
        try {
            const res = await $.getJSON('/api/evasion/saved');
            const list = $('#evasion-saved-list');
            if (!res.configs || !res.configs.length) { list.html('<p class="text-slate-600 text-sm text-center py-4">No saved configurations</p>'); return; }
            let html = '';
            for (const c of res.configs) {
                html += '<div class="flex items-center justify-between bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">' +
                    '<div>' +
                        '<span class="text-sm font-bold text-white">' + c.name + '</span>' +
                        '<span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400">' + c.stealth_grade + ' (' + c.stealth_score + '%)</span>' +
                        '<div class="text-xs text-slate-500 mt-1">' + (c.traffic_profile || 'N/A') + ' \u2022 ' + (c.timing_profile || 'N/A') + ' \u2022 ' + new Date(c.created_at).toLocaleString() + '</div>' +
                    '</div>' +
                    '<button class="btn-delete-evasion text-red-400 hover:text-red-300 text-xs" data-id="' + c.id + '"><i class="fas fa-trash"></i></button>' +
                '</div>';
            }
            list.html(html);
        } catch(e) { console.error(e); }
    },

    async deleteConfig(id) {
        const r = await Swal.fire({ title: 'Delete?', icon: 'warning', showCancelButton: true, background: '#1e293b', color: '#fff' });
        if (!r.isConfirmed) return;
        await $.ajax({ url: '/api/evasion/saved/' + id, method: 'DELETE' });
        this.loadSavedConfigs();
    }
};
