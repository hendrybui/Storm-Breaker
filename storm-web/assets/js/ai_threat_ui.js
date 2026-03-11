/**
 * Storm-Breaker AI Threat Analyzer UI
 * Neural threat detection, behavioral analysis, anomaly detection,
 * predictive modeling, and automated incident response
 */
const AIThreatUI = {
    initialized: false,

    init() {
        if (!this.initialized) {
            this.bindEvents();
        }
        this.initialized = true;
        this.render();
    },

    bindEvents() {
        $(document).on('click', '#btn-ai-analyze-payload', () => this.analyzePayload());
        $(document).on('click', '#btn-ai-behavioral', () => this.behavioralAnalysis());
        $(document).on('click', '#btn-ai-anomaly', () => this.detectAnomalies());
        $(document).on('click', '#btn-ai-predict', () => this.predictiveModel());
        $(document).on('click', '#btn-ai-response-plan', () => this.generateResponsePlan());
        $(document).on('click', '#btn-ai-landscape', () => this.threatLandscape());
        $(document).on('click', '.ai-sub-tab', function() {
            const t = $(this).data('target');
            $('.ai-sub-tab').removeClass('bg-violet-600 text-white').addClass('bg-slate-700 text-slate-300');
            $(this).removeClass('bg-slate-700 text-slate-300').addClass('bg-violet-600 text-white');
            $('.ai-sub-panel').addClass('hidden');
            $(`#${t}`).removeClass('hidden');
        });
    },

    render() {
        const c = $('#ai-threat-dashboard');
        if (!c.length) return;
        c.html(`
            <div class="space-y-4">
                <div class="flex flex-wrap gap-1.5 p-1.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
                    <button class="ai-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-violet-600 text-white" data-target="ai-panel-analyze"><i class="fas fa-brain mr-1"></i>Payload Analysis</button>
                    <button class="ai-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="ai-panel-behavior"><i class="fas fa-user-secret mr-1"></i>Behavioral</button>
                    <button class="ai-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="ai-panel-anomaly"><i class="fas fa-wave-square mr-1"></i>Anomaly Detection</button>
                    <button class="ai-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="ai-panel-predict"><i class="fas fa-chart-line mr-1"></i>Predictive</button>
                    <button class="ai-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="ai-panel-response"><i class="fas fa-shield-alt mr-1"></i>Response Plans</button>
                    <button class="ai-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="ai-panel-landscape"><i class="fas fa-globe mr-1"></i>Threat Landscape</button>
                </div>

                <!-- Payload Analysis -->
                <div id="ai-panel-analyze" class="ai-sub-panel">
                    <div class="bg-slate-800/80 rounded-xl border border-violet-500/30 p-4">
                        <h3 class="text-violet-400 font-bold mb-3"><i class="fas fa-brain mr-2"></i>AI Payload Analysis</h3>
                        <p class="text-slate-400 text-xs mb-3">Analyze payloads for threats using neural pattern matching, entropy analysis, and encoding detection.</p>
                        <textarea id="ai-payload-input" rows="5" class="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-green-300 text-sm font-mono" placeholder="Paste payload, URL, command, or suspicious data here..."></textarea>
                        <button id="btn-ai-analyze-payload" class="mt-2 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-microscope mr-1"></i>Analyze with AI</button>
                        <div id="ai-analyze-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Behavioral Analysis -->
                <div id="ai-panel-behavior" class="ai-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-violet-500/30 p-4">
                        <h3 class="text-violet-400 font-bold mb-3"><i class="fas fa-user-secret mr-2"></i>Behavioral Profiling</h3>
                        <p class="text-slate-400 text-xs mb-3">Profile IP addresses using behavioral analysis, anomaly detection, and threat indicators.</p>
                        <div class="flex gap-2">
                            <input id="ai-ip-input" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Enter IP address (e.g. 192.168.1.100)">
                            <button id="btn-ai-behavioral" class="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-user-shield mr-1"></i>Profile</button>
                        </div>
                        <div id="ai-behavioral-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Anomaly Detection -->
                <div id="ai-panel-anomaly" class="ai-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-violet-500/30 p-4">
                        <h3 class="text-violet-400 font-bold mb-3"><i class="fas fa-wave-square mr-2"></i>Multi-Model Anomaly Detection</h3>
                        <p class="text-slate-400 text-xs mb-3">Run 8 simultaneous anomaly detection models across traffic, geo, protocol, entropy, and session data.</p>
                        <button id="btn-ai-anomaly" class="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-satellite-dish mr-1"></i>Detect Anomalies</button>
                        <div id="ai-anomaly-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Predictive Model -->
                <div id="ai-panel-predict" class="ai-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-violet-500/30 p-4">
                        <h3 class="text-violet-400 font-bold mb-3"><i class="fas fa-chart-line mr-2"></i>Predictive Attack Modeling</h3>
                        <p class="text-slate-400 text-xs mb-3">AI predicts likely attack chains with stages, probabilities, and recommended countermeasures.</p>
                        <button id="btn-ai-predict" class="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-crystal-ball mr-1"></i>Generate Predictions</button>
                        <div id="ai-predict-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Response Plans -->
                <div id="ai-panel-response" class="ai-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-violet-500/30 p-4">
                        <h3 class="text-violet-400 font-bold mb-3"><i class="fas fa-shield-alt mr-2"></i>Automated Incident Response</h3>
                        <p class="text-slate-400 text-xs mb-3">Generate actionable incident response plans with automated and manual steps.</p>
                        <div class="grid grid-cols-2 gap-2 mb-3">
                            <select id="ai-threat-type" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="malware">Malware Incident</option>
                                <option value="data_breach">Data Breach</option>
                                <option value="ransomware">Ransomware</option>
                                <option value="intrusion">Network Intrusion</option>
                            </select>
                            <select id="ai-severity" class="bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="critical">Critical</option>
                                <option value="high">High</option>
                                <option value="medium">Medium</option>
                                <option value="low">Low</option>
                            </select>
                        </div>
                        <button id="btn-ai-response-plan" class="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-clipboard-list mr-1"></i>Generate Plan</button>
                        <div id="ai-response-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Threat Landscape -->
                <div id="ai-panel-landscape" class="ai-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-violet-500/30 p-4">
                        <h3 class="text-violet-400 font-bold mb-3"><i class="fas fa-globe mr-2"></i>Global Threat Landscape</h3>
                        <p class="text-slate-400 text-xs mb-3">Real-time overview of global threat landscape, trending attacks, APT groups, and targeted sectors.</p>
                        <button id="btn-ai-landscape" class="px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-earth-americas mr-1"></i>Load Landscape</button>
                        <div id="ai-landscape-result" class="mt-3"></div>
                    </div>
                </div>
            </div>
        `);
    },

    analyzePayload() {
        const payload = $('#ai-payload-input').val();
        if (!payload) return GrowlNotification.notify({title:'Error',description:'Enter payload to analyze',type:'error',position:'top-right',closeTimeout:3000});
        $('#ai-analyze-result').html('<div class="text-violet-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Neural analysis in progress...</div>');
        $.post('/api/ai-threat/analyze', {payload}, (d) => {
            if (!d.success) return $('#ai-analyze-result').html(`<div class="text-red-400">${d.error}</div>`);
            const r = d.result;
            const sevColor = {critical:'red',high:'orange',medium:'yellow',low:'green'}[r.risk_level] || 'slate';
            let html = `<div class="space-y-3">
                <div class="flex items-center gap-3">
                    <span class="px-3 py-1 rounded-full text-xs font-bold bg-${sevColor}-500/20 text-${sevColor}-400 border border-${sevColor}-500/30">${r.risk_level.toUpperCase()} RISK</span>
                    <span class="text-white font-bold">Score: ${r.risk_score}/100</span>
                    <span class="text-slate-400 text-xs">Entropy: ${r.entropy?.toFixed(3) || 'N/A'}</span>
                </div>`;
            if (r.threats_detected?.length) {
                html += `<div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2"><i class="fas fa-exclamation-triangle mr-1"></i>Threats Detected (${r.threats_detected.length})</h4><div class="space-y-1">`;
                r.threats_detected.forEach(t => {
                    html += `<div class="flex justify-between items-center text-xs"><span class="text-white">${t.name}</span><span class="text-red-300">${t.mitre_id || ''}</span><span class="text-yellow-400">Conf: ${t.confidence}%</span></div>`;
                });
                html += `</div></div>`;
            }
            if (r.encodings_detected?.length) {
                html += `<div class="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2">Encodings Detected</h4><div class="flex flex-wrap gap-1">`;
                r.encodings_detected.forEach(e => { html += `<span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs">${e}</span>`; });
                html += `</div></div>`;
            }
            if (r.kill_chain_stage) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><span class="text-xs text-slate-400">Kill Chain Stage:</span> <span class="text-violet-400 font-bold text-sm">${r.kill_chain_stage}</span></div>`;
            }
            if (r.recommendations?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-blue-400 text-xs font-bold mb-1">Recommendations</h4><ul class="list-disc list-inside text-xs text-slate-300 space-y-0.5">`;
                r.recommendations.forEach(rec => { html += `<li>${rec}</li>`; });
                html += `</ul></div>`;
            }
            html += `</div>`;
            $('#ai-analyze-result').html(html);
        }).fail(() => $('#ai-analyze-result').html('<div class="text-red-400">Analysis failed</div>'));
    },

    behavioralAnalysis() {
        const ip = $('#ai-ip-input').val() || '192.168.1.' + Math.floor(Math.random()*254+1);
        $('#ai-ip-input').val(ip);
        $('#ai-behavioral-result').html('<div class="text-violet-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Profiling...</div>');
        $.get('/api/ai-threat/behavioral', {ip}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-3 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Profile</div><div class="text-violet-400 font-bold text-sm">${r.matched_profile}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Risk</div><div class="text-orange-400 font-bold text-sm">${r.risk_level}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-3 text-center"><div class="text-xs text-slate-400">Score</div><div class="text-white font-bold text-sm">${r.risk_score}/100</div></div>
                </div>`;
            if (r.anomalies?.length) {
                html += `<div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Anomalies (${r.anomalies.length})</h4><div class="space-y-1">`;
                r.anomalies.forEach(a => { html += `<div class="text-xs text-slate-300">• ${a}</div>`; });
                html += `</div></div>`;
            }
            if (r.threat_indicators) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2">Threat Indicators</h4><div class="grid grid-cols-2 gap-1 text-xs">`;
                Object.entries(r.threat_indicators).forEach(([k,v]) => {
                    html += `<div class="flex justify-between"><span class="text-slate-400">${k.replace(/_/g,' ')}</span><span class="${v ? 'text-red-400' : 'text-green-400'}">${v ? 'YES' : 'NO'}</span></div>`;
                });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#ai-behavioral-result').html(html);
        });
    },

    detectAnomalies() {
        $('#ai-anomaly-result').html('<div class="text-violet-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Running 8 detection models...</div>');
        $.get('/api/ai-threat/anomalies', (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3"><div class="grid grid-cols-2 gap-2">`;
            if (r.anomalies) {
                r.anomalies.forEach(a => {
                    const color = a.status === 'anomaly_detected' ? 'red' : a.status === 'warning' ? 'yellow' : 'green';
                    html += `<div class="bg-${color}-900/20 border border-${color}-500/30 rounded-lg p-3">
                        <div class="flex justify-between items-center mb-1"><span class="text-${color}-400 font-bold text-xs">${a.model?.replace(/_/g,' ').toUpperCase() || 'Model'}</span><span class="text-xs text-${color}-300">${a.status?.replace(/_/g,' ')}</span></div>
                        <div class="text-slate-300 text-xs">${a.details || ''}</div>
                        <div class="mt-1 text-xs text-slate-500">Confidence: ${a.confidence || 0}%</div>
                    </div>`;
                });
            }
            html += `</div></div>`;
            $('#ai-anomaly-result').html(html);
        });
    },

    predictiveModel() {
        $('#ai-predict-result').html('<div class="text-violet-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Generating predictions...</div>');
        $.get('/api/ai-threat/predict', (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">`;
            if (r.predictions) {
                r.predictions.forEach((p, i) => {
                    html += `<div class="bg-slate-700/50 border border-violet-500/20 rounded-lg p-3">
                        <div class="flex justify-between items-center mb-2"><span class="text-violet-400 font-bold text-sm">${p.attack_chain || 'Chain '+(i+1)}</span><span class="text-yellow-400 text-xs">Prob: ${p.probability || 0}%</span></div>
                        <div class="space-y-1">`;
                    if (p.stages) {
                        p.stages.forEach((s, j) => {
                            html += `<div class="flex items-center gap-2 text-xs"><span class="w-5 h-5 rounded-full bg-violet-600 text-white flex items-center justify-center text-[10px]">${j+1}</span><span class="text-slate-300">${s}</span></div>`;
                        });
                    }
                    if (p.countermeasures?.length) {
                        html += `<div class="mt-2 pt-2 border-t border-slate-600"><span class="text-green-400 text-xs font-bold">Countermeasures:</span>`;
                        p.countermeasures.forEach(cm => { html += `<div class="text-xs text-slate-400 ml-2">• ${cm}</div>`; });
                        html += `</div>`;
                    }
                    html += `</div></div>`;
                });
            }
            html += `</div>`;
            $('#ai-predict-result').html(html);
        });
    },

    generateResponsePlan() {
        const type = $('#ai-threat-type').val();
        const severity = $('#ai-severity').val();
        $('#ai-response-result').html('<div class="text-violet-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Building response plan...</div>');
        $.get('/api/ai-threat/response-plan', {type, severity}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="bg-violet-900/20 border border-violet-500/30 rounded-lg p-3"><h4 class="text-violet-400 font-bold text-sm">${r.plan_name || 'Response Plan'}</h4><p class="text-slate-400 text-xs mt-1">Priority: ${r.priority || 'N/A'} | Estimated Time: ${r.estimated_time || 'N/A'}</p></div>`;
            if (r.automated_steps?.length) {
                html += `<div class="bg-green-900/20 border border-green-500/30 rounded-lg p-3"><h4 class="text-green-400 text-xs font-bold mb-2"><i class="fas fa-robot mr-1"></i>Automated Steps</h4><div class="space-y-1">`;
                r.automated_steps.forEach((s, i) => { html += `<div class="text-xs text-slate-300">${i+1}. ${s}</div>`; });
                html += `</div></div>`;
            }
            if (r.manual_steps?.length) {
                html += `<div class="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3"><h4 class="text-blue-400 text-xs font-bold mb-2"><i class="fas fa-user mr-1"></i>Manual Steps</h4><div class="space-y-1">`;
                r.manual_steps.forEach((s, i) => { html += `<div class="text-xs text-slate-300">${i+1}. ${s}</div>`; });
                html += `</div></div>`;
            }
            if (r.commands?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2"><i class="fas fa-terminal mr-1"></i>Commands</h4>`;
                r.commands.forEach(cmd => { html += `<div class="bg-slate-900 rounded p-2 mb-1 text-xs font-mono text-green-300">${cmd}</div>`; });
                html += `</div>`;
            }
            html += `</div>`;
            $('#ai-response-result').html(html);
        });
    },

    threatLandscape() {
        $('#ai-landscape-result').html('<div class="text-violet-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Loading threat landscape...</div>');
        $.get('/api/ai-threat/landscape', (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3 text-center"><span class="text-xs text-slate-400">Global Threat Index</span><div class="text-3xl font-bold text-red-400">${r.global_threat_index || 0}<span class="text-sm text-slate-500">/100</span></div></div>
                <div class="grid grid-cols-2 gap-2">`;
            if (r.trending_threats) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-orange-400 text-xs font-bold mb-2">Trending Threats</h4><div class="space-y-1">`;
                r.trending_threats.forEach(t => { html += `<div class="text-xs text-slate-300">• ${t.name || t} <span class="text-orange-400">(${t.trend || '↑'})</span></div>`; });
                html += `</div></div>`;
            }
            if (r.apt_groups) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Active APT Groups</h4><div class="space-y-1">`;
                r.apt_groups.forEach(g => { html += `<div class="text-xs text-slate-300">• <span class="text-red-300">${g.name || g}</span> <span class="text-slate-500">${g.origin || ''}</span></div>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            if (r.targeted_sectors) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-violet-400 text-xs font-bold mb-2">Targeted Sectors</h4><div class="flex flex-wrap gap-1">`;
                r.targeted_sectors.forEach(s => { html += `<span class="px-2 py-0.5 bg-violet-500/20 text-violet-300 rounded text-xs">${s}</span>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#ai-landscape-result').html(html);
        });
    }
};
