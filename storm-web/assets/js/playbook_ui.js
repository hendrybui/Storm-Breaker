/**
 * Storm-Breaker Playbook Automation UI Module v2.0
 * Create and execute multi-step attack automation workflows
 * Supports: 10 action types, step reorder, variable passing, live execution feedback
 */

const PlaybookUI = {
    playbooks: [],
    availableActions: [
        { id: 'generate_payload', name: 'Generate Payload', icon: 'fas fa-bomb', color: 'red', category: 'attack',
          params: ['type', 'lhost', 'lport'], description: 'Generate a reverse shell or exploitation payload' },
        { id: 'obfuscate', name: 'Obfuscate Payload', icon: 'fas fa-mask', color: 'purple', category: 'attack',
          params: ['payload', 'language', 'profile'], description: 'Apply multi-layer obfuscation to a payload' },
        { id: 'generate_lure', name: 'Generate Lure', icon: 'fas fa-envelope', color: 'blue', category: 'social',
          params: ['category', 'template_index', 'type'], description: 'Create a phishing email or SMS lure' },
        { id: 'generate_report', name: 'Generate Report', icon: 'fas fa-file-pdf', color: 'indigo', category: 'reporting',
          params: ['title', 'organization', 'target', 'classification'], description: 'Generate a professional pentest report' },
        { id: 'send_telegram', name: 'Send Telegram Alert', icon: 'fab fa-telegram', color: 'sky', category: 'notify',
          params: ['message'], description: 'Send a notification via Telegram bot integration' },
        { id: 'export_data', name: 'Export Data', icon: 'fas fa-download', color: 'emerald', category: 'reporting',
          params: ['data_type', 'format'], description: 'Export collected data (credentials, sessions, etc.)' },
        { id: 'http_request', name: 'HTTP Request', icon: 'fas fa-globe', color: 'orange', category: 'recon',
          params: ['url', 'method', 'headers'], description: 'Make an external HTTP request (webhook, C2)' },
        { id: 'conditional', name: 'Conditional Check', icon: 'fas fa-code-branch', color: 'pink', category: 'logic',
          params: ['condition', 'variable', 'value'], description: 'Check a condition before continuing' },
        { id: 'delay', name: 'Delay', icon: 'fas fa-clock', color: 'yellow', category: 'logic',
          params: ['seconds'], description: 'Wait before executing the next step' },
        { id: 'log', name: 'Log Message', icon: 'fas fa-terminal', color: 'green', category: 'logic',
          params: ['message'], description: 'Log a message to the execution record' },
    ],

    init() {
        this.loadPlaybooks();
        this.bindEvents();
    },

    async loadPlaybooks() {
        try {
            const resp = await $.get('/api/playbooks');
            this.playbooks = resp.playbooks || [];
            this.renderPlaybooks();
        } catch (e) {
            console.error('Failed to load playbooks', e);
        }
    },

    renderPlaybooks() {
        const container = $('#playbook-list');
        container.empty();

        if (this.playbooks.length === 0) {
            container.html(`
                <div class="text-center text-gray-400 py-10">
                    <i class="fas fa-book text-5xl mb-4 opacity-50"></i>
                    <p class="text-lg mb-1">No Playbooks Created</p>
                    <p class="text-sm text-gray-500">Create automated multi-step attack workflows</p>
                    <button onclick="PlaybookUI.showPlaybookBuilder()" class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 text-sm">
                        <i class="fas fa-plus mr-2"></i>Create First Playbook
                    </button>
                </div>
            `);
            return;
        }

        this.playbooks.forEach(pb => {
            const steps = typeof pb.steps === 'string' ? JSON.parse(pb.steps) : (pb.steps || []);
            const execLog = typeof pb.execution_log === 'string' ? JSON.parse(pb.execution_log) : (pb.execution_log || []);
            const statusConfig = {
                draft: { color: 'gray', icon: 'fas fa-pencil-alt' },
                ready: { color: 'cyan', icon: 'fas fa-check-circle' },
                running: { color: 'yellow', icon: 'fas fa-spinner fa-spin' },
                completed: { color: 'green', icon: 'fas fa-check-double' },
                error: { color: 'red', icon: 'fas fa-exclamation-triangle' },
            };
            const sc = statusConfig[pb.status] || statusConfig.draft;
            const lastRun = pb.last_run ? new Date(pb.last_run).toLocaleString() : 'Never';
            const successCount = execLog.filter(l => l.status === 'success').length;
            const errorCount = execLog.filter(l => l.status === 'error').length;

            container.append(`
                <div class="bg-gray-700 rounded-lg p-4 hover:bg-gray-650 transition-all border border-gray-600 hover:border-gray-500">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-3">
                            <div class="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                                <i class="fas fa-book text-white"></i>
                            </div>
                            <div>
                                <div class="font-semibold text-white text-sm">${this.escapeHtml(pb.name)}</div>
                                <div class="text-xs text-gray-400">${pb.description || 'No description'}</div>
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <span class="flex items-center gap-1 px-2 py-1 text-xs rounded bg-${sc.color}-900 text-${sc.color}-300">
                                <i class="${sc.icon} text-[10px]"></i> ${pb.status}
                            </span>
                            <span class="text-xs text-gray-500">${steps.length} steps</span>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-1 mb-3">
                        ${steps.map((s, i) => {
                            const action = this.availableActions.find(a => a.id === s.action);
                            const logEntry = execLog[i];
                            const stepColor = logEntry ? (logEntry.status === 'success' ? 'green' : logEntry.status === 'error' ? 'red' : 'gray') : 'gray';
                            return `<span class="px-2 py-0.5 bg-${stepColor}-900 text-${stepColor}-300 rounded text-xs flex items-center gap-1">
                                <i class="${action ? action.icon : 'fas fa-cog'} text-[9px]"></i>
                                ${i + 1}. ${action ? action.name : s.action}
                            </span>`;
                        }).join('<i class="fas fa-arrow-right text-gray-600 mx-0.5 text-[8px] self-center"></i>')}
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="text-xs text-gray-500">
                            <i class="fas fa-history mr-1"></i>Last: ${lastRun}
                            ${pb.run_count ? ` · Runs: ${pb.run_count}` : ''}
                            ${execLog.length > 0 ? ` · <span class="text-green-400">${successCount}✓</span> <span class="text-red-400">${errorCount}✗</span>` : ''}
                        </div>
                        <div class="flex gap-1.5">
                            <button onclick="PlaybookUI.executePlaybook(${pb.id})" class="px-3 py-1.5 bg-green-600 text-white rounded text-xs hover:bg-green-500 font-medium">
                                <i class="fas fa-play mr-1"></i>Run
                            </button>
                            <button onclick="PlaybookUI.editPlaybook(${pb.id})" class="px-3 py-1.5 bg-cyan-600 text-white rounded text-xs hover:bg-cyan-500">
                                <i class="fas fa-edit mr-1"></i>Edit
                            </button>
                            <button onclick="PlaybookUI.duplicatePlaybook(${pb.id})" class="px-2 py-1.5 bg-gray-600 text-white rounded text-xs hover:bg-gray-500" title="Duplicate">
                                <i class="fas fa-copy"></i>
                            </button>
                            <button onclick="PlaybookUI.viewLog(${pb.id})" class="px-2 py-1.5 bg-gray-600 text-white rounded text-xs hover:bg-gray-500" title="View Log">
                                <i class="fas fa-file-alt"></i>
                            </button>
                            <button onclick="PlaybookUI.deletePlaybook(${pb.id})" class="px-2 py-1.5 bg-red-600 text-white rounded text-xs hover:bg-red-500" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `);
        });
    },

    bindEvents() {
        $('#btn-new-playbook').on('click', () => this.showPlaybookBuilder());
        $('#btn-add-step').on('click', () => this.addStepToBuilder());
        $('#btn-save-playbook').on('click', () => this.savePlaybook());
    },

    showPlaybookBuilder(existing = null) {
        const builderSteps = existing ? (typeof existing.steps === 'string' ? JSON.parse(existing.steps) : existing.steps) : [];

        $('#playbook-builder').show();
        $('#playbook-builder-name').val(existing ? existing.name : '');
        $('#playbook-builder-desc').val(existing ? existing.description : '');
        $('#playbook-builder-id').val(existing ? existing.id : '');
        this.builderSteps = builderSteps;
        this.renderBuilderSteps();
        this.renderActionPalette();
    },

    renderActionPalette() {
        const container = $('#action-palette');
        container.empty();

        const categories = {
            attack: { label: 'Attack', icon: 'fas fa-crosshairs' },
            social: { label: 'Social Engineering', icon: 'fas fa-users' },
            recon: { label: 'Recon', icon: 'fas fa-search' },
            reporting: { label: 'Reporting', icon: 'fas fa-chart-bar' },
            notify: { label: 'Notifications', icon: 'fas fa-bell' },
            logic: { label: 'Flow Control', icon: 'fas fa-project-diagram' },
        };

        Object.entries(categories).forEach(([catKey, catInfo]) => {
            const actions = this.availableActions.filter(a => a.category === catKey);
            if (actions.length === 0) return;

            container.append(`<div class="text-[10px] text-gray-500 uppercase tracking-wider mt-2 mb-1 first:mt-0"><i class="${catInfo.icon} mr-1"></i>${catInfo.label}</div>`);
            actions.forEach(a => {
                container.append(`
                    <button onclick="PlaybookUI.addStep('${a.id}')" class="flex items-center gap-2 px-3 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors text-xs text-white w-full text-left group" title="${a.description}">
                        <i class="${a.icon} text-${a.color}-400 w-4 text-center"></i>
                        <span class="flex-1">${a.name}</span>
                        <i class="fas fa-plus text-gray-500 group-hover:text-white text-[10px]"></i>
                    </button>
                `);
            });
        });
    },

    builderSteps: [],

    addStep(actionId) {
        const action = this.availableActions.find(a => a.id === actionId);
        if (!action) return;

        const params = {};
        action.params.forEach(p => { params[p] = ''; });

        this.builderSteps.push({ action: actionId, params });
        this.renderBuilderSteps();
    },

    removeStep(index) {
        this.builderSteps.splice(index, 1);
        this.renderBuilderSteps();
    },

    moveStep(index, direction) {
        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= this.builderSteps.length) return;
        const temp = this.builderSteps[index];
        this.builderSteps[index] = this.builderSteps[newIndex];
        this.builderSteps[newIndex] = temp;
        this.renderBuilderSteps();
    },

    renderBuilderSteps() {
        const container = $('#builder-steps');
        container.empty();

        if (this.builderSteps.length === 0) {
            container.html('<div class="text-center text-gray-400 py-8 text-sm"><i class="fas fa-arrow-up text-2xl mb-2 opacity-50"></i><br>Click an action above to add steps</div>');
            return;
        }

        const paramHints = {
            type: 'ps_reverse, py_reverse, bash_reverse',
            lhost: '10.0.0.1', lport: '4444',
            payload: 'Code or {{prev_output}}',
            language: 'powershell, python, javascript, bash',
            profile: 'low, medium, high, aggressive, stealth',
            category: 'it_support, hr_department, finance, banking',
            template_index: '0, 1, 2...',
            seconds: '1-10',
            message: 'Text to log or send',
            title: 'Report title',
            organization: 'Your organization',
            target: 'Target organization',
            classification: 'CONFIDENTIAL',
            data_type: 'credentials, sessions, keystrokes',
            format: 'json, csv',
            url: 'https://webhook.example.com',
            method: 'GET, POST',
            headers: '{"Authorization": "Bearer ..."}',
            condition: 'has_data, equals, not_empty',
            variable: 'Variable name to check',
            value: 'Expected value',
        };

        this.builderSteps.forEach((step, i) => {
            const action = this.availableActions.find(a => a.id === step.action);

            const paramsHtml = Object.entries(step.params).map(([key, val]) => `
                <div class="flex items-center gap-2">
                    <label class="text-[10px] text-gray-400 w-24 text-right">${key}:</label>
                    <input type="text" class="step-param flex-1 bg-gray-600 text-white rounded px-2 py-1 text-xs border border-gray-500 focus:border-cyan-500 outline-none"
                           data-step="${i}" data-param="${key}" value="${this.escapeHtml(val || '')}" placeholder="${paramHints[key] || key}">
                </div>
            `).join('');

            container.append(`
                <div class="bg-gray-700 rounded-lg p-3 border-l-4 border-${action ? action.color : 'gray'}-500">
                    <div class="flex items-center justify-between mb-2">
                        <div class="flex items-center gap-2">
                            <span class="w-5 h-5 bg-gray-600 rounded flex items-center justify-center text-[10px] text-gray-300 font-bold">${i + 1}</span>
                            <i class="${action ? action.icon : 'fas fa-cog'} text-${action ? action.color : 'gray'}-400 text-sm"></i>
                            <span class="text-sm text-white font-medium">${action ? action.name : step.action}</span>
                            <span class="text-[10px] text-gray-500 hidden sm:inline">${action ? action.description : ''}</span>
                        </div>
                        <div class="flex items-center gap-1">
                            <button onclick="PlaybookUI.moveStep(${i}, -1)" class="text-gray-400 hover:text-white text-xs px-1 ${i === 0 ? 'opacity-30 pointer-events-none' : ''}"><i class="fas fa-arrow-up"></i></button>
                            <button onclick="PlaybookUI.moveStep(${i}, 1)" class="text-gray-400 hover:text-white text-xs px-1 ${i === this.builderSteps.length - 1 ? 'opacity-30 pointer-events-none' : ''}"><i class="fas fa-arrow-down"></i></button>
                            <button onclick="PlaybookUI.removeStep(${i})" class="text-red-400 hover:text-red-300 text-xs px-1 ml-1"><i class="fas fa-times"></i></button>
                        </div>
                    </div>
                    <div class="space-y-1">${paramsHtml}</div>
                </div>
            `);
        });

        // Bind param change events
        $('.step-param').off('change input').on('change input', function() {
            const stepIdx = $(this).data('step');
            const param = $(this).data('param');
            PlaybookUI.builderSteps[stepIdx].params[param] = $(this).val();
        });
    },

    async savePlaybook() {
        const name = $('#playbook-builder-name').val().trim();
        if (!name) {
            Swal.fire('Error', 'Enter a playbook name', 'warning');
            return;
        }

        // Collect latest param values
        $('.step-param').each(function() {
            const stepIdx = $(this).data('step');
            const param = $(this).data('param');
            PlaybookUI.builderSteps[stepIdx].params[param] = $(this).val();
        });

        if (this.builderSteps.length === 0) {
            Swal.fire('Error', 'Add at least one step to the playbook', 'warning');
            return;
        }

        const existingId = $('#playbook-builder-id').val();

        try {
            if (existingId) {
                await $.ajax({
                    url: `/api/playbooks/${existingId}`,
                    method: 'PUT',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        name,
                        description: $('#playbook-builder-desc').val(),
                        steps: this.builderSteps,
                        status: 'ready',
                    }),
                });
            } else {
                await $.ajax({
                    url: '/api/playbooks',
                    method: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        name,
                        description: $('#playbook-builder-desc').val(),
                        steps: this.builderSteps,
                    }),
                });
            }

            $('#playbook-builder').hide();
            this.loadPlaybooks();
            GrowlNotification.notify({ title: 'Saved', description: `Playbook "${name}" saved with ${this.builderSteps.length} steps`, type: 'success', position: 'top-right', closeTimeout: 3000 });
        } catch (e) {
            Swal.fire('Error', 'Failed to save playbook', 'error');
        }
    },

    async executePlaybook(id) {
        const pb = this.playbooks.find(p => p.id === id);
        const steps = pb ? (typeof pb.steps === 'string' ? JSON.parse(pb.steps) : pb.steps) : [];

        const result = await Swal.fire({
            title: `Execute: ${pb ? this.escapeHtml(pb.name) : 'Playbook'}?`,
            html: `<p style="color:#94a3b8;">${steps.length} steps will run sequentially</p>
                   <div style="text-align:left;margin-top:12px;font-size:12px;color:#64748b;">
                       ${steps.map((s, i) => {
                           const action = this.availableActions.find(a => a.id === s.action);
                           return `<div style="padding:2px 0;"><span style="color:#6b7280;">${i+1}.</span> ${action ? action.name : s.action}</div>`;
                       }).join('')}
                   </div>`,
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: '<i class="fas fa-play mr-1"></i> Execute',
            confirmButtonColor: '#16a34a',
        });

        if (!result.isConfirmed) return;

        try {
            Swal.fire({
                title: 'Executing Playbook...',
                html: '<p style="color:#94a3b8;">Running steps...</p>',
                allowOutsideClick: false,
                showConfirmButton: false,
                didOpen: () => Swal.showLoading(),
            });

            const resp = await $.ajax({
                url: `/api/playbooks/${id}/execute`,
                method: 'POST',
                contentType: 'application/json',
                data: '{}',
            });

            const log = resp.execution_log || [];
            const successCount = log.filter(l => l.status === 'success').length;
            const errorCount = log.filter(l => l.status === 'error').length;
            const skippedCount = log.filter(l => l.status === 'skipped').length;

            Swal.fire({
                title: errorCount > 0 ? 'Completed with Errors' : 'Execution Successful',
                html: `
                    <div style="text-align:left;">
                        <div style="display:flex;gap:16px;margin-bottom:16px;text-align:center;">
                            <div style="flex:1;background:#064e3b;border-radius:8px;padding:12px;">
                                <div style="font-size:24px;font-weight:bold;color:#4ade80;">${successCount}</div>
                                <div style="font-size:10px;color:#6ee7b7;">Success</div>
                            </div>
                            <div style="flex:1;background:#7f1d1d;border-radius:8px;padding:12px;">
                                <div style="font-size:24px;font-weight:bold;color:#f87171;">${errorCount}</div>
                                <div style="font-size:10px;color:#fca5a5;">Errors</div>
                            </div>
                            <div style="flex:1;background:#1e293b;border-radius:8px;padding:12px;">
                                <div style="font-size:24px;font-weight:bold;color:#94a3b8;">${skippedCount}</div>
                                <div style="font-size:10px;color:#94a3b8;">Skipped</div>
                            </div>
                        </div>
                        <div style="max-height:300px;overflow:auto;">
                            ${log.map((l, i) => {
                                const statusIcon = l.status === 'success' ? '✓' : l.status === 'error' ? '✗' : '⊘';
                                const borderColor = l.status === 'success' ? '#16a34a' : l.status === 'error' ? '#dc2626' : '#6b7280';
                                return `
                                <div style="margin-bottom:8px;padding:10px;background:#1e293b;border-radius:6px;border-left:3px solid ${borderColor};">
                                    <div style="display:flex;justify-content:space-between;">
                                        <span style="font-size:12px;color:#e2e8f0;font-weight:500;">${statusIcon} Step ${i + 1}: ${l.action}</span>
                                        <span style="font-size:10px;color:#64748b;">${l.timestamp ? new Date(l.timestamp).toLocaleTimeString() : ''}</span>
                                    </div>
                                    <div style="font-size:11px;color:${l.status === 'success' ? '#4ade80' : '#f87171'};margin-top:4px;word-break:break-all;">${(l.output || '').substring(0, 300)}</div>
                                </div>`;
                            }).join('')}
                        </div>
                    </div>
                `,
                icon: errorCount > 0 ? 'warning' : 'success',
                width: '650px',
            });

            this.loadPlaybooks();
        } catch (e) {
            Swal.fire('Error', 'Playbook execution failed', 'error');
        }
    },

    editPlaybook(id) {
        const pb = this.playbooks.find(p => p.id === id);
        if (pb) this.showPlaybookBuilder(pb);
    },

    async duplicatePlaybook(id) {
        const pb = this.playbooks.find(p => p.id === id);
        if (!pb) return;
        try {
            const steps = typeof pb.steps === 'string' ? JSON.parse(pb.steps) : (pb.steps || []);
            await $.ajax({
                url: '/api/playbooks',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({
                    name: `${pb.name} (Copy)`,
                    description: pb.description || '',
                    steps: steps,
                }),
            });
            this.loadPlaybooks();
            GrowlNotification.notify({ title: 'Duplicated', description: `Playbook copied`, type: 'success', position: 'top-right', closeTimeout: 3000 });
        } catch (e) {
            Swal.fire('Error', 'Failed to duplicate playbook', 'error');
        }
    },

    viewLog(id) {
        const pb = this.playbooks.find(p => p.id === id);
        if (!pb) return;
        const log = typeof pb.execution_log === 'string' ? JSON.parse(pb.execution_log) : (pb.execution_log || []);
        if (log.length === 0) {
            Swal.fire({
                title: 'No Execution Log',
                text: 'This playbook has not been executed yet.',
                icon: 'info',
                confirmButtonText: 'Run Now',
                showCancelButton: true,
                cancelButtonText: 'Close',
            }).then(result => {
                if (result.isConfirmed) this.executePlaybook(id);
            });
            return;
        }
        Swal.fire({
            title: `Log: ${this.escapeHtml(pb.name)}`,
            html: `
                <div style="text-align:left;font-size:12px;color:#94a3b8;margin-bottom:8px;">
                    Last run: ${pb.last_run || 'Unknown'} · Runs: ${pb.run_count || 0}
                </div>
                <pre style="text-align:left;max-height:400px;overflow:auto;background:#1e293b;color:#e2e8f0;padding:16px;border-radius:8px;font-size:11px;white-space:pre-wrap;">${JSON.stringify(log, null, 2)}</pre>`,
            width: '700px',
        });
    },

    async deletePlaybook(id) {
        const result = await Swal.fire({
            title: 'Delete Playbook?',
            text: 'This action cannot be undone.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc2626',
            confirmButtonText: '<i class="fas fa-trash mr-1"></i> Delete',
        });
        if (result.isConfirmed) {
            await $.ajax({ url: `/api/playbooks/${id}`, method: 'DELETE' });
            this.loadPlaybooks();
            GrowlNotification.notify({ title: 'Deleted', description: 'Playbook deleted', type: 'info', position: 'top-right', closeTimeout: 3000 });
        }
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
    },
};
