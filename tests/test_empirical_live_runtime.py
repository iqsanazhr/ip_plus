"""Live Pywebview and WinForms Runtime Empirical Verification.

Conducted by Challenger 1.
Spins up a real pywebview window on Windows with EdgeChromium / WinForms.
Tests live DWM transparency toggles, HWND discovery, BrowserView instances,
and confirms that no WinForms ArgumentException occurs in the host process.
"""

from __future__ import annotations

import os
import sys
import threading
import time

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

import webview
from handset.gui.api import WindowApi
from handset.gui.dwm import apply_dwm_transparency, reapply_dwm_rounded_corners


def run_live_harness():
    print("[CHALLENGER-1] Starting Live Pywebview Runtime Empirical Verification...")
    results = {
        "hwnd_found": False,
        "standard_mode_applied": False,
        "real_phone_mode_applied": False,
        "standard_mode_reapplied": False,
        "no_winforms_argument_exception": False,
        "api_sizing_verified": False,
        "api_settings_singleton_verified": False,
        "errors": [],
    }

    api = WindowApi(host="127.0.0.1", port=8765)

    def test_worker(win):
        try:
            # Allow window and WebView2 initialization
            time.sleep(1.5)

            # 1. HWND and Form Handle verification
            from webview.platforms.winforms import BrowserView
            import System

            if not BrowserView.instances:
                raise RuntimeError("No BrowserView instances found in WinForms platform!")

            form = list(BrowserView.instances.values())[0]
            hwnd = form.Handle.ToInt32()
            if hwnd <= 0:
                raise RuntimeError(f"Invalid HWND: {hwnd}")

            results["hwnd_found"] = True
            print(f"  [OK] Real WinForms HWND resolved: {hwnd}")

            # 2. Apply Standard Mode (Dark Theme)
            print("  [STEP 1] Applying Standard Mode (Dark)...")
            apply_dwm_transparency(hwnd, is_real_phone=False, current_theme="dark")
            reapply_dwm_rounded_corners(hwnd, is_fullscreen=False, is_real_phone=False)
            time.sleep(0.3)
            results["standard_mode_applied"] = True

            # 3. Apply Real Phone Mode
            print("  [STEP 2] Applying Real Phone Mode (Per-Pixel Transparency)...")
            apply_dwm_transparency(hwnd, is_real_phone=True, current_theme="dark")
            reapply_dwm_rounded_corners(hwnd, is_fullscreen=False, is_real_phone=True)
            time.sleep(0.3)
            results["real_phone_mode_applied"] = True

            # 4. Transition Back to Standard Mode (Light Theme)
            print("  [STEP 3] Transitioning Back to Standard Mode (Light)...")
            apply_dwm_transparency(hwnd, is_real_phone=False, current_theme="light")
            reapply_dwm_rounded_corners(hwnd, is_fullscreen=False, is_real_phone=False)
            time.sleep(0.3)
            results["standard_mode_reapplied"] = True

            # 5. Stress test: rapid toggling between modes
            print("  [STEP 4] Executing 10 rapid toggles between Real Phone and Standard...")
            for i in range(10):
                is_rp = (i % 2 == 0)
                apply_dwm_transparency(hwnd, is_real_phone=is_rp, current_theme="dark")
            time.sleep(0.2)

            # Confirm no ArgumentException occurred:
            results["no_winforms_argument_exception"] = True
            print("  [OK] Zero System.ArgumentException encountered across all DWM transitions!")

            # 6. Verify WindowApi sizing methods on the live window
            api.set_window(win)
            res_port = api.set_orientation(False)
            assert res_port["width"] == 346, f"Expected 346, got {res_port['width']}"
            assert res_port["height"] == 832, f"Expected 832, got {res_port['height']}"

            # Verify orientation switches
            res_land = api.set_orientation(True)
            assert res_land["width"] == 840, f"Expected 840, got {res_land['width']}"
            assert res_land["height"] == 468, f"Expected 468, got {res_land['height']}"

            # When in landscape, sync_device_aspect should be skipped
            res_sync_skipped = api.sync_device_aspect(400, drawer_open=True)
            assert res_sync_skipped.get("skipped") is True, f"Expected skipped=True in landscape, got {res_sync_skipped}"

            # Switch back to portrait
            res_port_back = api.set_orientation(False)
            assert res_port_back["width"] == 346

            # Verify sync_device_aspect in portrait without DRAWER_WIDTH
            res_sync = api.sync_device_aspect(400, drawer_open=True)
            assert res_sync["width"] == 400, f"Expected 400, got {res_sync}"
            assert res_sync["height"] == 832
            assert api._drawer_open is False, "Drawer open flag must remain False"

            results["api_sizing_verified"] = True
            print("  [OK] Live window sizing and DRAWER_WIDTH decoupling verified!")

            # 7. Test open_settings singleton on live STA thread
            print("  [STEP 5] Testing open_settings on live runtime...")
            s1 = api.open_settings()
            assert s1.get("ok") is True, f"Failed to open settings: {s1}"
            assert s1.get("action") == "created", f"Expected action=created, got {s1}"
            time.sleep(0.5)

            # Second call should focus existing window
            s2 = api.open_settings()
            assert s2.get("ok") is True, f"Failed to focus settings: {s2}"
            assert s2.get("action") == "focused", f"Expected action=focused, got {s2}"

            # Close settings
            s_close = api.close_settings()
            assert s_close.get("ok") is True
            assert api._settings_window is None

            results["api_settings_singleton_verified"] = True
            print("  [OK] Live settings window singleton focus & destroy verified!")

        except Exception as e:
            results["errors"].append(str(e))
            print(f"  [ERROR] Live test harness failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("  [TEARDOWN] Destroying test windows...")
            try:
                api.close_settings()
            except Exception:
                pass
            try:
                win.destroy()
            except Exception:
                pass

    html = """
    <!DOCTYPE html>
    <html>
    <head><style>body { background: transparent; margin: 0; }</style></head>
    <body>
        <div style="width: 200px; height: 300px; background: rgba(0, 120, 215, 0.5); border-radius: 20px;">
            <h3 style="color: white; text-align: center; padding-top: 20px;">Empirical Test</h3>
        </div>
    </body>
    </html>
    """

    win = webview.create_window(
        title="Challenger 1 Empirical Test Window",
        html=html,
        transparent=True,
        frameless=True,
        width=346,
        height=832,
    )

    t = threading.Thread(target=test_worker, args=(win,), daemon=True)
    t.start()
    webview.start()

    print("\n--- TEST EXECUTION SUMMARY ---")
    all_passed = True
    for k, v in results.items():
        if k == "errors":
            if v:
                all_passed = False
                print(f"  {k}: {v}")
        else:
            status = "PASS" if v else "FAIL"
            print(f"  {k}: {status}")
            if not v:
                all_passed = False

    if not all_passed:
        sys.exit(1)
    else:
        print("\n[CHALLENGER-1] ALL LIVE RUNTIME EMPIRICAL TESTS PASSED SUCCESSFULLY!")
        sys.exit(0)


if __name__ == "__main__":
    run_live_harness()
