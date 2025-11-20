# Storm Breaker - Flask Migration Guide

This is the Flask-based version of Storm Breaker, migrated from PHP to Python/Flask while maintaining full feature parity.

## Quick Start

### Installation

```powershell
cd 'C:\Users\Administrator\Storm-Breaker\storm-web'
py -3 -m pip install -r requirements.txt
```

### Run

```powershell
py .\app.py
```

Access at: `http://127.0.0.1:2525`

**Default Credentials:**
- Username: `admin`
- Password: `1!2@3#4$5%6^7&8*9(0)`

## Features

✅ **Authentication** - Login/logout with session management
✅ **Dashboard** - Phishing links and live traffic logs
✅ **Templates** - Camera, microphone, location, WiFi, CAPTCHA, and more
✅ **Image/Media Capture** - Automatic saving to `images/` folder
✅ **Result Logging** - Each template stores captured data in `result.txt`
✅ **Receiver Endpoint** - Collects results from all templates
✅ **Legacy Compatibility** - Original `.php` endpoints still work

## Project Structure

```
storm-web/
├── app.py                         # Flask application (main entry point)
├── requirements.txt               # Python dependencies (Flask)
├── config.php                     # User credentials
├── check-c.json                   # Session token storage
├── assets/                        # Static files
│   ├── css/                       # Stylesheets
│   ├── js/                        # JavaScript (jQuery, client code)
│   └── images/                    # Captured images folder
├── templates/                     # Phishing templates
│   ├── camera_temp/               # Camera capture template
│   ├── cloudflare_captcha/        # Cloudflare CAPTCHA phishing
│   ├── free_wifi/                 # Free WiFi login template
│   ├── job_application/           # Job application form
│   ├── microphone/                # Microphone access template
│   ├── nearyou/                   # Location-based template
│   ├── normal_data/               # Generic data capture
│   ├── voice_msg/                 # Voice message template
│   ├── weather/                   # Weather template
│   └── zoom_meeting/              # Zoom meeting phishing
├── flask_templates/               # Flask HTML templates
│   ├── login.html                 # Login page (Jinja2)
│   └── panel.html                 # Dashboard (Jinja2)
└── log/                           # Logs directory
```

## API Endpoints

### Authentication
- `GET/POST /login` - Login page and authentication
- `GET /logout` - Clear session and logout
- `GET /login.php` - Legacy endpoint (redirects to `/login`)
- `GET /logout.php` - Legacy endpoint (redirects to `/logout`)

### Dashboard
- `GET /panel` - Control panel
- `GET /panel.php` - Legacy endpoint (redirects to `/panel`)

### Template Management
- `GET /list_templates` - List template folders as JSON
- `GET /list_templates.php` - Legacy endpoint
- `GET /t/<name>/` - Serve template's `index.html`
- `POST /t/<name>/handler` - Capture form data → save to `result.txt`
- `POST /t/<name>/post` - Handle media uploads (images, audio)
- `POST /t/<name>/handler.php` - Legacy endpoint
- `POST /t/<name>/post.php` - Legacy endpoint

### Data Collection
- `POST /receiver` - Collect all results from templates
- `POST /receiver.php` - Legacy endpoint

### Assets
- `GET /assets/<path>` - Serve CSS, JS, fonts, etc.

## Configuration

Edit `config.php` to add users:

```php
$CONFIG = array (
    "admin" => [
        "fullname" => "Admin", 
        "password" => "1!2@3#4$5%6^7&8*9(0)",
    ], 
);
```

## How It Works

1. **User logs in** → Session created, token stored in `check-c.json`
2. **Dashboard loads** → Displays links to all phishing templates
3. **Client opens template** → Browser loads phishing page
4. **Data captured** → JavaScript sends results via POST to `/t/<name>/handler` or `/t/<name>/post`
5. **Results stored** → Each template folder gets a `result.txt` file
6. **Dashboard polls receiver** → Every 2 seconds, fetches new results via `/receiver`
7. **Logs displayed** → Dashboard shows captured data in real-time

## Migration Details

### What Changed
- **Backend**: PHP → Flask (Python web framework)
- **Routes**: All PHP endpoints mapped to Flask routes
- **Sessions**: Flask session management (replaces PHP `$_SESSION`)
- **File I/O**: Python file operations (replaces PHP `file_get_contents`)
- **Templates**: Flask Jinja2 templates for HTML generation

### Backward Compatibility
All original `.php` URLs are still supported:
- `/login.php` works → calls Flask `/login`
- `/receiver.php` works → calls Flask `/receiver`
- Existing clients need no changes

## Remote Access (ngrok)

To expose locally to the internet:

```powershell
cd 'C:\Users\Administrator\Downloads\ngrok-v3-stable-windows-adev64'
.\ngrok.exe http 2525
```

Your public URL will be displayed (e.g., `https://xxxxx.ngrok-free.app`)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 2525 in use** | Edit `app.py`, change `port=2525` to another port |
| **Flask not found** | Run: `py -m pip install Flask` |
| **Images not saving** | Ensure `images/` folder exists or let Flask create it |
| **Templates not showing** | Check `templates/` folder has subdirectories (not just HTML files) |
| **Login fails** | Verify credentials in `config.php` |

## Production Deployment

Use Gunicorn or uWSGI instead of Flask dev server:

```powershell
py -m pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:2525 app:app
```

## Additional Notes

- **Database**: No database. All data stored in `.txt` files
- **Sessions**: In-memory, uses cookies for persistence
- **Security**: For authorized testing only. Use in controlled environments
- **Logging**: Each template maintains its own `result.txt` file
- **Cleanup**: Delete `result.txt` files to clear old data

## Original Project

Based on: https://github.com/ultrasecurity/Storm-Breaker
