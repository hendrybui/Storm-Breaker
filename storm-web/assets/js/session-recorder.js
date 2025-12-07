// Session Recording Manager
// Records and replays user sessions including mouse movements, clicks, scrolls, etc.
// Uses rrweb (record and replay the web) library

const SessionRecorder = {
    isRecording: false,
    events: [],
    stopFn: null,
    endpoint: '/api/session',
    sendInterval: null,
    sessionId: null,

    // Initialize the recorder
    init(options = {}) {
        this.endpoint = options.endpoint || '/api/session';
        this.sendIntervalTime = options.sendInterval || 10000; // Send every 10 seconds
        this.sessionId = this.generateSessionId();

        // Check if rrweb is loaded
        if (typeof rrweb === 'undefined') {
            console.error('rrweb library not loaded. Please include rrweb script.');
            return false;
        }

        this.startRecording();
        return true;
    },

    // Generate unique session ID
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    },

    // Start recording
    startRecording() {
        if (this.isRecording) return;

        try {
            this.stopFn = rrweb.record({
                emit: (event) => {
                    this.events.push(event);

                    // Send events if buffer is too large (>500 events)
                    if (this.events.length >= 500) {
                        this.sendEvents();
                    }
                },
                // Recording options
                checkoutEveryNms: 60000, // Create full snapshot every 60 seconds
                checkoutEveryNth: 200, // Create full snapshot every 200 events
                recordCanvas: true, // Record canvas elements
                recordLog: true, // Record console logs
                recordCrossOriginIframes: false, // Don't record cross-origin iframes
                sampling: {
                    // Mouse movement sampling
                    mousemove: true,
                    mouseInteraction: {
                        MouseUp: true,
                        MouseDown: true,
                        Click: true,
                        ContextMenu: true,
                        DblClick: true,
                        Focus: true,
                        Blur: true,
                        TouchStart: true,
                        TouchEnd: true
                    },
                    // Scroll sampling
                    scroll: 150, // Throttle scroll events to every 150ms
                    // Media interaction
                    media: 800, // Throttle media events to every 800ms
                    // Input sampling
                    input: 'last' // Only record last input value
                },
                // Privacy settings (set to false to capture everything)
                maskAllInputs: false, // Capture input values
                maskInputOptions: {
                    password: false // Even capture passwords
                },
                maskTextSelector: null, // Don't mask any text
                blockClass: 'rr-block', // Elements with this class won't be recorded
                ignoreClass: 'rr-ignore', // Elements with this class won't trigger events
                inlineStylesheet: true,
                collectFonts: true
            });

            this.isRecording = true;
            console.log('Session recording started:', this.sessionId);

            // Start periodic sending
            this.startSendInterval();

            // Send session start event
            this.sendSessionStart();

        } catch (e) {
            console.error('Failed to start recording:', e);
            this.isRecording = false;
        }
    },

    // Stop recording
    stopRecording() {
        if (!this.isRecording) return;

        if (this.stopFn) {
            this.stopFn();
            this.stopFn = null;
        }

        this.isRecording = false;

        // Stop send interval
        if (this.sendInterval) {
            clearInterval(this.sendInterval);
            this.sendInterval = null;
        }

        // Send remaining events
        this.sendEvents();

        // Send session end event
        this.sendSessionEnd();

        console.log('Session recording stopped');
    },

    // Start interval to send events periodically
    startSendInterval() {
        this.sendInterval = setInterval(() => {
            if (this.events.length > 0) {
                this.sendEvents();
            }
        }, this.sendIntervalTime);
    },

    // Send session start notification
    async sendSessionStart() {
        try {
            await fetch(this.endpoint + '/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    url: window.location.href,
                    userAgent: navigator.userAgent,
                    timestamp: new Date().toISOString(),
                    viewport: {
                        width: window.innerWidth,
                        height: window.innerHeight
                    }
                })
            });
        } catch (e) {
            console.error('Failed to send session start:', e);
        }
    },

    // Send session end notification
    async sendSessionEnd() {
        try {
            await fetch(this.endpoint + '/end', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    timestamp: new Date().toISOString(),
                    duration: this.getSessionDuration()
                })
            });
        } catch (e) {
            console.error('Failed to send session end:', e);
        }
    },

    // Send recorded events to server
    async sendEvents() {
        if (this.events.length === 0) return;

        const eventsToSend = [...this.events];
        this.events = []; // Clear events

        try {
            await fetch(this.endpoint + '/events', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionId: this.sessionId,
                    events: eventsToSend,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (e) {
            console.error('Failed to send session events:', e);
            // Re-add events if send failed (keep only last 1000 to prevent memory issues)
            this.events = eventsToSend.concat(this.events).slice(-1000);
        }
    },

    // Get session duration
    getSessionDuration() {
        if (this.events.length === 0) return 0;

        const firstEvent = this.events[0];
        const lastEvent = this.events[this.events.length - 1];

        return lastEvent.timestamp - firstEvent.timestamp;
    },

    // Get current event count
    getEventCount() {
        return this.events.length;
    },

    // Pause recording
    pause() {
        this.isRecording = false;
    },

    // Resume recording
    resume() {
        this.isRecording = true;
    }
};

// Auto-initialize on page load (can be disabled)
if (typeof window !== 'undefined') {
    window.SessionRecorder = SessionRecorder;
}
