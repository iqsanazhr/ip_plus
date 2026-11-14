"""iPhone Link - Native Window Management & WebView2 Initialization."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

from .config import (
    REPO_ROOT,
    DEFAULT_HOST,
    DEFAULT_PORT,
    PORTRAIT_WIDTH,
    PORTRAIT_HEIGHT,
    MIN_WIDTH,
    MIN_HEIGHT,
    BG_DARK,
)


def resolve_webview_storage_path() -> str:
    """Resolve isolated WebView2 UserDataFolder path."""
    target_dir = REPO_ROOT / ".pane_webview_storage"
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        return str(target_dir)
    except Exception:
        fallback = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "iPhoneLink" / "WebView2"
        fallback.mkdir(parents=True, exist_ok=True)
        return str(fallback)


def create_app_window(api: Any, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> Any:
    """Create the pywebview frameless window configured with per-pixel alpha transparency."""
    import webview

    url = f"http://{host}:{port}/?t={int(time.time())}"

    # Calculate center of primary screen for initial placement
    spawn_x, spawn_y = None, None
    if sys.platform == "win32":
        try:
            import ctypes
            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            spawn_x = max(0, (sw - PORTRAIT_WIDTH) // 2)
            spawn_y = max(0, (sh - PORTRAIT_HEIGHT) // 2)
        except Exception:
            pass

    # Critical: transparent=True enables per-pixel alpha channel in WebView2 & WinForms
    window = webview.create_window(
        title="ip+",
        url=url,
        js_api=api,
        width=PORTRAIT_WIDTH,
        height=PORTRAIT_HEIGHT,
        x=spawn_x,
        y=spawn_y,
        frameless=True,
        easy_drag=False,
        on_top=True,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        background_color=BG_DARK,
        transparent=True,
    )
    return window
