/**
 * Storm-Breaker Lure Generator UI Module
 * Create phishing email/SMS lures from templates with variable substitution
 */

const LureGeneratorUI = {
    categories: {},
    savedLures: [],

    init() {
        this.loadCategories();
        this.loadSavedLures();
        this.bindEvents();
    },

    async loadCategories() {
        try {
            const resp = await $.get('/api/lures/categories');
            this.categories = resp.categories || {};
            this.renderCategorySelector();
        } catch (e) {
            console.error('Failed to load lure categories', e);
        }
    },

    async loadSavedLures() {
        try {
            const resp = await $.get('/api/lures/saved');
            this.savedLures = resp.lures || [];
            this.renderSavedLures();
        } catch (e) {
            console.error('Failed to load saved lures', e);
        }
    },

    renderCategorySelector() {
        const sel = $('#lure-category');
        sel.empty();
        Object.entries(this.categories).forEach(([key, cat]) => {
            sel.append(`<option value="${key}">${cat.icon} ${cat.name} (${cat.template_count} templates)</option>`);
        });
        this.renderTemplateSelector();
    },

    renderTemplateSelector() {
        const category = $('#lure-category').val();
        const cat = this.categories[category];
        if (!cat) return;

        const sel = $('#lure-template');
        sel.empty();
        cat.templates.forEach((t, i) => {
            sel.append(`<option value="${i}">${t.name}${t.has_sms ? ' 📱' : ''}</option>`);
        });
    },

    bindEvents() {
        $('#lure-category').on('change', () => {
            this.renderTemplateSelector();
        });

        $('#btn-preview-lure').on('click', () => this.previewTemplate());
        $('#btn-generate-lure').on('click', () => this.generateLure());
        $('#btn-save-lure').on('click', () => this.saveLure());
        $('#btn-copy-lure').on('click', () => {
            const content = $('#lure-output-body').text();
            if (content) {
                navigator.clipboard.writeText(content);
                GrowlNotification.notify({ title: 'Copied', description: 'Lure content copied', type: 'success', position: 'top-right', closeTimeout: 3000 });
            }
        });
    },

    async previewTemplate() {
        try {
            const resp = await $.ajax({
                url: '/api/lures/preview',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    category: $('#lure-category').val(),
                    template_index: parseInt($('#lure-template').val()),
                }),
            });

            if (resp.error) {
                Swal.fire('Error', resp.error, 'error');
                return;
            }

            // Show available variables as clickable badges
            const vars = resp.available_variables || [];
            this.currentVariables = vars;
            $('#lure-variables-info').html(`
                <div class="text-xs text-gray-400 mb-2">Available variables (${vars.length}):</div>
                <div class="flex flex-wrap gap-1 mb-3">
                    ${vars.map(v => `<span class="px-2 py-0.5 bg-indigo-900 text-indigo-300 rounded font-mono text-xs cursor-pointer hover:bg-indigo-800" onclick="LureGeneratorUI.focusVariable('${v}')">{{${v}}}</span>`).join('')}
                </div>
            `);

            // Dynamically generate variable input fields based on template
            this.renderVariableInputs(vars);

            // Show raw template preview
            $('#lure-output-subject').text(resp.subject || '');
            $('#lure-output-body').text(resp.body || '');
            if (resp.sms) {
                $('#lure-output-sms').text(resp.sms).parent().show();
            } else {
                $('#lure-output-sms').parent().hide();
            }
        } catch (e) {
            Swal.fire('Error', 'Failed to preview template', 'error');
        }
    },

    currentVariables: [],

    renderVariableInputs(vars) {
        const container = $('#lure-variable-inputs');
        if (!container.length) return;
        container.empty();

        // Common variables to show input fields for
        const varLabels = {
            name: 'Target Name', company: 'Company Name', link: 'Phishing URL',
            deadline: 'Deadline Date', hours: 'Hours Until Expiry',
            email: 'Target Email', company_domain: 'Company Domain',
            location: 'Location', device: 'Device', source_ip: 'Source IP',
            amount: 'Amount ($)', tracking: 'Tracking Number',
            ref_number: 'Reference Number', sender_name: 'Sender Name',
            sender_email: 'Sender Email', document_name: 'Document Name',
            folder_name: 'Folder Name', merchant_name: 'Merchant',
            card_last4: 'Card Last 4', doctor_name: 'Doctor Name',
            tax_year: 'Tax Year', item_count: 'Item Count', weight: 'Weight (lbs)',
        };

        vars.forEach(v => {
            const label = varLabels[v] || v.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
            container.append(`
                <div class="flex items-center gap-2">
                    <label class="text-xs text-gray-400 w-32 text-right">${label}:</label>
                    <input type="text" id="lure-var-${v}" class="lure-var-input flex-1 bg-gray-600 text-white rounded px-2 py-1 text-xs border border-gray-500 focus:border-cyan-500 outline-none" placeholder="${v}" data-var="${v}">
                </div>
            `);
        });
    },

    focusVariable(varName) {
        const el = $(`#lure-var-${varName}`);
        if (el.length) {
            el.focus().addClass('ring-2 ring-indigo-500');
            setTimeout(() => el.removeClass('ring-2 ring-indigo-500'), 1500);
        }
    },

    async generateLure() {
        const variables = {};
        // Collect all dynamic variable inputs
        $('.lure-var-input').each(function() {
            const val = $(this).val();
            const varName = $(this).data('var');
            if (val && varName) variables[varName] = val;
        });
        // Also collect from legacy hardcoded fields if they exist
        ['name', 'company', 'link', 'deadline', 'hours'].forEach(v => {
            const el = $(`#lure-var-${v}`);
            if (el.length && el.val()) variables[v] = el.val();
        });

        try {
            const resp = await $.ajax({
                url: '/api/lures/generate',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    category: $('#lure-category').val(),
                    template_index: parseInt($('#lure-template').val()),
                    variables,
                    type: $('#lure-type').val() || 'email',
                }),
            });

            if (resp.error) {
                Swal.fire('Error', resp.error, 'error');
                return;
            }

            $('#lure-output-subject').text(resp.subject || '');
            $('#lure-output-body').text(resp.body || '');

            // Show stats for SMS type
            let statsHtml = '';
            if (resp.type === 'sms' && resp.char_count) {
                const segColor = resp.sms_segments > 1 ? 'yellow' : 'green';
                statsHtml = `
                    <div class="flex items-center gap-3 mt-2 text-xs">
                        <span class="px-2 py-1 bg-gray-700 rounded text-${segColor}-400">
                            <i class="fas fa-sms mr-1"></i>${resp.char_count} chars • ${resp.sms_segments} SMS segment${resp.sms_segments > 1 ? 's' : ''}
                        </span>
                    </div>`;
            }
            $('#lure-output-stats').html(statsHtml);

            GrowlNotification.notify({ title: 'Generated', description: `${resp.category} — ${resp.template} (${resp.type})`, type: 'success', position: 'top-right', closeTimeout: 3000 });
        } catch (e) {
            Swal.fire('Error', 'Failed to generate lure', 'error');
        }
    },

    async saveLure() {
        const subject = $('#lure-output-subject').text();
        const body = $('#lure-output-body').text();
        if (!body) {
            Swal.fire('Error', 'Generate a lure first', 'warning');
            return;
        }

        const { value: name } = await Swal.fire({
            title: 'Save Lure',
            input: 'text',
            inputLabel: 'Lure name',
            inputPlaceholder: 'My custom lure',
            showCancelButton: true,
        });

        if (name) {
            try {
                await $.ajax({
                    url: '/api/lures/save',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        name,
                        category: $('#lure-category').val(),
                        type: $('#lure-type').val() || 'email',
                        subject,
                        body,
                    }),
                });
                this.loadSavedLures();
                GrowlNotification.notify({ title: 'Saved', description: `Lure "${name}" saved`, type: 'success', position: 'top-right', closeTimeout: 3000 });
            } catch (e) {
                Swal.fire('Error', 'Failed to save lure', 'error');
            }
        }
    },

    renderSavedLures() {
        const container = $('#saved-lures-list');
        container.empty();
        if (this.savedLures.length === 0) {
            container.html('<p class="text-gray-400 text-sm text-center py-4">No saved lures</p>');
            return;
        }
        this.savedLures.forEach(l => {
            container.append(`
                <div class="bg-gray-700 rounded-lg p-3 flex items-center justify-between hover:bg-gray-600 transition-colors">
                    <div>
                        <div class="text-sm font-semibold text-white">${this.escapeHtml(l.name)}</div>
                        <div class="text-xs text-gray-400">${l.category || ''} • ${l.lure_type || 'email'} • ${l.created_at || ''}</div>
                    </div>
                    <div class="flex gap-2">
                        <button onclick="LureGeneratorUI.loadSavedLure(${l.id})" class="px-2 py-1 bg-cyan-600 text-white rounded text-xs hover:bg-cyan-500"><i class="fas fa-redo"></i></button>
                        <button onclick="LureGeneratorUI.deleteSavedLure(${l.id})" class="px-2 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-500"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
            `);
        });
    },

    loadSavedLure(id) {
        const lure = this.savedLures.find(l => l.id === id);
        if (lure) {
            $('#lure-output-subject').text(lure.subject || '');
            $('#lure-output-body').text(lure.body || '');
            GrowlNotification.notify({ title: 'Loaded', description: `Lure "${lure.name}" loaded`, type: 'info', position: 'top-right', closeTimeout: 3000 });
        }
    },

    async deleteSavedLure(id) {
        const result = await Swal.fire({
            title: 'Delete Lure?', icon: 'warning', showCancelButton: true, confirmButtonColor: '#dc2626', confirmButtonText: 'Delete',
        });
        if (result.isConfirmed) {
            await $.ajax({ url: `/api/lures/saved/${id}`, method: 'DELETE' });
            this.loadSavedLures();
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },
};
