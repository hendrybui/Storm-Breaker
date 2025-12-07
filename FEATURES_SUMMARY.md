# Storm-Breaker Features - Quick Summary

## 🎯 At a Glance

| Category | Count | Status |
|----------|-------|--------|
| **Total Templates** | 12 | ✅ Active |
| **Basic Templates** | 10 | ✅ Active |
| **Advanced Templates** | 2 | ✅ Active |
| **Advanced Features** | 3 | ✅ Active |
| **Supported Platforms** | 4 | ✅ Active |
| **Browser APIs Used** | 10+ | ✅ Active |

---

## 📱 Templates Quick Reference

| # | Template | Purpose | Captures | Status |
|---|----------|---------|----------|--------|
| 1 | **Zoom Meeting** | Video call join | Camera, Mic, Device Info | ✅ Enhanced |
| 2 | **Job Application** | Job form | Camera, Location, Form Data | ✅ Enhanced |
| 3 | **Free WiFi** | WiFi portal | Location, Device Info | ✅ Stable |
| 4 | **Cloudflare Captcha** | CAPTCHA verify | Device Info, Clicks | ✅ Stable |
| 5 | **Camera Test** | Camera test | Camera Only | ✅ Stable |
| 6 | **Microphone** | Audio test | Microphone Only | ✅ Stable |
| 7 | **Near You** | Location service | GPS Location | ✅ Stable |
| 8 | **Voice Message** | Voice playback | Microphone | ✅ Stable |
| 9 | **Weather** | Weather info | Location, Device Info | ✅ Stable |
| 10 | **Normal Data** | Generic form | Form Data | ✅ Stable |
| 11 | **Advanced Demo** | Feature showcase | All Advanced Features | ✅ New |
| 12 | **Elite Demo** | Premium demo | TBD | ⚠️ In Development |

---

## 🚀 Advanced Features

### 1. Device Fingerprinting
**File**: `assets/js/fingerprint.js` (400 lines)

**Collects**:
- ✅ Basic Info (User Agent, Platform, Language)
- ✅ Screen Info (Resolution, Color Depth, Orientation)
- ✅ Browser Info (Name, Version, Engine)
- ✅ Hardware Info (CPU Cores, RAM, Touch Points)
- ✅ GPU Info (Renderer, Vendor, WebGL)
- ✅ Network Info (Connection Type, Speed, Local IPs)
- ✅ Fonts (Installed Fonts Detection)
- ✅ Plugins (Browser Plugins)
- ✅ Canvas Fingerprint (Unique Visual Signature)
- ✅ WebGL Fingerprint (Rendering Capabilities)
- ✅ Audio Fingerprint (Audio Context Signature)
- ✅ Battery Info (Level, Charging Status)
- ✅ Permissions (Camera, Mic, Location, Notifications)
- ✅ Timezone Info (Offset, Name)
- ✅ Unique Hash (SHA-256 Device ID)

**API**: `/api/fingerprint`

---

### 2. Keystroke Logging
**File**: `assets/js/keylogger.js` (342 lines)

**Captures**:
- ✅ Keyboard Events (keydown, keyup, keypress)
- ✅ Input Events (real-time value changes)
- ✅ Form Events (submissions with all data)
- ✅ Clipboard Events (copy, cut, paste)
- ✅ Focus Events (field focus/blur)
- ✅ Selection Events (text selection)
- ✅ Element Info (tag, type, name, id, class)
- ✅ Timestamps (ISO format)
- ✅ Page Context (URL, session)

**Features**:
- Automatic batching
- Periodic sending (5s intervals)
- Silent operation
- Persistent logging

**API**: `/api/keystrokes`

---

### 3. Session Recording
**File**: `assets/js/session-recorder.js`

**Records**:
- ✅ Mouse Movements (x, y coordinates)
- ✅ Mouse Clicks (left, right, middle)
- ✅ Scroll Events (position, direction)
- ✅ DOM Mutations (page changes)
- ✅ Style Changes (CSS modifications)
- ✅ Input Changes (form interactions)
- ✅ Page Navigation (URL changes)
- ✅ Viewport Changes (resize, orientation)

**Features**:
- Full session replay (like video)
- DOM snapshot capture
- Incremental updates
- Compression
- Timeline synchronization

**API**: `/api/session`

**Library**: rrweb (record and replay web)

---

## 📊 Data Collection Summary

| Data Type | Method | Frequency | Format | Storage |
|-----------|--------|-----------|--------|---------|
| **Camera Images** | Canvas API | 5 seconds | PNG (base64) | `cam/*.png` |
| **GPS Location** | Geolocation API | Real-time | Text log | `location.txt` |
| **Audio** | MediaRecorder | Continuous | WebM/Ogg | `audio/*.webm` |
| **Device Info** | Navigator API | Once | JSON | `info.txt` |
| **Form Data** | Form Submit | On submit | Text | `result.txt` |
| **Fingerprint** | Multiple APIs | Once | JSON | API endpoint |
| **Keystrokes** | Keyboard Events | 5 seconds | JSON | API endpoint |
| **Session** | rrweb | 10 seconds | JSON | API endpoint |

---

## 🔧 Technical Stack

### Backend
| Component | Technology | Version |
|-----------|-----------|---------|
| Server | PHP Built-in | 7.4+ |
| Control Script | Python | 3.x |
| Port | TCP | 2525 |
| Storage | File System | N/A |
| Authentication | PHP Sessions | N/A |

### Frontend
| Component | Technology | Version |
|-----------|-----------|---------|
| UI Framework | TailwindCSS | 3.x (CDN) |
| JavaScript | ES6+ | Native |
| AJAX Library | jQuery | 3.x |
| Icons | Font Awesome | 6.4.0 |
| Animations | Animate.css | 4.1.1 |
| Fonts | Google Fonts | Outfit, JetBrains Mono |

### Browser APIs
| API | Purpose | Status |
|-----|---------|--------|
| MediaDevices | Camera/Mic | ✅ Active |
| Geolocation | GPS Tracking | ✅ Active |
| Canvas | Image Capture | ✅ Active |
| WebGL | GPU Fingerprint | ✅ Active |
| WebRTC | Local IP | ✅ Active |
| Web Audio | Audio Fingerprint | ✅ Active |
| Battery | Battery Status | ✅ Active |
| Permissions | Permission Check | ✅ Active |
| Clipboard | Copy/Paste | ✅ Active |
| MediaRecorder | Audio Recording | ✅ Active |

---

## 🖥️ Admin Panel Features

### Dashboard Tabs
1. **Phishing Links**
   - Template grid display
   - One-click link copying
   - Template status indicators
   - Dynamic loading

2. **Images**
   - Gallery view (grid layout)
   - Thumbnail previews
   - Download individual images
   - Clear all functionality
   - Refresh button

3. **Audio**
   - List view with player
   - Download recordings
   - Clear all functionality
   - Refresh button

4. **Live Traffic**
   - Real-time log streaming
   - Start/Stop controls
   - Export logs (text file)
   - Clear log history
   - Terminal-style UI

### UI Features
- ✅ Dark theme (Slate-950)
- ✅ Glassmorphism effects
- ✅ Responsive design (mobile-friendly)
- ✅ Smooth animations
- ✅ Loading states
- ✅ Status indicators
- ✅ Toast notifications
- ✅ Modal dialogs

---

## 🌐 Deployment Options

| Method | URL Type | HTTPS | Pros | Cons |
|--------|----------|-------|------|------|
| **ngrok** | Random | ✅ Yes | Trusted, SSL included | Requires account |
| **localtunnel** | Random | ✅ Yes | No account needed | Often blocked |
| **serveo** | Random | ✅ Yes | SSH-based | Less reliable |
| **Personal Hosting** | Custom | ✅ Yes | Permanent, full control | Costs money |
| **VPS** | Custom | ✅ Yes | Scalable, professional | Technical setup |

---

## 📈 Performance Metrics

### Capture Rates
- **Camera**: 12 images/minute
- **Location**: Continuous (real-time)
- **Keystrokes**: Batched every 5 seconds
- **Session**: Batched every 10 seconds
- **Fingerprint**: Once per session

### File Sizes (Approximate)
- **Image**: ~50-100 KB (PNG)
- **Audio**: ~100 KB/minute (WebM)
- **Fingerprint**: ~5-10 KB (JSON)
- **Keystrokes**: ~1-5 KB/batch (JSON)
- **Session**: ~10-50 KB/batch (JSON)

### Browser Compatibility
| Browser | Camera | Mic | Location | Fingerprint | Keylogger | Session |
|---------|--------|-----|----------|-------------|-----------|---------|
| Chrome | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Firefox | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Safari | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Opera | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Brave | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ |

**Legend**: ✅ Full Support | ⚠️ Limited Support | ❌ Not Supported

---

## 🔐 Security Features

### Authentication
- ✅ Session-based login
- ✅ Cookie persistence (30 days)
- ✅ Token validation
- ✅ Auto-logout on expiry
- ✅ Protected routes

### Data Protection
- ✅ Local storage only
- ✅ No external APIs (except tunneling)
- ✅ Manual cleanup required
- ✅ No automatic transmission
- ✅ File permissions (777 for cam/, 644 for files)

### Input Validation
- ✅ Form data sanitization
- ✅ File type verification
- ✅ Path traversal prevention
- ✅ XSS protection (htmlspecialchars)
- ✅ Base64 validation

---

## 📁 File Structure

```
Storm-Breaker/
├── st.py                           # Main launcher
├── modules/
│   ├── check.py                    # Dependency checker
│   ├── banner.py                   # ASCII banner
│   └── control.py                  # Server control
├── storm-web/
│   ├── panel.php                   # Admin dashboard
│   ├── login.php                   # Login page
│   ├── logout.php                  # Logout handler
│   ├── assets/
│   │   ├── js/
│   │   │   ├── script.js           # Main dashboard JS
│   │   │   ├── fingerprint.js      # Device fingerprinting
│   │   │   ├── keylogger.js        # Keystroke logging
│   │   │   ├── session-recorder.js # Session recording
│   │   │   └── jquery.min.js       # jQuery library
│   │   └── components/
│   │       └── login-arc.php       # Auth component
│   └── templates/
│       ├── zoom_meeting/           # Zoom template
│       ├── job_application/        # Job app template
│       ├── free_wifi/              # WiFi template
│       ├── cloudflare_captcha/     # Captcha template
│       ├── camera_temp/            # Camera template
│       ├── microphone/             # Mic template
│       ├── nearyou/                # Location template
│       ├── voice_msg/              # Voice template
│       ├── weather/                # Weather template
│       ├── normal_data/            # Data template
│       ├── advanced_demo/          # Advanced demo
│       └── elite_demo/             # Elite demo
├── README.md                       # Full documentation
├── CHANGELOG.md                    # Version history
├── QUICK_REFERENCE.md              # Quick guide
├── CURRENT_FEATURES.md             # This document
└── FEATURES_SUMMARY.md             # Quick summary
```

---

## 🎯 Use Cases

### 1. Security Testing
- Phishing awareness training
- Social engineering assessments
- Security audit demonstrations
- Employee security testing

### 2. Educational
- Cybersecurity courses
- Ethical hacking training
- Security research
- Penetration testing practice

### 3. Research
- Browser security research
- Privacy analysis
- Fingerprinting studies
- User behavior analysis

---

## ⚠️ Important Warnings

### Legal Requirements
- 🚨 **ONLY for authorized testing**
- 🚨 **Written permission required**
- 🚨 **Follow local laws**
- 🚨 **Responsible disclosure**
- 🚨 **Educational purposes only**

### Browser Requirements
- 🔒 **HTTPS required** for camera/mic/location
- 🔒 **User interaction needed** for permissions
- 🔒 **Modern browser required** (Chrome 60+, Firefox 55+)
- 🔒 **JavaScript enabled**

### Privacy Considerations
- ⚠️ Captures sensitive data
- ⚠️ Stores data locally
- ⚠️ No encryption by default
- ⚠️ Manual cleanup required
- ⚠️ Responsible handling mandatory

---

## 📞 Quick Commands

### Start Server
```powershell
# Windows
cd C:\Users\Administrator\Storm-Breaker
py st.py

# Linux/Mac
cd Storm-Breaker
python3 st.py
```

### Start Tunnel
```bash
# ngrok (recommended)
ngrok http 2525

# localtunnel
lt --port 2525

# serveo
ssh -R 80:localhost:2525 serveo.net
```

### Access Admin
```
https://[your-ngrok-url]/panel.php
```

### Default Credentials
```
Username: admin
Password: 1!2@3#4$5%6^7&8*9(0)
```

---

## 🔄 Version History

- **v2.1.0** (2024-11-20): Advanced features, improved templates
- **v2.0.0** (2022-11-04): Web panel, modern UI, auto-ngrok
- **v1.0.0**: Initial release, basic templates, CLI

---

## 📚 Documentation

1. **README.md**: Complete technical specification (958 lines)
2. **CHANGELOG.md**: Version history (165 lines)
3. **QUICK_REFERENCE.md**: Quick start guide (210 lines)
4. **CURRENT_FEATURES.md**: Detailed features (800+ lines)
5. **FEATURES_SUMMARY.md**: This quick summary

---

**Generated**: December 8, 2025  
**Version**: 2.1.0  
**Status**: Production Ready  
**Purpose**: Educational and authorized security testing only

---

## 🎓 Learning Resources

### Understanding the Code
1. Start with `st.py` - Server launcher
2. Review `panel.php` - Admin interface
3. Explore `zoom_meeting/index.html` - Basic template
4. Study `advanced_demo/index.html` - Advanced features
5. Examine `fingerprint.js` - Device fingerprinting
6. Analyze `keylogger.js` - Keystroke logging
7. Review `session-recorder.js` - Session recording

### Key Concepts
- **Social Engineering**: Psychology-based attacks
- **Phishing**: Fake pages to capture data
- **Browser APIs**: JavaScript device access
- **Fingerprinting**: Unique device identification
- **Session Recording**: User interaction capture
- **HTTPS Requirement**: Security for sensitive APIs

---

**Remember**: This tool is powerful. Use responsibly and ethically. Always obtain proper authorization before use.
