"""Native Frameless Launcher for iPhone Link using pywebview.

Modular facade delegating to the `handset.gui` package adhering to clean industry standards.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from handset.gui import (
    main,
    WindowApi,
    create_app_window,
    ensure_backend_server_running,
    shutdown_backend_server,
    resolve_webview_storage_path,
    _ensure_backend_server_running,
    _resolve_webview_storage_path,
    _find_webview_controls,
    apply_phone_window_region,
)

if __name__ == "__main__":
    if "--server-child" in sys.argv or "--server-only" in sys.argv:
        from handset.server import main as server_main
        server_main()
    else:
        main()
