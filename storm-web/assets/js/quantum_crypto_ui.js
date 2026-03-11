/**
 * Storm-Breaker Quantum Crypto Engine UI
 * Post-quantum encryption, entropy analysis, algorithm benchmarking,
 * quantum threat assessment, and key exchange simulation
 */
const QuantumCryptoUI = {
    initialized: false,

    init() {
        if (!this.initialized) {
            this.bindEvents();
        }
        this.initialized = true;
        this.render();
    },

    bindEvents() {
        $(document).on('click', '#btn-qc-encrypt', () => this.encryptData());
        $(document).on('click', '#btn-qc-entropy', () => this.analyzeEntropy());
        $(document).on('click', '#btn-qc-benchmark', () => this.benchmark());
        $(document).on('click', '#btn-qc-threat', () => this.threatAssessment());
        $(document).on('click', '#btn-qc-keyex', () => this.keyExchange());
        $(document).on('click', '.qc-sub-tab', function() {
            const t = $(this).data('target');
            $('.qc-sub-tab').removeClass('bg-cyan-600 text-white').addClass('bg-slate-700 text-slate-300');
            $(this).removeClass('bg-slate-700 text-slate-300').addClass('bg-cyan-600 text-white');
            $('.qc-sub-panel').addClass('hidden');
            $(`#${t}`).removeClass('hidden');
        });
    },

    render() {
        const c = $('#quantum-dashboard');
        if (!c.length) return;
        c.html(`
            <div class="space-y-4">
                <div class="flex flex-wrap gap-1.5 p-1.5 bg-slate-900/50 rounded-xl border border-slate-700/50">
                    <button class="qc-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-cyan-600 text-white" data-target="qc-panel-encrypt"><i class="fas fa-lock mr-1"></i>PQ Encryption</button>
                    <button class="qc-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="qc-panel-entropy"><i class="fas fa-random mr-1"></i>Entropy Analysis</button>
                    <button class="qc-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="qc-panel-benchmark"><i class="fas fa-tachometer-alt mr-1"></i>Benchmarks</button>
                    <button class="qc-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="qc-panel-threat"><i class="fas fa-atom mr-1"></i>Quantum Threat</button>
                    <button class="qc-sub-tab px-3 py-1.5 rounded-lg text-xs font-bold bg-slate-700 text-slate-300" data-target="qc-panel-keyex"><i class="fas fa-exchange-alt mr-1"></i>Key Exchange</button>
                </div>

                <!-- PQ Encryption -->
                <div id="qc-panel-encrypt" class="qc-sub-panel">
                    <div class="bg-slate-800/80 rounded-xl border border-cyan-500/30 p-4">
                        <h3 class="text-cyan-400 font-bold mb-3"><i class="fas fa-lock mr-2"></i>Post-Quantum Encryption</h3>
                        <p class="text-slate-400 text-xs mb-3">Encrypt data using NIST-standardized post-quantum algorithms — Kyber, Dilithium, SPHINCS+, and more.</p>
                        <textarea id="qc-plaintext" rows="3" class="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-green-300 text-sm font-mono mb-2" placeholder="Enter plaintext to encrypt..."></textarea>
                        <div class="flex gap-2">
                            <select id="qc-algorithm" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="kyber1024">CRYSTALS-Kyber-1024 (NIST Level 5)</option>
                                <option value="dilithium5">CRYSTALS-Dilithium-5 (NIST Level 5)</option>
                                <option value="sphincs_sha2">SPHINCS+-SHA2-256f (NIST Level 5)</option>
                                <option value="falcon1024">FALCON-1024 (NTRU Lattice)</option>
                                <option value="bike_l3">BIKE Level 3 (Code-based)</option>
                                <option value="hqc256">HQC-256 (Code-based)</option>
                                <option value="mceliece">Classic McEliece 8192128</option>
                                <option value="aes256_gcm">AES-256-GCM (Symmetric)</option>
                            </select>
                            <button id="btn-qc-encrypt" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-shield-alt mr-1"></i>Encrypt</button>
                        </div>
                        <div id="qc-encrypt-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Entropy Analysis -->
                <div id="qc-panel-entropy" class="qc-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-cyan-500/30 p-4">
                        <h3 class="text-cyan-400 font-bold mb-3"><i class="fas fa-random mr-2"></i>Entropy & Randomness Analysis</h3>
                        <p class="text-slate-400 text-xs mb-3">Analyze data entropy, Shannon information, chi-squared distribution, serial correlation, and crypto-suitability.</p>
                        <textarea id="qc-entropy-data" rows="3" class="w-full bg-slate-900 border border-slate-600 rounded-lg p-3 text-green-300 text-sm font-mono mb-2" placeholder="Enter data to analyze entropy (or leave blank for random sample)..."></textarea>
                        <button id="btn-qc-entropy" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-chart-bar mr-1"></i>Analyze</button>
                        <div id="qc-entropy-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Benchmarks -->
                <div id="qc-panel-benchmark" class="qc-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-cyan-500/30 p-4">
                        <h3 class="text-cyan-400 font-bold mb-3"><i class="fas fa-tachometer-alt mr-2"></i>Algorithm Benchmarks</h3>
                        <p class="text-slate-400 text-xs mb-3">Compare performance of all post-quantum algorithms — keygen, encrypt/sign, decrypt/verify speeds and memory usage.</p>
                        <button id="btn-qc-benchmark" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-play mr-1"></i>Run Benchmarks</button>
                        <div id="qc-benchmark-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Quantum Threat Assessment -->
                <div id="qc-panel-threat" class="qc-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-cyan-500/30 p-4">
                        <h3 class="text-cyan-400 font-bold mb-3"><i class="fas fa-atom mr-2"></i>Quantum Threat Assessment</h3>
                        <p class="text-slate-400 text-xs mb-3">Comprehensive assessment of quantum computing threat to current cryptography — timeline, vulnerable systems, and migration plan.</p>
                        <button id="btn-qc-threat" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-exclamation-triangle mr-1"></i>Assess Threats</button>
                        <div id="qc-threat-result" class="mt-3"></div>
                    </div>
                </div>

                <!-- Key Exchange Simulation -->
                <div id="qc-panel-keyex" class="qc-sub-panel hidden">
                    <div class="bg-slate-800/80 rounded-xl border border-cyan-500/30 p-4">
                        <h3 class="text-cyan-400 font-bold mb-3"><i class="fas fa-exchange-alt mr-2"></i>Quantum-Safe Key Exchange</h3>
                        <p class="text-slate-400 text-xs mb-3">Simulate a post-quantum key exchange between two parties using lattice-based Key Encapsulation Mechanisms.</p>
                        <div class="flex gap-2 mb-3">
                            <select id="qc-kex-algo" class="flex-1 bg-slate-900 border border-slate-600 rounded-lg p-2 text-white text-sm">
                                <option value="kyber1024">CRYSTALS-Kyber-1024</option>
                                <option value="bike_l3">BIKE Level 3</option>
                                <option value="hqc256">HQC-256</option>
                                <option value="mceliece">Classic McEliece</option>
                            </select>
                            <button id="btn-qc-keyex" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg text-sm font-bold"><i class="fas fa-key mr-1"></i>Simulate</button>
                        </div>
                        <div id="qc-keyex-result" class="mt-3"></div>
                    </div>
                </div>
            </div>
        `);
    },

    encryptData() {
        const plaintext = $('#qc-plaintext').val();
        if (!plaintext) return GrowlNotification.notify({title:'Error',description:'Enter plaintext',type:'error',position:'top-right',closeTimeout:3000});
        const algorithm = $('#qc-algorithm').val();
        $('#qc-encrypt-result').html('<div class="text-cyan-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Encrypting with post-quantum algorithm...</div>');
        $.post('/api/quantum/encrypt', {plaintext, algorithm}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-4 gap-2">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Algorithm</div><div class="text-xs font-bold text-cyan-400">${r.algorithm}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">NIST Level</div><div class="text-sm font-bold text-green-400">${r.nist_level}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Quantum Safe</div><div class="text-sm font-bold ${r.quantum_safe?'text-green-400':'text-red-400'}">${r.quantum_safe?'YES':'NO'}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Overhead</div><div class="text-sm font-bold text-yellow-400">${r.overhead_ratio}x</div></div>
                </div>
                <div class="bg-slate-900 rounded-lg p-3"><div class="text-xs text-slate-400 mb-1">Ciphertext (${r.ciphertext_size} chars)</div><div class="text-xs text-cyan-300 font-mono break-all max-h-32 overflow-y-auto">${r.ciphertext}</div></div>
                <div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="bg-slate-700/50 rounded-lg p-2"><span class="text-slate-400">Key Fingerprint:</span><div class="text-cyan-400 font-mono">${r.public_key_fingerprint}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2"><span class="text-slate-400">Nonce:</span><div class="text-green-400 font-mono">${r.nonce}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2"><span class="text-slate-400">Tag:</span><div class="text-yellow-400 font-mono">${r.tag}</div></div>
                </div>
                <div class="text-xs text-slate-500">Encrypt time: ${r.encrypt_time_ms}ms | Family: ${r.family}</div>
            </div>`;
            $('#qc-encrypt-result').html(html);
        });
    },

    analyzeEntropy() {
        const data = $('#qc-entropy-data').val() || Array.from({length:256}, ()=>String.fromCharCode(Math.floor(Math.random()*256))).join('');
        $('#qc-entropy-result').html('<div class="text-cyan-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Analyzing entropy...</div>');
        $.post('/api/quantum/entropy', {data}, (d) => {
            if (!d.success) return;
            const r = d.result;
            const qColor = r.quality === 'excellent' ? 'green' : r.quality === 'good' ? 'cyan' : r.quality === 'fair' ? 'yellow' : 'red';
            let html = `<div class="space-y-3">
                <div class="grid grid-cols-4 gap-2">
                    <div class="bg-${qColor}-900/20 border border-${qColor}-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Quality</div><div class="text-sm font-bold text-${qColor}-400">${(r.quality||'').toUpperCase()}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Shannon Entropy</div><div class="text-sm font-bold text-cyan-400">${r.shannon_entropy}</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Entropy Ratio</div><div class="text-sm font-bold text-white">${(r.entropy_ratio*100).toFixed(1)}%</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Crypto Suitable</div><div class="text-sm font-bold ${r.crypto_suitable?'text-green-400':'text-red-400'}">${r.crypto_suitable?'YES':'NO'}</div></div>
                </div>
                <div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="bg-slate-700/50 rounded-lg p-2"><span class="text-slate-400">Chi-Squared:</span> <span class="text-white">${r.chi_squared}</span></div>
                    <div class="bg-slate-700/50 rounded-lg p-2"><span class="text-slate-400">Unique Bytes:</span> <span class="text-white">${r.unique_bytes}/256</span></div>
                    <div class="bg-slate-700/50 rounded-lg p-2"><span class="text-slate-400">Serial Correlation:</span> <span class="text-white">${r.serial_correlation}</span></div>
                </div>
                <div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-1">Recommendations</h4><ul class="list-disc list-inside text-xs text-slate-300">`;
            (r.recommendations||[]).forEach(rec => { html += `<li>${rec}</li>`; });
            html += `</ul></div></div>`;
            $('#qc-entropy-result').html(html);
        });
    },

    benchmark() {
        $('#qc-benchmark-result').html('<div class="text-cyan-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Running benchmarks...</div>');
        $.get('/api/quantum/benchmark', (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">`;
            if (r.best_kem) html += `<div class="bg-green-900/20 border border-green-500/30 rounded-lg p-2 text-xs"><span class="text-green-400 font-bold">Best KEM:</span> <span class="text-white">${r.best_kem.algorithm}</span> <span class="text-slate-400">(${r.best_kem.encrypt_ms}ms)</span></div>`;
            if (r.best_signature) html += `<div class="bg-blue-900/20 border border-blue-500/30 rounded-lg p-2 text-xs"><span class="text-blue-400 font-bold">Best Signature:</span> <span class="text-white">${r.best_signature.algorithm}</span> <span class="text-slate-400">(${r.best_signature.encrypt_ms}ms)</span></div>`;
            if (r.benchmarks?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">All Algorithms</h4><div class="space-y-1">`;
                r.benchmarks.forEach(b => {
                    const barWidth = Math.min(100, b.score * 2);
                    html += `<div class="bg-slate-800 rounded p-2"><div class="flex justify-between items-center text-xs mb-1"><span class="text-white font-bold">${b.algorithm}</span><span class="text-slate-400">${b.type} | ${b.family}</span><span class="text-cyan-400">Score: ${b.score}</span></div><div class="w-full bg-slate-700 rounded-full h-1.5"><div class="bg-cyan-500 h-1.5 rounded-full" style="width:${barWidth}%"></div></div><div class="flex justify-between text-[10px] text-slate-500 mt-1"><span>KeyGen: ${b.keygen_ms}ms</span><span>Encrypt: ${b.encrypt_ms}ms</span><span>Decrypt: ${b.decrypt_ms}ms</span><span>Ops/s: ${b.ops_per_second}</span><span>NIST: ${b.nist_level}</span></div></div>`;
                });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#qc-benchmark-result').html(html);
        });
    },

    threatAssessment() {
        $('#qc-threat-result').html('<div class="text-cyan-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Assessing quantum threats...</div>');
        $.get('/api/quantum/threat', (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">`;
            if (r.quantum_timeline) {
                const qt = r.quantum_timeline;
                html += `<div class="grid grid-cols-4 gap-2">
                    <div class="bg-red-900/20 border border-red-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Current Qubits</div><div class="text-lg font-bold text-red-400">${qt.current_qubits}</div></div>
                    <div class="bg-orange-900/20 border border-orange-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Logical Qubits</div><div class="text-lg font-bold text-orange-400">${qt.logical_qubits_available}</div></div>
                    <div class="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Years to Threat</div><div class="text-lg font-bold text-yellow-400">${qt.years_to_cryptographic_threat}</div></div>
                    <div class="bg-cyan-900/20 border border-cyan-500/30 rounded-lg p-2 text-center"><div class="text-xs text-slate-400">Threat Year</div><div class="text-lg font-bold text-cyan-400">${qt.estimated_threat_year}</div></div>
                </div>`;
            }
            if (r.vulnerable_systems?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-2">Vulnerable Cryptographic Systems</h4><div class="space-y-1">`;
                r.vulnerable_systems.forEach(s => {
                    const c = s.risk === 'critical' ? 'red' : s.risk === 'medium' ? 'yellow' : 'green';
                    html += `<div class="bg-${c}-900/10 border border-${c}-500/20 rounded p-2 flex justify-between items-center text-xs"><span class="text-white font-bold">${s.protocol}</span><span class="text-slate-400">${s.usage}</span><span class="text-${c}-400">${(s.risk||'').toUpperCase()}</span><span class="text-slate-500">Urgency: ${s.migration_urgency}</span></div>`;
                });
                html += `</div></div>`;
            }
            if (r.migration_recommendations?.length) {
                html += `<div class="bg-green-900/20 border border-green-500/30 rounded-lg p-3"><h4 class="text-green-400 text-xs font-bold mb-2">Migration Roadmap</h4><div class="space-y-1">`;
                r.migration_recommendations.forEach(m => { html += `<div class="text-xs flex gap-2"><span class="w-5 h-5 rounded-full bg-green-600 text-white flex items-center justify-center text-[10px] shrink-0">${m.priority}</span><span class="text-white">${m.action}</span><span class="text-slate-500 ml-auto">${m.timeline}</span></div>`; });
                html += `</div></div>`;
            }
            if (r.hndl_risk) {
                html += `<div class="bg-red-900/30 border border-red-500/40 rounded-lg p-3"><h4 class="text-red-400 text-xs font-bold mb-1">⚠️ Harvest Now, Decrypt Later</h4><p class="text-xs text-slate-300">${r.hndl_risk.description}</p><div class="flex flex-wrap gap-1 mt-2">`;
                (r.hndl_risk.targeted_data||[]).forEach(d => { html += `<span class="px-2 py-0.5 bg-red-500/20 text-red-300 rounded text-xs">${d}</span>`; });
                html += `</div></div>`;
            }
            html += `</div>`;
            $('#qc-threat-result').html(html);
        });
    },

    keyExchange() {
        const algo = $('#qc-kex-algo').val();
        $('#qc-keyex-result').html('<div class="text-cyan-400 animate-pulse"><i class="fas fa-spinner fa-spin mr-2"></i>Simulating key exchange...</div>');
        $.post('/api/quantum/key-exchange', {algorithm: algo}, (d) => {
            if (!d.success) return;
            const r = d.result;
            let html = `<div class="space-y-3">
                <div class="bg-cyan-900/20 border border-cyan-500/30 rounded-lg p-3 text-center"><span class="text-cyan-400 font-bold">${r.algorithm}</span> <span class="text-slate-400 text-xs">| NIST Level ${r.nist_level} | ${r.total_time_ms}ms total</span></div>`;
            if (r.steps?.length) {
                html += `<div class="bg-slate-700/50 rounded-lg p-3"><h4 class="text-cyan-400 text-xs font-bold mb-2">Protocol Steps</h4><div class="space-y-2">`;
                r.steps.forEach(s => {
                    const actorColor = s.actor === 'Alice' ? 'pink' : s.actor === 'Bob' ? 'blue' : 'green';
                    html += `<div class="flex items-start gap-2 text-xs"><span class="w-5 h-5 rounded-full bg-${actorColor}-600 text-white flex items-center justify-center text-[10px] shrink-0">${s.step}</span><div><span class="text-${actorColor}-400 font-bold">${s.actor}:</span> <span class="text-white">${s.action}</span><div class="text-slate-500 font-mono mt-0.5">${s.data}</div><span class="text-slate-600">${s.time_ms}ms</span></div></div>`;
                });
                html += `</div></div>`;
            }
            if (r.key_sizes) {
                html += `<div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><span class="text-slate-400">Public Key</span><div class="text-cyan-400 font-bold">${r.key_sizes.public_key} bytes</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><span class="text-slate-400">Ciphertext</span><div class="text-cyan-400 font-bold">${r.key_sizes.ciphertext} bytes</div></div>
                    <div class="bg-slate-700/50 rounded-lg p-2 text-center"><span class="text-slate-400">Shared Secret</span><div class="text-green-400 font-bold">${r.key_sizes.shared_secret} bytes</div></div>
                </div>`;
            }
            if (r.security_notes?.length) {
                html += `<div class="bg-green-900/20 border border-green-500/30 rounded-lg p-3"><h4 class="text-green-400 text-xs font-bold mb-1">Security Notes</h4><ul class="list-disc list-inside text-xs text-slate-300">`;
                r.security_notes.forEach(n => { html += `<li>${n}</li>`; });
                html += `</ul></div>`;
            }
            html += `</div>`;
            $('#qc-keyex-result').html(html);
        });
    }
};
