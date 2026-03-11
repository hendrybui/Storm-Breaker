/**
 * Storm-Breaker Session Hijacker UI
 * Frontend for cookie parsing, JWT analysis, token extraction, replay building
 */
const SessionHijackerUI = {
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
        $(document).on('click', '#btn-parse-cookies', () => this.parseCookies());
        $(document).on('click', '#btn-analyze-jwt', () => this.analyzeJWT());
        $(document).on('click', '#btn-extract-tokens', () => this.extractTokens());
        $(document).on('click', '#btn-build-replay', () => this.buildReplay());
        $(document).on('click', '#btn-assess-session', () => this.assessSession());
        $(document).on('click', '.btn-delete-hijack', function() {
            SessionHijackerUI.deleteRecord($(this).data('id'));
        });
        $(document).on('click', '.replay-tab-btn', function() {
            const lang = $(this).data('lang');
            $('.replay-tab-btn').removeClass('bg-indigo-600').addClass('bg-slate-700');
            $(this).removeClass('bg-slate-700').addClass('bg-indigo-600');
            $('.replay-code-block').addClass('hidden');
            $(`#replay-${lang}`).removeClass('hidden');
        });
    },

    render() {
        const container = $('#session-hijack-dashboard');
        if (!container.length) return;
        container.html(`
            <div class="space-y-5">
                <!-- Tools Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Cookie Parser -->
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-cookie-bite text-amber-400 mr-2"></i>Cookie Parser</h4>
                        <textarea id="cookie-input" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono mb-2" placeholder="Paste cookie string: name1=value1; name2=value2..."></textarea>
                        <button id="btn-parse-cookies" class="w-full px-3 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-search-plus mr-1"></i>Parse & Classify
                        </button>
                    </div>

                    <!-- JWT Analyzer -->
                    <div class="bg-slate-800/60 rounded-lg border border-slate-700/50 p-4">
                        <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-key text-yellow-400 mr-2"></i>JWT Analyzer</h4>
                        <textarea id="jwt-input" rows="3" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white font-mono mb-2" placeholder="Paste JWT token: eyJhbGc..."></textarea>
                        <button id="btn-analyze-jwt" class="w-full px-3 py-2 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg text-xs font-bold transition-colors">
                            <i class="fas fa-unlock-alt mr-1"></i>Decode & Analyze
                        </button>
                    </div>
                </div>

                <!-- Token Extractor -->
                <div class="bg-slate-800/60 rounded-lg border border-indigo-700/50 p-4">
                    <h4 class="text-sm font-bold text-white mb-3"><i class="fas fa-bullseye text-indigo-400 mr-2"></i>Multi-Source Token Extractor</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                        <div>
                            <label class="text-xs text-slate-400">Cookies</label>
                            <textarea id="extract-cookies" rows="2" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white font-mono" placeholder="name=value; name2=value2..."></textarea>
                        </div>
                        <div>
                            <label class="text-xs text-slate-400">URL (with params)</label>
                            <input type="text" id="extract-url" class="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-white" placeholder="https://example.com?token=abc123">
                        </div>
                    </div>
                    <button id="btn-extract-tokens" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-bold transition-colors">
                        <i class="fas fa-crosshairs mr-2"></i>Extract All Tokens
                    </button>
                </div>

                <!-- Session Assessment -->
                <div class="flex gap-2">
                    <button id="btn-assess-session" class="flex-1 px-4 py-3 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-red-500/20">
                        <i class="fas fa-shield-alt mr-2"></i>Full Session Assessment
                    </button>
                    <button id="btn-build-replay" class="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg text-sm font-bold transition-all shadow-lg shadow-indigo-500/20">
                        <i class="fas fa-redo mr-2"></i>Build Replay Request
                    </button>
                </div>

                <!-- Results -->
                <div id="hijack-result" class="hidden bg-slate-900 rounded-xl border border-indigo-800 p-5">
                    <div class="flex items-center justify-between mb-3">
                        <h3 id="hijack-result-title" class="text-sm font-bold text-white"><i class="fas fa-lock text-indigo-400 mr-2"></i>Result</h3>
                        <button onclick="$('#hijack-result').hide()" class="text-slate-500 hover:text-white text-xs"><i class="fas fa-times"></i></button>
                    </div>
                    <div id="hijack-result-visual" class="mb-3"></div>
                    <div id="hijack-result-replay" class="hidden mb-3"></div>
                    <pre id="hijack-result-raw" class="text-xs text-slate-300 bg-slate-950 rounded-lg p-4 overflow-auto max-h-[350px] font-mono"></pre>
                </div>

                <!-- History -->
                <div>
                    <h3 class="text-sm font-bold text-white mb-3"><i class="fas fa-history text-rose-400 mr-2"></i>Hijack History</h3>
                    <div id="hijack-history-list" class="space-y-2 max-h-[250px] overflow-y-auto"></div>
                </div>
            </div>
        `);
    },

    async parseCookies() {
        const input = $('#cookie-input').val().trim();
        if (!input) { Swal.fire('Error', 'Paste cookies first', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/session-hijack/parse-cookies', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ cookie_string: input }) });
            this.showResult(res, `Cookies: ${res.total} found, ${res.high_value_count} high-value`, this.renderCookieVisual(res));
        } catch(e) { Swal.fire('Error', 'Parse failed', 'error'); }
    },

    async analyzeJWT() {
        const token = $('#jwt-input').val().trim();
        if (!token) { Swal.fire('Error', 'Paste JWT first', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/session-hijack/analyze-jwt', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ token }) });
            this.showResult(res, `JWT: ${res.algorithm || 'unknown'} — Hijack: ${res.hijack_value}`, this.renderJWTVisual(res));
        } catch(e) { Swal.fire('Error', 'Analysis failed', 'error'); }
    },

    async extractTokens() {
        const data = {};
        const cookies = $('#extract-cookies').val().trim();
        const url = $('#extract-url').val().trim();
        if (cookies) data.cookies = cookies;
        if (url) data.url = url;
        if (!Object.keys(data).length) { Swal.fire('Error', 'Provide at least one source', 'warning'); return; }
        try {
            const res = await $.ajax({ url: '/api/session-hijack/extract-tokens', method: 'POST', contentType: 'application/json',
                data: JSON.stringify(data) });
            this.showResult(res, `Tokens: ${res.total} extracted (${res.critical_count} critical)`, this.renderTokenVisual(res));
        } catch(e) { Swal.fire('Error', 'Extraction failed', 'error'); }
    },

    async buildReplay() {
        const cookies = $('#cookie-input').val().trim() || $('#extract-cookies').val().trim();
        if (!cookies) { Swal.fire('Error', 'Parse cookies first', 'warning'); return; }
        const { value: url } = await Swal.fire({
            title: 'Target URL', input: 'text', inputValue: 'https://target.example.com',
            background: '#1e293b', color: '#fff',
        });
        if (!url) return;
        try {
            const res = await $.ajax({ url: '/api/session-hijack/build-replay', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ cookies: cookies.split(';').map(c => { const [n, ...v] = c.split('='); return { name: n.trim(), value: v.join('=').trim() }; }), target_url: url }) });
            this.showResult(res, `Replay Request Built`, '', true);
            this.renderReplayCode(res);
        } catch(e) { Swal.fire('Error', 'Build failed', 'error'); }
    },

    async assessSession() {
        const cookies = $('#cookie-input').val().trim() || $('#extract-cookies').val().trim();
        if (!cookies) { Swal.fire('Error', 'Parse cookies first', 'warning'); return; }
        const cookieList = cookies.split(';').map(c => { const [n, ...v] = c.split('='); return { name: n.trim(), value: v.join('=').trim(), category: 'unknown', risk: 'unknown' }; });
        try {
            const res = await $.ajax({ url: '/api/session-hijack/assess', method: 'POST', contentType: 'application/json',
                data: JSON.stringify({ cookies: cookieList }) });
            this.showResult(res, `Session: ${res.session_strength} — Hijack: ${res.hijack_feasibility}`, this.renderAssessVisual(res));
            this.loadHistory();
            GrowlNotification.notify({ title: 'Session Assessed', description: `Feasibility: ${res.hijack_feasibility}`, type: 'warning', position: 'top-right' });
        } catch(e) { Swal.fire('Error', 'Assessment failed', 'error'); }
    },

    renderCookieVisual(res) {
        let html = '<div class="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">';
        for (const [cat, count] of Object.entries(res.risk_summary || {})) {
            const color = { critical: 'red', high: 'orange', medium: 'yellow', low: 'green', none: 'slate', unknown: 'slate' }[cat] || 'slate';
            html += `<div class="bg-${color}-500/10 border border-${color}-500/30 rounded-lg p-2 text-center">
                <div class="text-lg font-bold text-${color}-400">${count}</div>
                <div class="text-xs text-slate-400">${cat}</div>
            </div>`;
        }
        html += '</div>';
        if (res.platform_hints && res.platform_hints.length) {
            html += `<div class="text-xs text-slate-400">Platform hints: <span class="text-white">${res.platform_hints.join(', ')}</span></div>`;
        }
        return html;
    },

    renderJWTVisual(res) {
        if (!res.is_valid_jwt) return `<div class="text-red-400 text-sm">Invalid JWT: ${res.error || 'Unknown error'}</div>`;
        const color = { critical: 'red', high: 'orange', medium: 'yellow', low: 'green' }[res.hijack_value] || 'slate';
        let html = `<div class="flex gap-4 items-center mb-3">
            <div class="text-center"><div class="text-2xl font-bold text-${color}-400">${res.hijack_value}</div><div class="text-xs text-slate-400">Hijack Value</div></div>
            <div class="text-xs text-slate-300"><b>Algorithm:</b> ${res.algorithm}<br><b>Expired:</b> ${res.is_expired === true ? '❌ Yes' : res.is_expired === false ? '✅ No' : '❓ Unknown'}</div>
        </div>`;
        if (res.vulnerabilities && res.vulnerabilities.length) {
            html += '<div class="space-y-1">';
            for (const v of res.vulnerabilities) {
                html += `<div class="text-xs bg-red-500/10 border border-red-500/30 rounded px-2 py-1 text-red-300">⚠️ ${v.severity}: ${v.description}</div>`;
            }
            html += '</div>';
        }
        return html;
    },

    renderTokenVisual(res) {
        let html = `<div class="flex gap-3 mb-2">
            <span class="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">${res.critical_count} Critical</span>
            <span class="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs">${res.high_count} High</span>
            <span class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">${res.jwt_count} JWT</span>
        </div>`;
        return html;
    },

    renderAssessVisual(res) {
        const score = res.risk_score || 0;
        const color = score >= 70 ? 'red' : score >= 50 ? 'orange' : score >= 30 ? 'yellow' : 'green';
        let html = `<div class="flex items-center gap-4 mb-3">
            <div class="text-center"><div class="text-3xl font-bold text-${color}-400">${score}</div><div class="text-xs text-slate-400">Risk Score</div></div>
            <div class="flex-1"><div class="w-full bg-slate-800 rounded-full h-3"><div class="bg-${color}-500 h-3 rounded-full" style="width:${score}%"></div></div>
                <div class="text-xs text-slate-400 mt-1">Hijack: ${res.hijack_feasibility} | Strength: ${res.session_strength}</div></div>
        </div>`;
        if (res.attack_vectors && res.attack_vectors.length) {
            html += '<div class="space-y-1 mb-2">';
            for (const v of res.attack_vectors) {
                const c = { critical: 'red', high: 'orange', medium: 'yellow' }[v.severity] || 'slate';
                html += `<div class="text-xs bg-${c}-500/10 border border-${c}-500/30 rounded px-2 py-1 text-${c}-300">⚡ ${v.vector}: ${v.description}</div>`;
            }
            html += '</div>';
        }
        return html;
    },

    renderReplayCode(res) {
        const code = res.replay_code || {};
        $('#hijack-result-replay').removeClass('hidden').html(`
            <div class="flex gap-1 mb-2">
                <button class="replay-tab-btn px-3 py-1 bg-indigo-600 text-white rounded text-xs" data-lang="curl">cURL</button>
                <button class="replay-tab-btn px-3 py-1 bg-slate-700 text-white rounded text-xs" data-lang="python">Python</button>
                <button class="replay-tab-btn px-3 py-1 bg-slate-700 text-white rounded text-xs" data-lang="javascript">JavaScript</button>
            </div>
            <pre id="replay-curl" class="replay-code-block text-xs text-green-300 bg-slate-950 rounded-lg p-3 overflow-auto max-h-[200px] font-mono">${this.escapeHtml(code.curl || '')}</pre>
            <pre id="replay-python" class="replay-code-block hidden text-xs text-blue-300 bg-slate-950 rounded-lg p-3 overflow-auto max-h-[200px] font-mono">${this.escapeHtml(code.python || '')}</pre>
            <pre id="replay-javascript" class="replay-code-block hidden text-xs text-yellow-300 bg-slate-950 rounded-lg p-3 overflow-auto max-h-[200px] font-mono">${this.escapeHtml(code.javascript || '')}</pre>
        `);
    },

    showResult(data, title, visualHtml, hideRaw) {
        $('#hijack-result').removeClass('hidden').show();
        $('#hijack-result-title').html(`<i class="fas fa-lock text-indigo-400 mr-2"></i>${title}`);
        $('#hijack-result-visual').html(visualHtml || '');
        $('#hijack-result-replay').addClass('hidden');
        if (hideRaw) {
            $('#hijack-result-raw').hide();
        } else {
            $('#hijack-result-raw').show().text(JSON.stringify(data, null, 2));
        }
    },

    escapeHtml(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    },

    async loadHistory() {
        try {
            const res = await $.getJSON('/api/session-hijack/history');
            const list = $('#hijack-history-list');
            if (!res.records || !res.records.length) { list.html('<p class="text-slate-600 text-sm text-center py-4">No hijack records</p>'); return; }
            let html = '';
            for (const r of res.records.slice(0, 15)) {
                const feasColor = { very_high: 'red', high: 'orange', medium: 'yellow', low: 'green' }[r.hijack_feasibility] || 'slate';
                html += `<div class="flex items-center justify-between bg-slate-800/50 rounded-lg border border-slate-700/50 p-3">
                    <div>
                        <span class="text-sm font-bold text-white">${r.victim_ip}</span>
                        <span class="ml-2 text-xs px-2 py-0.5 rounded-full bg-${feasColor}-500/20 text-${feasColor}-400">${r.hijack_feasibility} (${r.risk_score})</span>
                        <div class="text-xs text-slate-500 mt-1">${r.token_count} tokens • ${r.critical_tokens} critical • ${new Date(r.created_at).toLocaleString()}</div>
                    </div>
                    <button class="btn-delete-hijack text-red-400 hover:text-red-300 text-xs" data-id="${r.id}"><i class="fas fa-trash"></i></button>
                </div>`;
            }
            list.html(html);
        } catch(e) { console.error(e); }
    },

    async deleteRecord(id) {
        await $.ajax({ url: `/api/session-hijack/${id}`, method: 'DELETE' });
        this.loadHistory();
    }
};
