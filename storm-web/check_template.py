import urllib.request

try:
    req = urllib.request.Request('http://127.0.0.1:2525/panel', headers={'Cookie': 'session=test'})
    r = urllib.request.urlopen(req)
    html = r.read().decode('utf-8', 'ignore')
    
    # Check for new IDs (correct)
    print("=== Checking served HTML for tab div IDs ===")
    id_new_evasion = 'id="tab-evasion"'
    id_new_threat = 'id="tab-threat-intel"'
    id_new_session = 'id="tab-session-hijack"'
    id_new_pivot = 'id="tab-pivot"'
    id_old_evasion = 'id="evasion-tab"'
    id_old_threat = 'id="threat-intel-tab"'
    id_old_session = 'id="session-hijack-tab"'
    id_old_pivot = 'id="pivot-tab"'
    
    print("tab-evasion found:", id_new_evasion in html)
    print("tab-threat-intel found:", id_new_threat in html)
    print("tab-session-hijack found:", id_new_session in html)
    print("tab-pivot found:", id_new_pivot in html)
    
    print()
    print("evasion-tab found (OLD/WRONG):", id_old_evasion in html)
    print("threat-intel-tab found (OLD/WRONG):", id_old_threat in html)
    print("session-hijack-tab found (OLD/WRONG):", id_old_session in html)
    print("pivot-tab found (OLD/WRONG):", id_old_pivot in html)
    
    print()
    print("evasion_ui.js loaded:", "evasion_ui.js" in html)
    print("threat_intel_ui.js loaded:", "threat_intel_ui.js" in html)
    print("session_hijacker_ui.js loaded:", "session_hijacker_ui.js" in html)
    print("pivot_engine_ui.js loaded:", "pivot_engine_ui.js" in html)
    
    print()
    print("evasion-dashboard div:", "evasion-dashboard" in html)
    print("session-hijack-dashboard div:", "session-hijack-dashboard" in html)
    
    print()
    print("EvasionUI.init() in script:", "EvasionUI.init()" in html)
    print("SessionHijackerUI.init() in script:", "SessionHijackerUI.init()" in html)
    
except urllib.error.HTTPError as e:
    if e.code == 302:
        print(f"Got redirect (302) to: {e.headers.get('Location')}")
        print("Panel requires login - checking template file directly instead")
    else:
        print(f"HTTP Error: {e.code}")
except Exception as e:
    print(f"Error: {e}")
