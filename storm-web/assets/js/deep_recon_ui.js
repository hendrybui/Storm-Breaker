/**
 * Storm-Breaker Deep Recon OSINT UI
 * Domain reconnaissance, social profiling, dark web scanning,
 * email intelligence, infrastructure mapping, and data correlation
 */
const DeepReconUI = {
    initialized: false,

    init() {
        if (!this.initialized) {
            this.bindEvents();
        }
        this.initialized = true;
        this.render();
    },

    bindEvents() {
        $(document).on('click', '#btn-dr-domain', () => this.domainRecon());
        $(document).on('click', '#btn-dr-social', () => this.socialSearch());
        $(document).on('click', '#btn-dr-darkweb', () => this.darkWebScan());
        $(document).on('click', '#btn-dr-email', () => this.emailIntel());
        $(document).on('click', '#btn-dr-infra', () => this.infraMap());
        $(document).on('click', '#btn-dr-correlate', () => this.correlateData());
        $(document).on('click', '.dr-sub-tab', function() {
            const t = $(this).data('target');
            $('.dr-sub-tab').removeClass('bg-emerald-600 text-white').addClass('bg-slate-700 text-slate-300');
            $(this).removeClass('bg-slate-700 text-slate-300').addClass('bg-emerald-600 text-white');
            $('.dr-sub-panel').addClass('hidden');
            $(`#${t}`).removeClass('hidden');
        });
    },

    render() {
        const c = $('#deeprecon-dashboard');
        if (!c.length) return;
        c.html(`
            <div class="space-y-4">
                <div class="flex flex-wrap gap-1.5 p-1.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
                    <button class="dr-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white" data-target="dr-panel-domain"><i class="fas fa-globe mr-1"></i>Domain Recon</button>
                    <button class="dr-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="dr-panel-social"><i class="fas fa-users mr-1"></i>Social Profiling</button>
                    <button class="dr-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="dr-panel-darkweb"><i class="fas fa-user-ninja mr-1"></i>Dark Web</button>
                    <button class="dr-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="dr-panel-email"><i class="fas fa-envelope mr-1"></i>Email Intel</button>
                    <button class="dr-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="dr-panel-infra"><i class="fas fa-network-wired mr-1"></i>Infrastructure</button>
                    <button class="dr-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="dr-panel-correlate"><i class="fas fa-project-diagram mr-1"></i>Correlator</button>
                </div>

                <!-- Domain Recon -->
                <div id="dr-panel-domain" class="dr-sub-panel">
                    <div class="bg-slate-800/80 rounded-xl border border-emerald-500/30 p-4">
                        <h3 class="text-emerald-400 font-bold mb-3"><i class="fas fa-globe mr-2"></i>Domain Reconnaissance</h3>
                        <p class="text-slate-400 text-xs mb-3">Full domain recon — DNS records, subdomains, WHOIS, SSL/TLS, tech stack, security headers, and email security.</p>
                        <div class="flex gap-2">
                            <input id="dr-domain-input" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Enter domain (e.g. example.com)">
                            <button id="btn-dr-domain" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-search mr-1"></i>Recon</button>
                        </div>
                        <div id="dr-domain-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Social Profiling -->
                <div id="dr-panel-social" class="dr-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-emerald-500/30 p-4">
                        <h3 class="text-emerald-400 font-bold mb-3"><i class="fas fa-users mr-2"></i>Social Media Profiling</h3>
                        <p class="text-slate-400 text-xs mb-3">Search for a username across 20+ social platforms, assess digital footprint, and identify exposure risks.</p>
                        <div class="flex gap-2">
                            <input id="dr-social-input" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Enter username">
                            <button id="btn-dr-social" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-fingerprint mr-1"></i>Search</button>
                        </div>
                        <div id="dr-social-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Dark Web Scanner -->
                <div id="dr-panel-darkweb" class="dr-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-emerald-500/30 p-4">
                        <h3 class="text-emerald-400 font-bold mb-3"><i class="fas fa-user-ninja mr-2"></i>Dark Web Scanner</h3>
                        <p class="text-slate-400 text-xs mb-3">Scan dark web markets, forums, breach databases, and paste sites for mentions of your target.</p>
                        <div class="flex gap-2">
                            <input id="dr-darkweb-input" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Search term (domain, email, org name)">
                            <button id="btn-dr-darkweb" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-spider mr-1"></i>Scan</button>
                        </div>
                        <div id="dr-darkweb-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Email Intelligence -->
                <div id="dr-panel-email" class="dr-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-emerald-500/30 p-4">
                        <h3 class="text-emerald-400 font-bold mb-3"><i class="fas fa-envelope mr-2"></i>Email Intelligence</h3>
                        <p class="text-slate-400 text-xs mb-3">Comprehensive email OSINT — breach check, reputation, linked profiles, deliverability, and risk assessment.</p>
                        <div class="flex gap-2">
                            <input id="dr-email-input" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Enter email address">
                            <button id="btn-dr-email" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-at mr-1"></i>Investigate</button>
                        </div>
                        <div id="dr-email-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Infrastructure Mapping -->
                <div id="dr-panel-infra" class="dr-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-emerald-500/30 p-4">
                        <h3 class="text-emerald-400 font-bold mb-3"><i class="fas fa-network-wired mr-2"></i>Infrastructure Mapping</h3>
                        <p class="text-slate-400 text-xs mb-3">Map cloud infrastructure, ASN info, network topology, and attack surface of an organization.</p>
                        <div class="flex gap-2">
                            <input id="dr-infra-input" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm" placeholder="Organization or domain name">
                            <button id="btn-dr-infra" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-sitemap mr-1"></i>Map</button>
                        </div>
                        <div id="dr-infra-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Data Correlator -->
                <div id="dr-panel-correlate" class="dr-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-emerald-500/30 p-4">
                        <h3 class="text-emerald-400 font-bold mb-3"><i class="fas fa-project-diagram mr-2"></i>Intelligence Correlator</h3>
                        <p class="text-slate-400 text-xs mb-3">Correlate multiple entities (emails, domains, usernames) to discover relationships and build intelligence graphs.</p>
                        <textarea id="dr-correlate-input" rows="3" class="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-green-300 text-sm font-mono mb-2" placeholder="Enter entities, one per line (emails, domains, usernames)..."></textarea>
                        <button id="btn-dr-correlate" class="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-share-alt mr-1"></i>Correlate</button>
                        <div id="dr-correlate-result" class="mt-3"></div>
                    </div>
                </div>
            </div>
        `);
    },

    domainRecon() {
        const domain = $('#dr-domain-input').val();
        if (!domain) return GrowlNotification.notify({title:'Error',description:'Enter a domain',type:'error',position:'top-right',closeTimeout:3000});
        $('#dr-domain-result').html('<div class="text-emerald-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Performing deep recon...</div>');
        $.post('/api/deeprecon/domain', {domain}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-3 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Security Score</div><div class="text-xl font-bold text-${r.security_score>70?'green':r.security_score>40?'yellow':'red'}-400">${r.security_score}%</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Subdomains</div><div class="text-xl font-bold text-cyan-400">${r.subdomains?.length||0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">DNS Records</div><div class="text-xl font-bold text-emerald-400">${r.dns_records?.length||0}</div></div>
                </div>`;
            // WHOIS
            if (r.whois) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-emerald-400 text-xs font-bold mb-2">WHOIS</h4><div class="grid grid-cols-2 gap-1 text-xs">`;
                Object.entries(r.whois).forEach(([k,v]) => {
                    if (typeof v !== 'object') html += `<div><span class="text-slate-400">${k}:</span> <span class="text-white">${v}</span></div>`;
                });
                html += `</div></div>`;
            }
            // SSL
            if (r.ssl) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">SSL/TLS</h4><div class="grid grid-cols-2 gap-1 text-xs">`;
                Object.entries(r.ssl).forEach(([k,v]) => {
                    if (typeof v === 'boolean') html += `<div><span class="text-slate-400">${k}:</span> <span class="${v?'text-green-400':'text-red-400'}">${v?'Yes':'No'}</span></div>`;
                    else html += `<div><span class="text-slate-400">${k}:</span> <span class="text-white">${v}</span></div>`;
                });
                html += `</div></div>`;
            }
            // Tech Stack
            if (r.technologies?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2">Technology Stack</h4><div class="flex flex-wrap gap-1">`;
                r.technologies.forEach(t => { html += `<span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs">${t}</span>`; });
                html += `</div></div>`;
            }
            // DNS
            if (r.dns_records?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-emerald-400 text-xs font-bold mb-2">DNS Records</h4><div class="space-y-1">`;
                r.dns_records.forEach(d => { html += `<div class="flex gap-2 text-xs"><span class="text-emerald-400 font-bold w-12">${d.type}</span><span class="text-white flex-1 font-mono truncate">${d.value}</span><span class="text-slate-500">TTL: ${d.ttl}</span></div>`; });
                html += `</div></div>`;
            }
            // Security Headers
            if (r.security_headers) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Security Headers</h4><div class="grid grid-cols-2 gap-1 text-xs">`;
                Object.entries(r.security_headers).forEach(([k,v]) => { html += `<div class="flex justify-between"><span class="text-slate-400">${k}</span><span class="${v?'text-green-400':'text-red-400'}">${v?'✓':'✗'}</span></div>`; });
                html += `</div></div>`;
            }
            // Subdomains
            if (r.subdomains?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">Subdomains (${r.subdomains.length})</h4><div class="flex flex-wrap gap-1">`;
                r.subdomains.forEach(s => { html += `<span class="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 rounded text-xs font-mono">${s}</span>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#dr-domain-result').html(html);
        });
    },

    socialSearch() {
        const username = $('#dr-social-input').val();
        if (!username) return GrowlNotification.notify({title:'Error',description:'Enter a username',type:'error',position:'top-right',closeTimeout:3000});
        $('#dr-social-result').html('<div class="text-emerald-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Searching platforms...</div>');
        $.post('/api/deeprecon/social', {username}, (d) => {
            if (!d.success) return;
            const r = d.result;
            const expColor = r.risk_profile?.exposure_level === 'high' ? 'red' : r.risk_profile?.exposure_level === 'medium' ? 'yellow' : 'green';
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-3 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Platforms Found</div><div class="text-xl font-bold text-emerald-400">${r.profiles_found}/${r.platforms_checked}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Footprint Score</div><div class="text-xl font-bold text-cyan-400">${r.digital_footprint_score}%</div></div>
                    <div class="bg-${expColor}-900/20 border border-${expColor}-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Exposure</div><div class="text-xl font-bold text-${expColor}-400">${(r.risk_profile?.exposure_level||'').toUpperCase()}</div></div>
                </div>`;
            if (r.results?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-emerald-400 text-xs font-bold mb-2">Platform Results</h4><div class="grid grid-cols-2 gap-1">`;
                r.results.forEach(p => {
                    if (p.found) {
                        html += `<div class="bg-green-900/10 border border-green-500/20 rounded p-2 text-xs"><div class="flex justify-between"><span class="text-green-400 font-bold">${p.platform}</span><span class="text-green-300">${p.confidence}%</span></div><div class="text-slate-400 truncate font-mono mt-0.5">${p.url||''}</div><div class="text-slate-500 mt-0.5">${p.followers||0} followers | ${p.posts||0} posts</div></div>`;
                    } else {
                        html += `<div class="bg-slate-800/50 rounded p-2 text-xs"><span class="text-slate-500">${p.platform}</span> <span class="text-red-400">Not Found</span></div>`;
                    }
                });
                html += `</div></div>`;
            }
            if (r.possible_emails?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2">Possible Email Addresses</h4><div class="flex flex-wrap gap-1">`;
                r.possible_emails.forEach(e => { html += `<span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded text-xs font-mono">${e}</span>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#dr-social-result').html(html);
        });
    },

    darkWebScan() {
        const query = $('#dr-darkweb-input').val();
        if (!query) return GrowlNotification.notify({title:'Error',description:'Enter search term',type:'error',position:'top-right',closeTimeout:3000});
        $('#dr-darkweb-result').html('<div class="text-emerald-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Scanning dark web...</div>');
        $.post('/api/deeprecon/darkweb', {query}, (d) => {
            if (!d.success) return;
            const r = d.result;
            const riskColor = r.risk_level === 'critical' ? 'red' : r.risk_level === 'high' ? 'orange' : 'green';
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-3 gap-2">
                    <div class="bg-${riskColor}-900/20 border border-${riskColor}-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Risk Level</div><div class="text-xl font-bold text-${riskColor}-400">${(r.risk_level||'').toUpperCase()}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Findings</div><div class="text-xl font-bold text-red-400">${r.findings?.length||0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Breaches</div><div class="text-xl font-bold text-orange-400">${r.breaches?.length||0}</div></div>
                </div>`;
            if (r.findings?.length) {
                html += `<div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Dark Web Findings</h4><div class="space-y-1">`;
                r.findings.forEach(f => {
                    const c = f.severity === 'critical' ? 'red' : f.severity === 'high' ? 'orange' : 'yellow';
                    html += `<div class="bg-${c}-900/10 border border-${c}-500/20 rounded p-2 text-xs"><div class="flex justify-between"><span class="text-${c}-400 font-bold">${f.source}</span><span class="text-slate-400">${f.category.replace(/_/g,' ')}</span><span class="text-slate-500">${f.date_found}</span></div><div class="text-slate-300 mt-1">${f.detail}</div></div>`;
                });
                html += `</div></div>`;
            }
            if (r.breaches?.length) {
                html += `<div class="bg-orange-900/20 border border-orange-500/30 rounded-lg p-3"><h4 class="text-orange-400 text-xs font-bold mb-2">Breach Database Hits</h4><div class="space-y-1">`;
                r.breaches.forEach(b => { html += `<div class="bg-slate-800/50 rounded p-2 text-xs"><div class="flex justify-between"><span class="text-orange-300 font-bold">${b.source}</span><span class="text-slate-400">${b.date}</span><span class="text-red-400">${(b.records_exposed||0).toLocaleString()} records</span></div><div class="flex flex-wrap gap-1 mt-1">${(b.data_types||[]).map(t=>`<span class="px-1.5 py-0.5 bg-orange-500/20 text-orange-300 rounded text-[10px]">${t}</span>`).join('')}</div></div>`; });
                html += `</div></div>`;
            }
            if (r.recommendations?.length) {
                html += `<div class="bg-green-900/20 border border-green-500/30 rounded-lg p-3"><h4 class="text-green-400 text-xs font-bold mb-1">Recommendations</h4><ul class="list-disc list-inside text-xs text-slate-300">`;
                r.recommendations.forEach(rec => { html += `<li>${rec}</li>`; });
                html += `</ul></div>`;
            }
            html += `</div>`;
            $('#dr-darkweb-result').html(html);
        });
    },

    emailIntel() {
        const email = $('#dr-email-input').val();
        if (!email) return GrowlNotification.notify({title:'Error',description:'Enter an email',type:'error',position:'top-right',closeTimeout:3000});
        $('#dr-email-result').html('<div class="text-emerald-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Investigating email...</div>');
        $.post('/api/deeprecon/email', {email}, (d) => {
            if (!d.success) return;
            const r = d.result;
            const riskColor = r.risk_assessment === 'high' ? 'red' : r.risk_assessment === 'medium' ? 'yellow' : 'green';
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-4 gap-2">
                    <div class="bg-${riskColor}-900/20 border border-${riskColor}-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Risk</div><div class="text-sm font-bold text-${riskColor}-400">${(r.risk_assessment||'').toUpperCase()}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Provider</div><div class="text-sm font-bold text-cyan-400">${r.provider||'Unknown'}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Breaches</div><div class="text-sm font-bold text-red-400">${r.breaches?.count||0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Deliverable</div><div class="text-sm font-bold ${r.deliverable?'text-green-400':'text-red-400'}">${r.deliverable?'YES':'NO'}</div></div>
                </div>`;
            // Flags
            html += `<div class="flex flex-wrap gap-2 text-xs">`;
            if (r.disposable) html += `<span class="px-2 py-0.5 bg-red-500/20 text-red-300 rounded">⚠ Disposable</span>`;
            if (r.role_account) html += `<span class="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 rounded">Role Account</span>`;
            if (r.reputation?.blacklisted) html += `<span class="px-2 py-0.5 bg-red-500/20 text-red-300 rounded">Blacklisted</span>`;
            html += `<span class="px-2 py-0.5 bg-slate-500/20 text-slate-300 rounded">First seen: ${r.first_seen||'Unknown'}</span></div>`;
            // Reputation
            if (r.reputation) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2">Reputation</h4><div class="grid grid-cols-2 gap-1 text-xs">
                    <div><span class="text-slate-400">Score:</span> <span class="text-white">${r.reputation.score}/100</span></div>
                    <div><span class="text-slate-400">Spam Reports:</span> <span class="text-white">${r.reputation.spam_reports}</span></div>
                    <div><span class="text-slate-400">Fraud Score:</span> <span class="text-white">${r.reputation.fraud_score}/100</span></div>
                </div></div>`;
            }
            // Breaches
            if (r.breaches?.details?.length) {
                html += `<div class="bg-red-900/20 border border-red-500/30 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Data Breaches</h4><div class="space-y-1">`;
                r.breaches.details.forEach(b => { html += `<div class="text-xs bg-slate-800/50 rounded p-2"><span class="text-red-300 font-bold">${b.name}</span> <span class="text-slate-500">${b.date}</span><div class="flex flex-wrap gap-1 mt-1">${(b.data_compromised||[]).map(d=>`<span class="px-1.5 py-0.5 bg-red-500/20 text-red-300 rounded text-[10px]">${d}</span>`).join('')}</div></div>`; });
                html += `</div></div>`;
            }
            // Linked Profiles
            if (r.linked_profiles?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-emerald-400 text-xs font-bold mb-2">Linked Social Profiles</h4><div class="grid grid-cols-2 gap-1">`;
                r.linked_profiles.forEach(p => { html += `<div class="text-xs bg-slate-800/50 rounded p-1.5"><span class="text-emerald-300">${p.platform}</span> → <span class="text-white font-mono">${p.username}</span> <span class="text-slate-500">${p.confidence}%</span></div>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#dr-email-result').html(html);
        });
    },

    infraMap() {
        const target = $('#dr-infra-input').val();
        if (!target) return GrowlNotification.notify({title:'Error',description:'Enter target',type:'error',position:'top-right',closeTimeout:3000});
        $('#dr-infra-result').html('<div class="text-emerald-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Mapping infrastructure...</div>');
        $.post('/api/deeprecon/infra', {target}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-3 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Total IPs</div><div class="text-xl font-bold text-cyan-400">${r.total_ips||0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Exposed Services</div><div class="text-xl font-bold text-orange-400">${r.exposed_services||0}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Attack Surface</div><div class="text-xl font-bold text-red-400">${r.attack_surface_score||0}/100</div></div>
                </div>`;
            // ASN
            if (r.asn) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">ASN Information</h4><div class="grid grid-cols-2 gap-1 text-xs">
                    <div><span class="text-slate-400">ASN:</span> <span class="text-cyan-400 font-mono">${r.asn.number}</span></div>
                    <div><span class="text-slate-400">Name:</span> <span class="text-white">${r.asn.name}</span></div>
                    <div><span class="text-slate-400">Country:</span> <span class="text-white">${r.asn.country}</span></div>
                    <div><span class="text-slate-400">Peers:</span> <span class="text-white">${r.asn.peers}</span></div>
                </div></div>`;
            }
            // Cloud
            if (r.cloud_infrastructure?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-emerald-400 text-xs font-bold mb-2">Cloud Infrastructure</h4><div class="space-y-1">`;
                r.cloud_infrastructure.forEach(c => { html += `<div class="bg-slate-800/50 rounded p-2 text-xs"><span class="text-emerald-300 font-bold">${c.provider}</span><div class="flex flex-wrap gap-1 mt-1">${(c.services_detected||[]).map(s=>`<span class="px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded text-[10px]">${s}</span>`).join('')}</div><div class="text-slate-500 mt-1">Regions: ${(c.regions||[]).join(', ')}</div></div>`; });
                html += `</div></div>`;
            }
            // Network Topology
            if (r.network_topology?.nodes?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-yellow-400 text-xs font-bold mb-2">Network Topology</h4><div class="space-y-1">`;
                r.network_topology.nodes.forEach(n => { html += `<div class="flex justify-between items-center text-xs bg-slate-800/50 rounded p-1.5"><span class="text-yellow-300 font-bold">${n.type}</span><span class="text-slate-400">${n.os||n.engine||n.provider||''}</span><span class="text-slate-500 font-mono">${(n.ips||[]).join(', ')}</span></div>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#dr-infra-result').html(html);
        });
    },

    correlateData() {
        const input = $('#dr-correlate-input').val();
        if (!input) return GrowlNotification.notify({title:'Error',description:'Enter entities to correlate',type:'error',position:'top-right',closeTimeout:3000});
        const entities = input.split('\n').map(s=>s.trim()).filter(s=>s);
        $('#dr-correlate-result').html('<div class="text-emerald-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Correlating data...</div>');
        $.post('/api/deeprecon/correlate', {entities: JSON.stringify(entities)}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">`;
            if (r.threat_summary) {
                const ts = r.threat_summary;
                html += `<div class="grid grid-cols-3 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Entities</div><div class="text-xl font-bold text-emerald-400">${ts.entities_analyzed}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Correlations</div><div class="text-xl font-bold text-cyan-400">${ts.correlations_found}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Avg Risk</div><div class="text-xl font-bold text-orange-400">${ts.avg_risk_score}</div></div>
                </div>`;
            }
            // Nodes
            if (r.graph?.nodes?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-emerald-400 text-xs font-bold mb-2">Entities</h4><div class="space-y-1">`;
                r.graph.nodes.forEach(n => { html += `<div class="flex justify-between text-xs bg-slate-800/50 rounded p-1.5"><span class="text-white font-mono">${n.label}</span><span class="text-emerald-300">${n.type}</span><span class="text-yellow-400">Risk: ${n.risk_score}</span></div>`; });
                html += `</div></div>`;
            }
            // Edges
            if (r.graph?.edges?.length) {
                html += `<div class="bg-cyan-900/20 border border-cyan-500/30 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">Relationships</h4><div class="space-y-1">`;
                r.graph.edges.forEach(e => {
                    const fromNode = r.graph.nodes[e.from]?.label || e.from;
                    const toNode = r.graph.nodes[e.to]?.label || e.to;
                    html += `<div class="text-xs bg-slate-800/50 rounded p-1.5"><span class="text-white">${fromNode}</span> <span class="text-cyan-400">↔ ${e.relationship?.replace(/_/g,' ')}</span> <span class="text-white">${toNode}</span><span class="text-slate-500 ml-2">${e.confidence}% — ${e.evidence}</span></div>`;
                });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#dr-correlate-result').html(html);
        });
    }
};
