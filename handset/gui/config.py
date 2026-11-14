"""iPhone Link - Configuration & Constants for GUI & Window Management."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Repository root resolution
if not getattr(sys, "frozen", False):
    REPO_ROOT = Path(__file__).resolve().parent.parent.parent
else:
    REPO_ROOT = Path(sys.executable).resolve().parent

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

# Default physical dimensions
PORTRAIT_WIDTH = 346
PORTRAIT_HEIGHT = 832
MIN_WIDTH = 240
MIN_HEIGHT = 360

DRAWER_WIDTH = 360
LANDSCAPE_HEIGHT = 468
LANDSCAPE_WIDTH_NO_DRAWER = 840
LANDSCAPE_WIDTH_DRAWER = 1200

# Theme Background Colors
BG_DARK = "#10141e"
BG_LIGHT = "#eaf0f8"
