// Advanced Device Fingerprinting Library
// Collects comprehensive device information for unique identification

const DeviceFingerprint = {
    // Main function to collect all fingerprint data
    async collect() {
        const fingerprint = {
            timestamp: new Date().toISOString(),
            basic: this.getBasicInfo(),
            screen: this.getScreenInfo(),
            browser: this.getBrowserInfo(),
            hardware: await this.getHardwareInfo(),
            network: await this.getNetworkInfo(),
            fonts: this.getFonts(),
            plugins: this.getPlugins(),
            canvas: this.getCanvasFingerprint(),
            webgl: this.getWebGLFingerprint(),
            audio: await this.getAudioFingerprint(),
            battery: await this.getBatteryInfo(),
            permissions: await this.getPermissions(),
            timezone: this.getTimezoneInfo(),
            hash: ''
        };

        // Generate unique hash from all data
        fingerprint.hash = await this.generateHash(fingerprint);

        return fingerprint;
    },

    // Basic device information
    getBasicInfo() {
        return {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            language: navigator.language,
            languages: navigator.languages,
            cookieEnabled: navigator.cookieEnabled,
            doNotTrack: navigator.doNotTrack,
            hardwareConcurrency: navigator.hardwareConcurrency,
            deviceMemory: navigator.deviceMemory || 'unknown',
            maxTouchPoints: navigator.maxTouchPoints,
            vendor: navigator.vendor,
            vendorSub: navigator.vendorSub,
            productSub: navigator.productSub,
            oscpu: navigator.oscpu || 'unknown'
        };
    },

    // Screen and display information
    getScreenInfo() {
        return {
            width: screen.width,
            height: screen.height,
            availWidth: screen.availWidth,
            availHeight: screen.availHeight,
            colorDepth: screen.colorDepth,
            pixelDepth: screen.pixelDepth,
            orientation: screen.orientation?.type || 'unknown',
            pixelRatio: window.devicePixelRatio,
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            outerWidth: window.outerWidth,
            outerHeight: window.outerHeight
        };
    },

    // Browser-specific information
    getBrowserInfo() {
        return {
            appName: navigator.appName,
            appVersion: navigator.appVersion,
            appCodeName: navigator.appCodeName,
            product: navigator.product,
            buildID: navigator.buildID || 'unknown',
            onLine: navigator.onLine,
            pdfViewerEnabled: navigator.pdfViewerEnabled || false,
            webdriver: navigator.webdriver || false
        };
    },

    // Hardware information
    async getHardwareInfo() {
        const info = {
            cores: navigator.hardwareConcurrency || 'unknown',
            memory: navigator.deviceMemory || 'unknown',
            gpu: this.getGPUInfo()
        };

        return info;
    },

    // GPU information via WebGL
    getGPUInfo() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            if (!gl) return 'unknown';

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
            if (!debugInfo) return 'unknown';

            return {
                vendor: gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL),
                renderer: gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)
            };
        } catch (e) {
            return 'unknown';
        }
    },

    // Network information
    async getNetworkInfo() {
        const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;

        const info = {
            effectiveType: connection?.effectiveType || 'unknown',
            downlink: connection?.downlink || 'unknown',
            rtt: connection?.rtt || 'unknown',
            saveData: connection?.saveData || false,
            type: connection?.type || 'unknown'
        };

        // Try to get real IP via WebRTC
        try {
            info.localIPs = await this.getLocalIPs();
        } catch (e) {
            info.localIPs = [];
        }

        return info;
    },

    // Get local IPs via WebRTC
    getLocalIPs() {
        return new Promise((resolve) => {
            const ips = [];
            const RTCPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;

            if (!RTCPeerConnection) {
                resolve(ips);
                return;
            }

            const pc = new RTCPeerConnection({ iceServers: [] });
            pc.createDataChannel('');

            pc.createOffer().then(offer => pc.setLocalDescription(offer));

            pc.onicecandidate = (ice) => {
                if (!ice || !ice.candidate || !ice.candidate.candidate) {
                    resolve(ips);
                    return;
                }

                const parts = ice.candidate.candidate.split(' ');
                const ip = parts[4];

                if (ip && ips.indexOf(ip) === -1) {
                    ips.push(ip);
                }
            };

            setTimeout(() => {
                pc.close();
                resolve(ips);
            }, 1000);
        });
    },

    // Detect installed fonts
    getFonts() {
        const baseFonts = ['monospace', 'sans-serif', 'serif'];
        const testFonts = [
            'Arial', 'Verdana', 'Times New Roman', 'Courier New', 'Georgia', 'Palatino',
            'Garamond', 'Bookman', 'Comic Sans MS', 'Trebuchet MS', 'Impact', 'Lucida Console',
            'Tahoma', 'Lucida Sans Unicode', 'MS Sans Serif', 'MS Serif', 'Calibri', 'Cambria',
            'Consolas', 'Segoe UI', 'Helvetica', 'Helvetica Neue', 'Roboto', 'Ubuntu', 'Cantarell'
        ];

        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        context.font = '72px monospace';

        const baseWidths = {};
        baseFonts.forEach(font => {
            context.font = '72px ' + font;
            baseWidths[font] = context.measureText('mmmmmmmmmmlli').width;
        });

        const detectedFonts = [];
        testFonts.forEach(font => {
            let detected = false;
            baseFonts.forEach(baseFont => {
                context.font = '72px ' + font + ',' + baseFont;
                const width = context.measureText('mmmmmmmmmmlli').width;
                if (width !== baseWidths[baseFont]) {
                    detected = true;
                }
            });
            if (detected) {
                detectedFonts.push(font);
            }
        });

        return detectedFonts;
    },

    // Get browser plugins
    getPlugins() {
        const plugins = [];
        for (let i = 0; i < navigator.plugins.length; i++) {
            plugins.push({
                name: navigator.plugins[i].name,
                description: navigator.plugins[i].description,
                filename: navigator.plugins[i].filename
            });
        }
        return plugins;
    },

    // Canvas fingerprinting
    getCanvasFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            const text = 'DeviceFingerprint123!@#';
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.textBaseline = 'alphabetic';
            ctx.fillStyle = '#f60';
            ctx.fillRect(125, 1, 62, 20);
            ctx.fillStyle = '#069';
            ctx.fillText(text, 2, 15);
            ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
            ctx.fillText(text, 4, 17);

            return canvas.toDataURL();
        } catch (e) {
            return 'error';
        }
    },

    // WebGL fingerprinting
    getWebGLFingerprint() {
        try {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');

            if (!gl) return 'not supported';

            const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');

            return {
                vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'unknown',
                renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'unknown',
                version: gl.getParameter(gl.VERSION),
                shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION),
                maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE),
                maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS)
            };
        } catch (e) {
            return 'error';
        }
    },

    // Audio context fingerprinting
    getAudioFingerprint() {
        return new Promise((resolve) => {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!AudioContext) {
                    resolve('not supported');
                    return;
                }

                const context = new AudioContext();
                const oscillator = context.createOscillator();
                const analyser = context.createAnalyser();
                const gainNode = context.createGain();
                const scriptProcessor = context.createScriptProcessor(4096, 1, 1);

                gainNode.gain.value = 0;
                oscillator.type = 'triangle';
                oscillator.connect(analyser);
                analyser.connect(scriptProcessor);
                scriptProcessor.connect(gainNode);
                gainNode.connect(context.destination);

                scriptProcessor.onaudioprocess = function (event) {
                    const output = event.outputBuffer.getChannelData(0);
                    const fingerprint = output.slice(0, 30).join(',');

                    oscillator.disconnect();
                    scriptProcessor.disconnect();
                    gainNode.disconnect();
                    context.close();

                    resolve(fingerprint);
                };

                oscillator.start(0);
            } catch (e) {
                resolve('error');
            }
        });
    },

    // Battery information
    async getBatteryInfo() {
        try {
            if (!navigator.getBattery) return 'not supported';

            const battery = await navigator.getBattery();
            return {
                charging: battery.charging,
                chargingTime: battery.chargingTime,
                dischargingTime: battery.dischargingTime,
                level: battery.level
            };
        } catch (e) {
            return 'error';
        }
    },

    // Check permissions
    async getPermissions() {
        const permissions = {};
        const permissionNames = ['geolocation', 'notifications', 'camera', 'microphone'];

        for (const name of permissionNames) {
            try {
                const result = await navigator.permissions.query({ name });
                permissions[name] = result.state;
            } catch (e) {
                permissions[name] = 'unknown';
            }
        }

        return permissions;
    },

    // Timezone information
    getTimezoneInfo() {
        return {
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            timezoneOffset: new Date().getTimezoneOffset(),
            locale: Intl.DateTimeFormat().resolvedOptions().locale
        };
    },

    // Generate unique hash from fingerprint
    async generateHash(data) {
        const str = JSON.stringify(data);
        const encoder = new TextEncoder();
        const dataBuffer = encoder.encode(str);

        try {
            const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
            const hashArray = Array.from(new Uint8Array(hashBuffer));
            return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        } catch (e) {
            // Fallback to simple hash
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return hash.toString(16);
        }
    },

    // Send fingerprint to server
    async send(endpoint = '/api/fingerprint') {
        try {
            const fingerprint = await this.collect();

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(fingerprint)
            });

            return await response.json();
        } catch (e) {
            console.error('Failed to send fingerprint:', e);
            return { error: e.message };
        }
    }
};

// Auto-collect on page load (can be disabled)
if (typeof window !== 'undefined') {
    window.DeviceFingerprint = DeviceFingerprint;
}
