"""Database seeders."""

import json
import os
import sys
from pathlib import Path

# Make the repo importable when this file is run directly.
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "backend"))
