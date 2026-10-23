# Localhost-only launcher for storm-web/app.py (test run).
# The fork's app.py hardcodes host='0.0.0.0', which would expose the
# admin/admin panel and its /api/terminal web shell to the LAN.
import os
import sys

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storm-web')
sys.path.insert(0, BASE)
os.chdir(BASE)

import app  # noqa: E402  (storm-web/app.py)

app.db.init_database()
app.app.run(host='127.0.0.1', port=2525, debug=False)
