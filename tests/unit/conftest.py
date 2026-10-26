"""Put ``storm-web/`` on sys.path so ``app.*`` (and sibling ``database``)
are importable from unit tests, exactly as the char suite does."""
import sys
from pathlib import Path

STORM_WEB = Path(__file__).resolve().parents[2] / "storm-web"
if str(STORM_WEB) not in sys.path:
    sys.path.insert(0, str(STORM_WEB))
