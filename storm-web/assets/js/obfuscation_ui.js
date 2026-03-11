/**
 * Storm-Breaker Obfuscation UI Module
 * Frontend interface for payload obfuscation engine
 */

const ObfuscationUI = {
    profiles: {},
    techniques: {},

    init() {
        this.loadProfiles();
        this.bindEvents();
    },

    async loadProfiles() {
        try {
            const resp = await $.get('/api/obfuscate/profiles');
            this.profiles = resp.profiles || {};
            this.techniques = resp.techniques || {};
            this.renderProfileSelector();
            this.renderTechniqueList();
        } catch (e) {
            console.error('Failed to load obfuscation profiles', e);
        }
    },

    renderProfileSelector() {
        const sel = $('#obfuscation-profile');
        sel.empty();
        Object.entries(this.profiles).forEach(([key, prof]) => {
            sel.append(`<option value="${key}">${prof.name} - ${prof.description}</option>`);
        });
    },

    renderTechniqueList() {
        const lang = $('#obfuscation-language').val();
        const container = $('#obfuscation-techniques');
        container.empty();
        const techs = this.techniques[lang] || [];
        if (techs.length === 0) {
            container.html('<p class="text-gray-400 text-sm">No specific techniques for this language</p>');
            return;
        }
        techs.forEach(t => {
            container.append(`
                <label class="flex items-center gap-2 text-sm text-gray-300 cursor-pointer hover:text-white">
                    <input type="checkbox" class="obfusc-technique rounded bg-gray-600 border-gray-500" value="${t}">
                    <span class="font-mono">${t}</span>
                </label>
            `);
        });
    },

    bindEvents() {
        $('#obfuscation-language').on('change', () => this.renderTechniqueList());

        $('#btn-obfuscate').on('click', () => this.obfuscatePayload());

        $('#btn-obfusc-copy').on('click', () => {
            const text = $('#obfuscation-output').text();
            navigator.clipboard.writeText(text).then(() => {
                GrowlNotification.notify({ title: 'Copied', description: 'Obfuscated payload copied to clipboard', type: 'success', position: 'top-right', closeTimeout: 3000 });
            });
        });

        // Integration: Load from payload generator
        $('#btn-obfusc-from-payload').on('click', () => {
            const payloadOutput = $('#payload-output').text();
            if (payloadOutput) {
                $('#obfuscation-input').val(payloadOutput);
                GrowlNotification.notify({ title: 'Loaded', description: 'Payload loaded from generator', type: 'info', position: 'top-right', closeTimeout: 3000 });
            } else {
                GrowlNotification.notify({ title: 'Empty', description: 'No payload in generator output', type: 'warning', position: 'top-right', closeTimeout: 3000 });
            }
        });
    },

    async obfuscatePayload() {
        const payload = $('#obfuscation-input').val().trim();
        if (!payload) {
            Swal.fire('Error', 'Enter a payload to obfuscate', 'error');
            return;
        }

        const language = $('#obfuscation-language').val();
        const profile = $('#obfuscation-profile').val();
        const customTechniques = [];
        $('.obfusc-technique:checked').each(function() { customTechniques.push($(this).val()); });

        $('#btn-obfuscate').prop('disabled', true).html('<i class="fas fa-spinner fa-spin mr-2"></i>Obfuscating...');

        try {
            const resp = await $.ajax({
                url: '/api/obfuscate',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    payload, language, profile,
                    custom_techniques: customTechniques.length > 0 ? customTechniques : undefined,
                }),
            });

            if (resp.error) {
                Swal.fire('Error', resp.error, 'error');
                return;
            }

            $('#obfuscation-output').text(resp.obfuscated || '');

            const techniques = resp.techniques || [];
            const detectionScore = resp.detection_score ?? '—';
            const entropy = typeof resp.entropy === 'number' ? resp.entropy.toFixed(3) : '—';
            const sizeRatio = resp.original_size ? ((resp.obfuscated_size / resp.original_size) * 100).toFixed(0) : '—';
            const detectionColor = detectionScore <= 30 ? 'green' : detectionScore <= 60 ? 'yellow' : 'red';

            $('#obfusc-stats').html(`
                <div class="grid grid-cols-5 gap-3 text-center">
                    <div class="bg-gray-700 rounded-lg p-3">
                        <div class="text-xl font-bold text-cyan-400">${techniques.length}</div>
                        <div class="text-xs text-gray-400">Techniques</div>
                    </div>
                    <div class="bg-gray-700 rounded-lg p-3">
                        <div class="text-xl font-bold text-purple-400">${resp.original_size || 0}→${resp.obfuscated_size || 0}</div>
                        <div class="text-xs text-gray-400">Size (${sizeRatio}%)</div>
                    </div>
                    <div class="bg-gray-700 rounded-lg p-3">
                        <div class="text-xl font-bold text-${detectionColor}-400">${detectionScore}%</div>
                        <div class="text-xs text-gray-400">Detection Risk</div>
                    </div>
                    <div class="bg-gray-700 rounded-lg p-3">
                        <div class="text-xl font-bold text-orange-400">${entropy}</div>
                        <div class="text-xs text-gray-400">Entropy</div>
                    </div>
                    <div class="bg-gray-700 rounded-lg p-3">
                        <div class="text-xl font-bold text-green-400">${resp.profile_name || resp.profile || ''}</div>
                        <div class="text-xs text-gray-400">Profile</div>
                    </div>
                </div>
                <div class="mt-3 flex items-center gap-3">
                    <div class="flex-1 bg-gray-700 rounded-full h-2">
                        <div class="bg-${detectionColor}-500 h-2 rounded-full transition-all" style="width:${detectionScore}%"></div>
                    </div>
                    <span class="text-xs text-${detectionColor}-400 font-semibold">${detectionScore <= 30 ? 'LOW RISK' : detectionScore <= 60 ? 'MEDIUM RISK' : 'HIGH RISK'}</span>
                </div>
                <div class="mt-3 text-xs text-gray-400">
                    <span class="text-gray-500">Applied:</span> ${techniques.join(', ')}
                    ${resp.hash ? `<span class="ml-3 text-gray-500">Hash:</span> <span class="font-mono">${resp.hash}</span>` : ''}
                </div>
            `);

            GrowlNotification.notify({ title: 'Obfuscated', description: `Applied ${techniques.length} techniques — ${detectionScore}% detection risk`, type: 'success', position: 'top-right', closeTimeout: 3000 });
        } catch (e) {
            Swal.fire('Error', 'Obfuscation failed', 'error');
        } finally {
            $('#btn-obfuscate').prop('disabled', false).html('<i class="fas fa-mask mr-2"></i>Obfuscate');
        }
    },
};
