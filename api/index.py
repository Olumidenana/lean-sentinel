import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parent

for p in [CURRENT_DIR, ROOT_DIR]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from lean_sentinel.web.server import app
