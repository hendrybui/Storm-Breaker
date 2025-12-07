# Storm-Breaker - Current Features Overview

**Generated**: December 8, 2025  
**Version**: 2.1.0  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Core System Features](#core-system-features)
2. [Admin Panel Features](#admin-panel-features)
3. [Phishing Templates](#phishing-templates)
4. [Advanced Features](#advanced-features)
5. [Data Collection Capabilities](#data-collection-capabilities)
6. [Technical Infrastructure](#technical-infrastructure)

---

## 🎯 Core System Features

### 1. **Python-Based Server Management**
- **File**: `st.py`
- **Port**: 2525 (PHP built-in server)
- **Features**:
  - Automatic PHP server startup
  - Graceful shutdown handling
  - Dependency checking
  - ASCII banner display
  - Cross-platform support (Windows, Linux, macOS)

### 2. **Authentication System**
- **Default Credentials**:
  - Username: `admin`
  - Password: `1!2@3#4$5%6^7&8*9(0)` (or `admin` in some configs)
- **Security**:
  - Session-based authentication
  - Cookie-based login persistence
  - Token generation and validation
  - Protected admin routes

### 3. **Tunneling Support**
- **ngrok** (Recommended): HTTPS tunneling with trusted certificates
- **localtunnel**: Alternative tunneling solution
- **serveo**: SSH-based tunneling option
- All provide HTTPS for browser permission requirements

---

## 🖥️ Admin Panel Features

### Modern Web Interface (`panel.php`)

#### **Dashboard Components**:

1. **System Status Cards**
   - Real-time system status (Active/Inactive)
   - Port information (2525)
   - Session ID tracking
   - Visual status indicators with animations

2. **Tab-Based Navigation**
   - **Phishing Links Tab**: Template selection and link generation
   - **Images Tab**: View captured camera images
   - **Audio Tab**: Access recorded audio files
   - **Live Traffic Tab**: Real-time activity monitoring

3. **Template Management**
   - Grid display of all available templates
   - One-click link copying
   - Template status indicators
   - Dynamic template loading

4. **Data Viewing**
   - Image gallery with thumbnails
   - Audio player integration
   - Download individual files
   - Bulk operations (clear all)

5. **Live Traffic Monitor**
   - Real-time log streaming
   - Start/Stop listening controls
   - Export logs as text file
   - Clear log history
   - Terminal-style interface

#### **UI/UX Features**:
- **Design**: Modern dark theme with glassmorphism
- **Framework**: TailwindCSS for responsive design
- **Fonts**: Outfit (UI), JetBrains Mono (code)
- **Icons**: Font Awesome 6.4.0
- **Animations**: Animate.css integration
- **Colors**: 
  - Primary: Blue (#667eea) to Purple (#764ba2) gradients
  - Background: Slate-950 (#020617)
  - Accents: Emerald (success), Red (danger)

---

## 📱 Phishing Templates

### **1. Zoom Meeting Template** (`zoom_meeting/`)
**Purpose**: Fake Zoom meeting join page

**Features**:
- Authentic Zoom branding and UI
- "Enable Camera & Microphone" button
- Video preview display
- Permission request handling
- Error message display
- Stealth mode (morphs to Google page)

**Captures**:
- Camera images (every 5 seconds)
- Microphone audio
- Device information
- User interactions

**Files**:
- `index.html` - Main template
- `post.php` - Data receiver
- `cam/` - Image storage
- `info.txt` - Device info log

---

### **2. Job Application Template** (`job_application/`)
**Purpose**: Professional job opportunity form

**Features**:
- Realistic job application form
- Multiple input fields (name, email, phone, city)
- CV status selection
- Skills and work preference inputs
- Persistent background tracking
- Continues after form submission

**Captures**:
- Form data (all fields)
- Camera images (continuous)
- GPS location (real-time tracking)
- Device information

**Files**:
- `index.html` - Application form
- `submit.php` - Form handler
- `capture.php` - Camera capture endpoint
- `location.php` - GPS data handler
- `result.txt` - Form submissions
- `cam/` - Captured images
- `location.txt` - GPS coordinates

---

### **3. Free WiFi Template** (`free_wifi/`)
**Purpose**: Public WiFi login portal

**Captures**:
- Device information
- Location data
- Network information

**Files**:
- `index.html` - WiFi portal
- `login.php` - Login handler
- `info.txt` - Device logs

---

### **4. Cloudflare Captcha Template** (`cloudflare_captcha/`)
**Purpose**: Fake CAPTCHA verification

**Features**:
- Authentic Cloudflare styling
- Interactive checkbox
- Loading animations
- Verification flow

**Captures**:
- Device information
- Click interactions
- Browser fingerprint

**Files**:
- `index.html` - CAPTCHA page
- `verify.php` - Verification handler

---

### **5. Camera Test Template** (`camera_temp/`)
**Purpose**: Simple camera functionality test

**Features**:
- Minimal technical interface
- Direct camera access
- Real-time preview

**Captures**:
- Camera images only

---

### **6. Microphone Test Template** (`microphone/`)
**Purpose**: Audio recording test

**Features**:
- Audio waveform visualization
- Recording controls
- Playback functionality

**Captures**:
- Microphone audio recordings

**Files**:
- `index.html` - Audio interface
- `record.php` - Audio handler
- `audio/` - Audio storage

---

### **7. Near You Template** (`nearyou/`)
**Purpose**: Location-based service

**Features**:
- Map interface
- Location permission request
- Distance calculations

**Captures**:
- Precise GPS coordinates
- Location accuracy
- Timestamp data

**Files**:
- `index.html` - Map interface
- `location.php` - Location handler
- `location.txt` - GPS logs

---

### **8. Voice Message Template** (`voice_msg/`)
**Purpose**: Voice message playback prompt

**Features**:
- Messaging app style UI
- Play button interface
- Audio permission request

**Captures**:
- Microphone recordings

---

### **9. Weather Template** (`weather/`)
**Purpose**: Weather information service

**Features**:
- Weather app interface
- Location-based weather
- Temperature display

**Captures**:
- Location data
- Device information

---

### **10. Normal Data Template** (`normal_data/`)
**Purpose**: Generic data collection form

**Features**:
- Simple form interface
- Multiple input types
- Basic validation

**Captures**:
- Form data
- Submission timestamps

---

## 🚀 Advanced Features

### **1. Device Fingerprinting** (`fingerprint.js`)

**Comprehensive Data Collection**:

#### Basic Information:
- User Agent
- Platform
- Language
- Cookies enabled
- Do Not Track status
- Online status

#### Screen & Display:
- Screen resolution
- Available screen size
- Color depth
- Pixel ratio
- Orientation
- Touch support

#### Browser Information:
- Browser name and version
- Rendering engine
- Build ID
- Product
- Vendor

#### Hardware Information:
- CPU cores (hardwareConcurrency)
- Device memory (RAM)
- Max touch points

#### GPU Information (WebGL):
- Renderer
- Vendor
- WebGL version
- Supported extensions

#### Network Information:
- Connection type
- Effective type
- Downlink speed
- RTT (Round Trip Time)
- Save data preference
- Local IP addresses (via WebRTC)

#### Font Detection:
- Installed fonts enumeration
- Font rendering fingerprint

#### Browser Plugins:
- Plugin names
- Plugin descriptions
- MIME types

#### Canvas Fingerprinting:
- Canvas rendering hash
- Unique visual signature

#### WebGL Fingerprinting:
- WebGL parameters
- Rendering capabilities

#### Audio Context Fingerprinting:
- Audio processing signature
- Oscillator fingerprint

#### Battery Information:
- Battery level
- Charging status
- Charging time
- Discharging time

#### Permissions:
- Camera permission status
- Microphone permission status
- Geolocation permission status
- Notifications permission status

#### Timezone Information:
- Timezone offset
- Timezone name

#### Unique Hash Generation:
- SHA-256 hash of all fingerprint data
- Unique device identifier

**API Endpoint**: `/api/fingerprint`

---

### **2. Keystroke Logging** (`keylogger.js`)

**Captured Events**:

#### Keyboard Events:
- **keydown**: Key press detection
- **keyup**: Key release detection
- **keypress**: Character input
- Special keys (Ctrl, Alt, Shift, etc.)
- Key combinations

#### Input Events:
- **input**: Real-time value changes
- **change**: Field value changes
- Field names and IDs
- Input types (text, password, email, etc.)
- Current values

#### Form Events:
- **submit**: Form submission capture
- All form field values
- Form action and method
- Form ID and name

#### Clipboard Events:
- **copy**: Copied text
- **cut**: Cut text
- **paste**: Pasted text
- Clipboard data

#### Focus Events:
- **focus**: Field focus
- **blur**: Field blur
- Active element tracking

#### Selection Events:
- **select**: Text selection
- Selected text content
- Selection range

**Data Logged**:
- Timestamp (ISO format)
- Event type
- Key pressed
- Element information (tag, type, name, id, class)
- Element value
- Page URL
- User session info

**Features**:
- Automatic batching
- Periodic sending (configurable interval)
- Silent operation
- No console output
- Persistent logging

**API Endpoint**: `/api/keystrokes`

---

### **3. Session Recording** (`session-recorder.js`)

**Powered by**: rrweb (record and replay web)

**Recorded Interactions**:

#### Mouse Events:
- Mouse movements (x, y coordinates)
- Mouse clicks (left, right, middle)
- Mouse hover states
- Scroll events

#### Page Events:
- DOM mutations
- Style changes
- Input changes
- Page navigation

#### Viewport Events:
- Window resize
- Scroll position
- Viewport changes

#### Media Events:
- Video/audio playback
- Media controls

**Features**:
- **Full Session Replay**: Can be replayed like a video
- **DOM Snapshot**: Initial page state capture
- **Incremental Updates**: Only changes are recorded
- **Compression**: Efficient data storage
- **Privacy Options**: Can mask sensitive data
- **Timestamp Synchronization**: Accurate replay timing

**Data Format**:
- JSON array of events
- Timestamp for each event
- Event type and data
- Session ID

**API Endpoint**: `/api/session`

**Replay Capability**:
- Admin can replay entire user session
- See exactly what user saw and did
- Timeline scrubbing
- Playback speed control

---

### **4. Advanced Demo Template** (`advanced_demo/`)

**Purpose**: Showcase all three advanced features in one page

**Features**:
- Live status indicators for each feature
- Test form with multiple input types
- Real-time feature status updates
- Comprehensive information display

**Active Features**:
1. Device Fingerprinting (auto-collected on load)
2. Keystroke Logging (captures all input)
3. Session Recording (records all interactions)

**Use Case**: Demonstration and testing of advanced capabilities

---

## 📊 Data Collection Capabilities

### **Camera Capture**
- **Method**: Canvas API + getUserMedia
- **Frequency**: Every 5 seconds (configurable)
- **Format**: PNG (base64 encoded)
- **Resolution**: 640x640 (configurable)
- **Storage**: `cam/` folder in each template
- **Naming**: `YYYY-MM-DD_HH-mm-ss_uniqueid.png`
- **Persistence**: Continues in background

### **Location Tracking**
- **Method**: Geolocation API (watchPosition)
- **Frequency**: Real-time updates
- **Data**:
  - Latitude
  - Longitude
  - Accuracy (meters)
  - Timestamp
  - Altitude (if available)
  - Speed (if available)
- **Storage**: `location.txt`
- **Format**: Text log with timestamps

### **Audio Recording**
- **Method**: MediaRecorder API
- **Format**: WebM/Ogg (browser dependent)
- **Storage**: `audio/` folder
- **Features**:
  - Continuous recording
  - Chunk-based storage
  - Waveform visualization

### **Device Information**
- **Basic**: User agent, platform, language
- **Screen**: Resolution, color depth, orientation
- **Hardware**: CPU cores, RAM, GPU
- **Network**: Connection type, speed, IP
- **Browser**: Version, plugins, features
- **Storage**: `info.txt`

### **Form Data**
- **Method**: Form submission interception
- **Data**: All form fields and values
- **Storage**: `result.txt`
- **Format**: Structured text with timestamps

---

## 🔧 Technical Infrastructure

### **Backend**

#### PHP Components:
1. **Server**: PHP 7.4+ built-in server
2. **Session Management**: PHP sessions
3. **File Operations**: file_put_contents, file_get_contents
4. **Data Processing**: JSON encoding/decoding, base64 operations
5. **Authentication**: Cookie-based with token validation

#### Python Components:
1. **Server Control**: `st.py` launcher
2. **Dependency Checking**: `modules/check.py`
3. **Banner Display**: `modules/banner.py`
4. **Process Management**: Subprocess control

### **Frontend**

#### Core Technologies:
- **HTML5**: Semantic markup, modern APIs
- **CSS3**: Flexbox, Grid, animations, gradients
- **JavaScript ES6+**: Async/await, promises, modules
- **jQuery 3.x**: AJAX, DOM manipulation

#### UI Framework:
- **TailwindCSS**: Utility-first CSS via CDN
- **Font Awesome 6.4**: Icon library
- **Animate.css**: Animation library
- **Google Fonts**: Outfit, JetBrains Mono

#### Browser APIs Used:
1. **MediaDevices API**: Camera and microphone access
2. **Geolocation API**: GPS tracking
3. **Canvas API**: Image capture and fingerprinting
4. **WebGL API**: GPU fingerprinting
5. **WebRTC API**: Local IP detection
6. **Web Audio API**: Audio fingerprinting
7. **Battery API**: Battery status
8. **Permissions API**: Permission checking
9. **Clipboard API**: Copy/paste detection
10. **MediaRecorder API**: Audio recording

### **Data Storage**

#### File-Based System:
- **No Database**: All data stored in files
- **Structure**:
  ```
  templates/[template_name]/
  ├── cam/              # Images
  ├── audio/            # Audio files
  ├── location.txt      # GPS logs
  ├── result.txt        # Form data
  └── info.txt          # Device info
  ```

#### Permissions:
- **cam/ folders**: 777 (writable)
- **PHP files**: 644 (readable, executable)
- **Data files**: 644 (readable, writable by PHP)

### **Security Features**

1. **Authentication**:
   - Session-based login
   - Cookie persistence
   - Token validation
   - Auto-logout on session expiry

2. **Data Protection**:
   - Local storage only
   - No external API calls (except tunneling)
   - Manual cleanup required
   - No automatic data transmission

3. **Input Validation**:
   - Form data sanitization
   - File type verification
   - Path traversal prevention
   - XSS protection (htmlspecialchars)

### **Performance Optimizations**

1. **Lazy Loading**: Images and audio loaded on demand
2. **Batch Processing**: Keystrokes sent in batches
3. **Compression**: Session data compressed
4. **Caching**: Browser caching for static assets
5. **Async Operations**: Non-blocking AJAX requests

---

## 📈 Statistics

### Template Count:
- **Total**: 12 templates
- **Basic**: 10 templates
- **Advanced**: 2 templates (advanced_demo, elite_demo)

### Platform Support:
- ✅ Windows 10/11
- ✅ Linux (Ubuntu, Debian, etc.)
- ✅ macOS
- ✅ Android (via Termux)
- ❌ iOS (limited support)

### Browser Compatibility:
- ✅ Chrome/Edge: Excellent
- ✅ Firefox: Good
- ⚠️ Safari: Limited (iOS restrictions)
- ✅ Opera: Good
- ⚠️ Brave: Limited (privacy features block some functionality)

### Data Collection Rates:
- **Camera**: Every 5 seconds
- **Location**: Real-time (continuous)
- **Keystrokes**: Batched every 5 seconds
- **Session**: Every 10 seconds
- **Fingerprint**: Once on page load

---

## 🔄 Workflow

### Standard Operation:

1. **Start Server**: `py st.py` (Port 2525)
2. **Start Tunnel**: `ngrok http 2525`
3. **Access Admin**: `https://[ngrok-url]/panel.php`
4. **Login**: Use admin credentials
5. **Select Template**: Choose from dashboard
6. **Copy Link**: Share template URL
7. **Monitor Data**: View captured data in real-time
8. **Download Logs**: Export data as needed
9. **Clear Logs**: Clean up after testing

### Data Flow:

```
Victim Device
    ↓
Template Page (index.html)
    ↓
JavaScript Capture (camera/location/keystrokes)
    ↓
AJAX POST Request
    ↓
PHP Handler (post.php/submit.php/etc.)
    ↓
File Storage (cam/, location.txt, etc.)
    ↓
Admin Panel (panel.php)
    ↓
Admin Views Data
```

---

## 🎯 Key Differentiators

### What Makes Storm-Breaker Unique:

1. **No Database Required**: Simple file-based storage
2. **Plug and Play**: Works out of the box
3. **Cross-Platform**: Runs on Windows, Linux, macOS
4. **Modern UI**: Professional admin panel
5. **Advanced Features**: Fingerprinting, keylogging, session recording
6. **Persistent Tracking**: Continues after user navigates away
7. **Stealth Mode**: Templates morph to innocent pages
8. **Realistic Templates**: Authentic-looking phishing pages
9. **Real-Time Monitoring**: Live traffic and data viewing
10. **Easy Deployment**: Simple tunneling with ngrok

---

## 📝 Configuration Options

### Customizable Settings:

1. **Admin Credentials**: `storm-web/config.php`
2. **Server Port**: `st.py` (default: 2525)
3. **Capture Interval**: Template JavaScript (default: 5000ms)
4. **Image Quality**: Canvas resolution (default: 640x640)
5. **Send Intervals**: 
   - Keystrokes: 5 seconds
   - Session: 10 seconds
   - Camera: 5 seconds
6. **Template Branding**: HTML/CSS customization

---

## 🚨 Important Notes

### Legal & Ethical:
- ⚠️ **ONLY for authorized testing**
- ⚠️ **Obtain written permission**
- ⚠️ **Follow local laws**
- ⚠️ **Educational purposes only**

### Browser Limitations:
- 🔒 **HTTPS required** for camera/mic/location
- 🔒 **User interaction needed** for permissions
- 🔒 **Safari iOS** has strict limitations
- 🔒 **Brave browser** blocks many features

### Best Practices:
- ✅ Always use HTTPS (ngrok provides this)
- ✅ Test on own devices first
- ✅ Clear logs after each test
- ✅ Use strong admin passwords
- ✅ Monitor captured data regularly
- ✅ Delete sensitive data promptly

---

## 📚 Documentation Files

1. **README.md**: Complete technical specification
2. **CHANGELOG.md**: Version history and updates
3. **QUICK_REFERENCE.md**: Quick start guide
4. **CURRENT_FEATURES.md**: This document

---

## 🔮 Future Enhancements (Planned)

### High Priority:
- [ ] Multi-language support
- [ ] Custom template builder
- [ ] Real-time notifications
- [ ] Data analytics dashboard
- [ ] Mobile admin app

### Medium Priority:
- [ ] Two-factor authentication
- [ ] RESTful API
- [ ] Webhook support
- [ ] Scheduled cleanup
- [ ] Encrypted storage

### Low Priority:
- [ ] Video recording
- [ ] Screen recording
- [ ] Template marketplace

---

**Last Updated**: December 8, 2025  
**Version**: 2.1.0  
**Maintained By**: UltraSecurity  
**Purpose**: Educational and authorized security testing only
