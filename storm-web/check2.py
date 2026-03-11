import urllib.request
import sys

# Test basic connectivity first
try:
    r = urllib.request.urlopen('http://127.0.0.1:2525/')
    print("Server is reachable! Status:", r.status)
except Exception as e:
    print("Server NOT reachable:", e)
    sys.exit(1)

# Now check the JS file directly
try:
    r = urllib.request.urlopen('http://127.0.0.1:2525/static/js/evasion_ui.js')
    content = r.read().decode()
    print("evasion_ui.js: Status", r.status, "Size:", len(content), "bytes")
    print("Contains EvasionUI:", "EvasionUI" in content)
except Exception as e:
    print("evasion_ui.js:", e)

# Read the template file directly from disk  
import os
tmpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_templates', 'panel.html')
with open(tmpl_path, 'r', encoding='utf-8') as f:
    html = f.read()

print("\n=== Template file on disk ===")
print('tab-evasion found:', 'id="tab-evasion"' in html)
print('tab-threat-intel found:', 'id="tab-threat-intel"' in html)  
print('tab-session-hijack found:', 'id="tab-session-hijack"' in html)
print('tab-pivot found:', 'id="tab-pivot"' in html)
print()
print('evasion-tab found (OLD):', 'id="evasion-tab"' in html)
print('session-hijack-tab found (OLD):', 'id="session-hijack-tab"' in html)
print()
print('evasion_ui.js in template:', 'evasion_ui.js' in html)
print('EvasionUI.init() in template:', 'EvasionUI.init()' in html)
print('SessionHijackerUI.init() in template:', 'SessionHijackerUI.init()' in html)
print('evasion-dashboard in template:', 'evasion-dashboard' in html)
print('session-hijack-dashboard in template:', 'session-hijack-dashboard' in html)
