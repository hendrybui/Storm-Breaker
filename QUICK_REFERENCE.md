# Storm-Breaker Quick Reference Guide

## 🚀 Quick Start Commands

### Windows:
```powershell
# Terminal 1 - Start Server
cd C:\Users\Administrator\Storm-Breaker
py st.py

# Terminal 2 - Start Tunnel (ngrok)
cd C:\Users\Administrator\Downloads\ngrok-v3-stable-windows-amd64
ngrok http 2525
```

### Linux/Mac:
```bash
# Terminal 1 - Start Server
cd Storm-Breaker
python3 st.py

# Terminal 2 - Start Tunnel
ngrok http 2525
```

---

## 🔐 Default Credentials

- **Username**: `admin`
- **Password**: `1!2@3#4$5%6^7&8*9(0)`

Change in: `storm-web/config.php`

---

## 📋 Available Templates

| Template | Purpose | Captures |
|----------|---------|----------|
| **zoom_meeting** | Zoom meeting join page | Camera, Mic, Device Info |
| **job_application** | Job opportunity form | Camera, Location, Form Data |
| **free_wifi** | WiFi login portal | Location, Device Info |
| **cloudflare_captcha** | CAPTCHA verification | Device Info |
| **camera_temp** | Camera test | Camera only |
| **microphone** | Microphone test | Microphone only |
| **nearyou** | Location service | Location only |
| **voice_msg** | Voice message | Microphone |
| **weather** | Weather service | Location, Device Info |
| **normal_data** | Generic form | Form Data |

---

## 📂 Data Storage Locations

```
storm-web/templates/[template_name]/
├── cam/              # Captured images
├── location.txt      # GPS coordinates
├── result.txt        # Form submissions
└── info.txt          # Device information
```

---

## 🔧 Common Issues & Solutions

### Issue: Browser blocks permissions
**Solution**: 
- Use ngrok (more trusted than localtunnel)
- Click "Enable Camera & Microphone" button
- Manually allow in browser settings

### Issue: "Connection refused" error
**Solution**: 
- Start `py st.py` BEFORE ngrok/localtunnel
- Check if port 2525 is already in use

### Issue: Template not loading
**Solution**:
- Clear browser cache
- Check PHP server is running
- Verify tunnel URL is accessible

---

## 🌐 Tunneling Options

### ngrok (Recommended)
```bash
ngrok http 2525
# Provides: https://[random].ngrok.io
# Pros: Trusted by browsers, SSL included
# Cons: Requires account for long sessions
```

### localtunnel
```bash
lt --port 2525
# Provides: https://[random].loca.lt
# Pros: No account needed
# Cons: Often blocked by browsers
```

### serveo
```bash
ssh -R 80:localhost:2525 serveo.net
# Provides: https://[random].serveo.net
# Pros: SSH-based, no installation
# Cons: Less reliable
```

---

## 📊 Admin Panel Features

1. **Dashboard** - Overview of all templates
2. **Template Selection** - Choose and activate templates
3. **View Logs** - See captured data in real-time
4. **Download Logs** - Export all data as ZIP
5. **Clear Logs** - Delete old data
6. **Link Generator** - Create shareable URLs

---

## 🎯 Best Practices

1. ✅ Always use HTTPS (ngrok provides this)
2. ✅ Test on your own devices first
3. ✅ Get written authorization before testing
4. ✅ Use realistic templates for better success
5. ✅ Monitor logs regularly
6. ✅ Clear logs after each test
7. ❌ Never use for unauthorized access
8. ❌ Don't store sensitive data long-term

---

## 🔄 Workflow

```
1. Start Storm-Breaker server (py st.py)
   ↓
2. Start tunnel (ngrok http 2525)
   ↓
3. Copy public URL
   ↓
4. Login to admin panel
   ↓
5. Select template
   ↓
6. Share generated link
   ↓
7. Monitor captured data
   ↓
8. Download logs
   ↓
9. Clear logs when done
```

---

## 📱 Template URLs

After selecting a template, URLs follow this pattern:

```
https://[your-ngrok-url]/templates/[template_name]/
```

Examples:
- `https://abc123.ngrok.io/templates/zoom_meeting/`
- `https://abc123.ngrok.io/templates/job_application/`
- `https://abc123.ngrok.io/templates/free_wifi/`

---

## 🛡️ Security Tips

- Change default admin password immediately
- Use strong, unique passwords
- Don't share admin panel URL
- Keep logs secure and encrypted
- Delete data after testing
- Follow responsible disclosure practices

---

## 📞 Emergency Stop

To stop Storm-Breaker:

1. Press `CTRL+C` in the terminal running `py st.py`
2. Press `CTRL+C` in the terminal running ngrok
3. Close all browser windows
4. Clear logs if needed

---

## 📖 Additional Resources

- Full README: `README.md`
- Configuration: `storm-web/config.php`
- Templates: `storm-web/templates/`
- Assets: `storm-web/assets/`

---

**Remember**: This tool is for educational and authorized testing only. Always obtain proper authorization before use.
