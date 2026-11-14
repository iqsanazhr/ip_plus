"""iPhone Link - Native GUI & Window Subsystem."""

from __future__ import annotations

import os
import sys
import time

from .config import DEFAULT_HOST, DEFAULT_PORT, REPO_ROOT
from .dwm import apply_dwm_transparency, reapply_dwm_rounded_corners, find_webview_controls, apply_phone_window_region
from .real_phone import calculate_real_phone_dimensions
from .process import (
    ensure_backend_server_running,
    shutdown_backend_server,
    make_child_job_object,
)
from .window import resolve_webview_storage_path, create_app_window
from .api import WindowApi

# Aliases for backward compatibility with older tests and modules
_ensure_backend_server_running = ensure_backend_server_running
_resolve_webview_storage_path = resolve_webview_storage_path
_find_webview_controls = find_webview_controls


def _auto_unblock_zone_identifiers() -> None:
    """Auto-unblock NTFS Zone.Identifier streams on Windows."""
    if os.name != "nt":
        return
    os.environ.setdefault("COMPlus_LoadFromRemoteSources", "1")
    os.environ.setdefault("PYTHONNET_PYDLL", "")
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        delete_file_w = kernel32.DeleteFileW
        delete_file_w.argtypes = [ctypes.c_wchar_p]
        delete_file_w.restype = ctypes.c_int
    except Exception:
        pass


def main() -> None:
    """Main launcher entry point for the native GUI window."""
    _auto_unblock_zone_identifiers()

    host = DEFAULT_HOST
    port = DEFAULT_PORT

    for i, arg in enumerate(sys.argv):
        if arg == "--host" and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
        elif arg == "--port" and i + 1 < len(sys.argv):
            try:
                port = int(sys.argv[i + 1])
            except ValueError:
                pass

    ensure_backend_server_running(host=host, port=port)

    api = WindowApi(host=host, port=port)
    window = create_app_window(api, host=host, port=port)
    api.set_window(window)

    # Initialize System Tray
    try:
        from handset.tray import TrayIcon
        tray = TrayIcon(
            on_show=lambda: api.restore_from_tray(),
            on_hide=lambda: api.minimize_to_tray(),
            on_toggle=lambda: api.toggle_tray_window(),
            on_quit=lambda: api.close(),
        )
        tray.start(wait_ready=0.5)
    except Exception as e:
        print("[iPhoneLink Tray] Tray init failed (non-critical):", e)

    storage_path = resolve_webview_storage_path()
    try:
        import webview
        webview.start(
            debug=False,
            private_mode=False,
            storage_path=storage_path,
        )
    finally:
        shutdown_backend_server()
        os._exit(0)


__all__ = [
    "main",
    "WindowApi",
    "create_app_window",
    "ensure_backend_server_running",
    "shutdown_backend_server",
    "resolve_webview_storage_path",
    "_ensure_backend_server_running",
    "_resolve_webview_storage_path",
    "_find_webview_controls",
]
