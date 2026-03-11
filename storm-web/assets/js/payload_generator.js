/**
 * Storm-Breaker Payload Generator UI
 * Generate reverse shells, droppers, stagers, and implants
 */

const PayloadGenerator = {
    payloadTypes: {},
    lastResult: null,

    async init() {
        await this.loadTypes();
    },

    async loadTypes() {
        try {
            const resp = await fetch('/api/payloads/types');
            const data = await resp.json();
            this.payloadTypes = data.types || {};
            this.renderTypeSelector();
        } catch (e) { console.error('Load payload types error:', e); }
    },

    renderTypeSelector() {
        const grid = document.getElementById('payloadTypeGrid');
        if (!grid) return;

        const categories = {};
        for (const [key, info] of Object.entries(this.payloadTypes)) {
            const cat = info.category || 'other';
            if (!categories[cat]) categories[cat] = [];
            categories[cat].push({ key, ...info });
        }

        let html = '';
        const catLabels = { shell: '🐚 Reverse Shells', dropper: '📦 Droppers', stager: '🔗 Stagers', implant: '🛰️ Implants', phishing: '🎣 Phishing', recon: '🔍 Recon' };

        for (const [cat, items] of Object.entries(categories)) {
            html += `<div class="mb-4"><h4 class="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">${catLabels[cat] || cat}</h4><div class="grid grid-cols-1 md:grid-cols-2 gap-2">`;
            for (const item of items) {
                const colorMap = { blue: 'border-blue-500/30 hover:border-blue-400', red: 'border-red-500/30 hover:border-red-400', green: 'border-green-500/30 hover:border-green-400', yellow: 'border-yellow-500/30 hover:border-yellow-400', purple: 'border-purple-500/30 hover:border-purple-400', orange: 'border-orange-500/30 hover:border-orange-400', cyan: 'border-cyan-500/30 hover:border-cyan-400' };
                const borderClass = colorMap[item.color] || 'border-gray-600 hover:border-gray-400';

                html += `
                <div class="payload-type-card bg-gray-800/50 rounded-lg p-3 border ${borderClass} cursor-pointer transition-all hover:bg-gray-700/50"
                     onclick="PayloadGenerator.selectType('${item.key}')" data-type="${item.key}">
                    <div class="flex items-center">
                        <i class="fas ${item.icon} text-lg mr-3 text-${item.color}-400"></i>
                        <div>
                            <div class="font-semibold text-white text-sm">${item.name}</div>
                            <div class="text-xs text-gray-400">${item.platform} · ${item.description}</div>
                        </div>
                    </div>
                </div>`;
            }
            html += '</div></div>';
        }

        grid.innerHTML = html;
    },

    selectType(type) {
        // Highlight selected
        document.querySelectorAll('.payload-type-card').forEach(c => c.classList.remove('ring-2', 'ring-cyan-400'));
        const card = document.querySelector(`[data-type="${type}"]`);
        if (card) card.classList.add('ring-2', 'ring-cyan-400');

        document.getElementById('selectedPayloadType').value = type;
        document.getElementById('payloadConfigSection').classList.remove('hidden');
        document.getElementById('payloadOutput').classList.add('hidden');

        // Show/hide template field for phishing type
        const templateField = document.getElementById('payloadTemplateField');
        if (templateField) {
            templateField.style.display = type.includes('phishing') ? 'block' : 'none';
        }
    },

    async generate() {
        const type = document.getElementById('selectedPayloadType').value;
        if (!type) return;

        const lhost = document.getElementById('payloadLhost').value || '127.0.0.1';
        const lport = document.getElementById('payloadLport').value || '4444';
        const callbackUrl = document.getElementById('payloadCallbackUrl').value || `http://${lhost}:${lport}`;
        const template = document.getElementById('payloadTemplate')?.value || '';
        const obfuscate = document.getElementById('payloadObfuscate')?.checked || false;

        const btn = document.getElementById('generatePayloadBtn');
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Generating...';
        btn.disabled = true;

        try {
            const resp = await fetch('/api/payloads/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, lhost, lport, callback_url: callbackUrl, template, obfuscate })
            });
            const data = await resp.json();

            if (data.error) throw new Error(data.error);

            this.lastResult = data;
            this.renderOutput(data);

            GrowlNotification.notify({
                title: 'Payload Generated',
                description: `${this.payloadTypes[type]?.name || type} ready`,
                type: 'success', position: 'top-right', closeTimeout: 3000
            });
        } catch (e) {
            GrowlNotification.notify({
                title: 'Generation Error', description: e.message,
                type: 'error', position: 'top-right', closeTimeout: 4000
            });
        } finally {
            btn.innerHTML = '<i class="fas fa-bolt mr-2"></i>Generate Payload';
            btn.disabled = false;
        }
    },

    renderOutput(data) {
        const container = document.getElementById('payloadOutput');
        container.classList.remove('hidden');

        const langColors = {
            powershell: 'text-blue-400', python: 'text-yellow-400', bash: 'text-green-400',
            html: 'text-orange-400', vbscript: 'text-purple-400',
        };
        const langColor = langColors[data.language] || 'text-gray-300';

        document.getElementById('payloadCodeOutput').innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-bold uppercase ${langColor}">${data.language} · ${data.filename}</span>
                <div class="flex gap-2">
                    <button onclick="PayloadGenerator.copyCode()" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded transition-colors">
                        <i class="fas fa-copy mr-1"></i>Copy Code
                    </button>
                    <button onclick="PayloadGenerator.downloadPayload()" class="text-xs bg-cyan-600 hover:bg-cyan-500 px-3 py-1 rounded transition-colors">
                        <i class="fas fa-download mr-1"></i>Download
                    </button>
                </div>
            </div>
            <pre class="bg-gray-950 rounded p-4 text-sm overflow-x-auto max-h-96 font-mono ${langColor} whitespace-pre-wrap">${this.escapeHtml(data.code)}</pre>`;

        // One-liner
        if (data.oneliner) {
            document.getElementById('payloadOneLiner').innerHTML = `
                <div class="flex items-center justify-between mb-1">
                    <span class="text-xs text-gray-400 font-bold">ONE-LINER</span>
                    <button onclick="PayloadGenerator.copyOneLiner()" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1 rounded transition-colors">
                        <i class="fas fa-copy mr-1"></i>Copy
                    </button>
                </div>
                <code class="block bg-gray-950 rounded p-3 text-xs text-green-400 font-mono break-all">${this.escapeHtml(data.oneliner)}</code>`;
        }
    },

    copyCode() {
        if (this.lastResult) {
            navigator.clipboard.writeText(this.lastResult.code);
            GrowlNotification.notify({ title: 'Copied', description: 'Code copied', type: 'info', position: 'top-right', closeTimeout: 2000 });
        }
    },

    copyOneLiner() {
        if (this.lastResult) {
            navigator.clipboard.writeText(this.lastResult.oneliner);
            GrowlNotification.notify({ title: 'Copied', description: 'One-liner copied', type: 'info', position: 'top-right', closeTimeout: 2000 });
        }
    },

    downloadPayload() {
        if (!this.lastResult) return;
        const blob = new Blob([this.lastResult.code], { type: 'text/plain' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = this.lastResult.filename;
        a.click();
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};
