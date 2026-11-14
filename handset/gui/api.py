"""iPhone Link - JS-accessible WindowApi Bridge."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import os
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any

from .config import (
    PORTRAIT_WIDTH,
    PORTRAIT_HEIGHT,
    DRAWER_WIDTH,
    LANDSCAPE_HEIGHT,
    LANDSCAPE_WIDTH_NO_DRAWER,
    LANDSCAPE_WIDTH_DRAWER,
)
from .dwm import (
    apply_dwm_transparency,
    reapply_dwm_rounded_corners,
    apply_phone_window_region,
    center_window_on_screen,
    apply_window_icon,
)
from .real_phone import calculate_real_phone_dimensions


class WindowApi:
    """JS-accessible API exposed under window.pywebview.api."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self._window: Any = None
        self._settings_window: Any = None
        self._cached_settings_hwnd: int | None = None
        self._settings_lock = threading.Lock()
        self._host = host
        self._port = port
        self._cached_hwnd: int | None = None
        self._current_display_width = PORTRAIT_WIDTH
        self._ideal_display_width = PORTRAIT_WIDTH
        self._drawer_open = False
        self._is_landscape = False
        self._hidden_to_tray = False
        self._is_fullscreen = False
        self._is_real_phone = False
        self._current_theme = "dark"
        self._saved_window_pos: tuple[int, int] | None = None
        self._saved_portrait_phys_size: tuple[int, int] | None = None
        self._saved_landscape_phys_size: tuple[int, int] | None = None

        # Real Phone scale ratio & dimension persistence
        self._real_phone_scale_ratio: float = 1.0
        self._real_phone_portrait_height: int = 820
        self._real_phone_landscape_height: int = 430
        try:
            from handset.server import load_user_settings
            st = load_user_settings()
            if "realPhoneScaleRatio" in st:
                self._real_phone_scale_ratio = float(st.get("realPhoneScaleRatio", 1.0))
            if "realPhonePortraitHeight" in st:
                self._real_phone_portrait_height = int(st.get("realPhonePortraitHeight", 820))
            if "realPhoneLandscapeHeight" in st:
                self._real_phone_landscape_height = int(st.get("realPhoneLandscapeHeight", 430))
        except Exception:
            pass

    def _get_window_dpi_scale(self, hwnd: int | None = None) -> float:
        """Accurately query DPI scale factor."""
        if sys.platform != "win32":
            return 1.0
        try:
            h = hwnd or self._get_hwnd()
            if h and hasattr(ctypes.windll.user32, "GetDpiForWindow"):
                dpi = ctypes.windll.user32.GetDpiForWindow(wintypes.HWND(h))
                if dpi > 0:
                    return float(dpi) / 96.0
        except Exception:
            pass
        return 1.0

    def _schedule_reapply_corners(self):
        """Schedule DWM corner updates and native phone squircle window region."""
        hwnd = self._get_hwnd()
        if hwnd:
            is_fs = getattr(self, "_is_fullscreen", False)
            is_rp = getattr(self, "_is_real_phone", False)
            is_land = getattr(self, "_is_landscape", False)
            if is_rp:
                apply_phone_window_region(hwnd, True, is_land)
            else:
                apply_phone_window_region(hwnd, False)
                reapply_dwm_rounded_corners(hwnd, is_fs, False)
            
            def _deferred():
                h = self._get_hwnd()
                if h:
                    if getattr(self, "_is_real_phone", False):
                        apply_phone_window_region(h, True, getattr(self, "_is_landscape", False))
                    else:
                        apply_phone_window_region(h, False)
                        reapply_dwm_rounded_corners(h, getattr(self, "_is_fullscreen", False), False)

            # Debounce timers: cancel previous pending timers to prevent thread storms during drag
            if not hasattr(self, "_corner_timers"):
                self._corner_timers = []
            for t in self._corner_timers:
                try:
                    t.cancel()
                except Exception:
                    pass
            self._corner_timers.clear()

            for delay in (0.04, 0.15):
                t = threading.Timer(delay, _deferred)
                t.daemon = True
                self._corner_timers.append(t)
                t.start()

    def set_window(self, window: Any):
        self._window = window
        if hasattr(window, "events") and hasattr(window.events, "resized"):
            try:
                window.events.resized += lambda *args: self._schedule_reapply_corners()
            except Exception:
                pass

        def _center_main_startup():
            for _ in range(30):
                h = self._get_hwnd()
                if h and sys.platform == "win32":
                    w = getattr(self._window, "width", PORTRAIT_WIDTH)
                    h_val = getattr(self._window, "height", PORTRAIT_HEIGHT)
                    center_window_on_screen(h, w, h_val)
                    apply_window_icon(h)
                    self._schedule_reapply_corners()
                    break
                time.sleep(0.04)

        threading.Thread(target=_center_main_startup, daemon=True).start()

    def _get_hwnd(self) -> int | None:
        try:
            if self._cached_hwnd and ctypes.windll.user32.IsWindow(wintypes.HWND(self._cached_hwnd)):
                return self._cached_hwnd
            h = ctypes.windll.user32.FindWindowW(None, "ip+")
            if not h:
                h = ctypes.windll.user32.FindWindowW(None, "iPhone Link")
            if not h and self._window and hasattr(self._window, "title"):
                h = ctypes.windll.user32.FindWindowW(None, str(self._window.title))
            if not h:
                try:
                    from webview.platforms.winforms import BrowserView
                    for form in list(BrowserView.instances.values()):
                        if form and hasattr(form, "Handle"):
                            cand = int(form.Handle.ToInt64() if hasattr(form.Handle, "ToInt64") else int(form.Handle))
                            if cand and ctypes.windll.user32.IsWindow(wintypes.HWND(cand)):
                                h = cand
                                break
                except Exception:
                    pass
            if h:
                self._cached_hwnd = h
            return h
        except Exception:
            return None

    def _get_settings_hwnd(self) -> int | None:
        """Resolve HWND for the Settings window."""
        try:
            if self._cached_settings_hwnd and ctypes.windll.user32.IsWindow(wintypes.HWND(self._cached_settings_hwnd)):
                return self._cached_settings_hwnd
            if self._settings_window:
                try:
                    from webview.platforms.winforms import BrowserView
                    form = BrowserView.instances.get(self._settings_window.uid)
                    if form and hasattr(form, "Handle"):
                        cand = int(form.Handle.ToInt64() if hasattr(form.Handle, "ToInt64") else int(form.Handle))
                        if cand and ctypes.windll.user32.IsWindow(wintypes.HWND(cand)):
                            self._cached_settings_hwnd = cand
                            return cand
                except Exception:
                    pass
            for title in ("ip+ - Settings", "ip+ Settings", "iPhone Link - Settings", "iPhone-Link Settings"):
                h = ctypes.windll.user32.FindWindowW(None, title)
                if h:
                    self._cached_settings_hwnd = h
                    return h
        except Exception:
            pass
        return None

    def _eval_js(self, script: str) -> None:
        if self._window is None:
            return
        try:
            self._window.evaluate_js(script)
        except Exception:
            pass

    def _api_post(self, path: str, payload: bytes = b"{}", timeout: float = 1.5) -> dict:
        req = urllib.request.Request(
            f"http://{self._host}:{self._port}{path}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def start_window_drag(self) -> None:
        if sys.platform != "win32":
            return
        hwnd = self._get_hwnd()
        if hwnd:
            user32 = getattr(ctypes.windll, "user32", None)
            if user32:
                user32.ReleaseCapture()
                user32.SendMessageW(wintypes.HWND(hwnd), 0x0112, 0xF010 + 2, 0)

    def start_window_resize(self, direction: str = "bottom_right") -> None:
        if sys.platform != "win32":
            return
        hwnd = self._get_hwnd()
        if hwnd:
            user32 = getattr(ctypes.windll, "user32", None)
            if user32:
                user32.ReleaseCapture()
                user32.SendMessageW(wintypes.HWND(hwnd), 0x0112, 0xF008, 0)

    def resize_window(self, width: int, height: int, is_final: bool = False) -> dict:
        """Directly resize the window to given dimensions while preserving locked ratio and DWM region."""
        if not self._window:
            return {"ok": False, "error": "No window"}
        try:
            is_rp = getattr(self, "_is_real_phone", False)
            is_land = getattr(self, "_is_landscape", False)
            asp = getattr(self, "_last_aspect", None)
            if not asp:
                asp = 2436.0 / 1125.0 if is_land else 1125.0 / 2436.0

            if is_rp:
                bezel = 24
                if is_land:
                    if asp < 1.0:
                        asp = 1.0 / asp
                    w = max(380, min(2200, int(round(width))))
                    inner_w = max(100, w - bezel)
                    inner_h = int(round(inner_w / asp))
                    h = inner_h + bezel
                else:
                    if asp > 1.0:
                        asp = 1.0 / asp
                    h = max(360, min(1600, int(round(height))))
                    inner_h = max(100, h - bezel)
                    inner_w = int(round(inner_h * asp))
                    w = inner_w + bezel

                if is_land:
                    self._real_phone_landscape_height = h
                    self._real_phone_scale_ratio = max(0.3, min(3.0, round((h - bezel) / (430 - bezel), 4)))
                    self._real_phone_portrait_height = int(round((820 - bezel) * self._real_phone_scale_ratio)) + bezel
                else:
                    self._real_phone_portrait_height = h
                    self._real_phone_scale_ratio = max(0.3, min(3.0, round((h - bezel) / (820 - bezel), 4)))
                    self._real_phone_landscape_height = int(round((430 - bezel) * self._real_phone_scale_ratio)) + bezel

                if is_final:
                    try:
                        from handset.server import save_user_settings
                        save_user_settings({
                            "realPhoneScaleRatio": self._real_phone_scale_ratio,
                            "realPhonePortraitHeight": self._real_phone_portrait_height,
                            "realPhoneLandscapeHeight": self._real_phone_landscape_height,
                        })
                    except Exception:
                        pass
            else:
                w = max(240, min(2560, int(round(width))))
                h = max(320, min(2560, int(round(height))))

            self._window.resize(w, h)
            
            # Fast immediate region update without spawning timer threads during active drag
            hwnd = self._get_hwnd()
            if hwnd:
                if is_rp:
                    apply_phone_window_region(hwnd, True, is_land)
                else:
                    apply_phone_window_region(hwnd, False)

            # Settle rounded corners and DWM effects when resize drag finishes
            if is_final:
                self._schedule_reapply_corners()
                
            return {"ok": True, "width": w, "height": h}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def finish_window_resize(self) -> dict:
        """Called when pointer drag resize completes to settle corners and regions."""
        self._schedule_reapply_corners()
        return {"ok": True}

    def scale_window_ratio(self, delta_pct: float) -> dict:
        if not self._window:
            return {"ok": False, "error": "No window"}
        try:
            scale = 1.0 + (float(delta_pct) / 100.0)
            cur_w, cur_h = self._window.width, self._window.height
            is_rp = getattr(self, "_is_real_phone", False)
            is_land = getattr(self, "_is_landscape", False)
            asp = getattr(self, "_last_aspect", None)
            if not asp:
                asp = 2436.0 / 1125.0 if is_land else 1125.0 / 2436.0

            if is_rp:
                bezel = 24
                if is_land:
                    if asp < 1.0:
                        asp = 1.0 / asp
                    new_w = max(380, min(2200, int(round(cur_w * scale))))
                    inner_w = max(100, new_w - bezel)
                    inner_h = int(round(inner_w / asp))
                    new_h = inner_h + bezel
                else:
                    if asp > 1.0:
                        asp = 1.0 / asp
                    new_h = max(360, min(1600, int(round(cur_h * scale))))
                    inner_h = max(100, new_h - bezel)
                    inner_w = int(round(inner_h * asp))
                    new_w = inner_w + bezel

                if is_land:
                    self._real_phone_landscape_height = new_h
                    self._real_phone_scale_ratio = max(0.3, min(3.0, round((new_h - bezel) / (430 - bezel), 4)))
                    self._real_phone_portrait_height = int(round((820 - bezel) * self._real_phone_scale_ratio)) + bezel
                else:
                    self._real_phone_portrait_height = new_h
                    self._real_phone_scale_ratio = max(0.3, min(3.0, round((new_h - bezel) / (820 - bezel), 4)))
                    self._real_phone_landscape_height = int(round((430 - bezel) * self._real_phone_scale_ratio)) + bezel

                try:
                    from handset.server import save_user_settings
                    save_user_settings({
                        "realPhoneScaleRatio": self._real_phone_scale_ratio,
                        "realPhonePortraitHeight": self._real_phone_portrait_height,
                        "realPhoneLandscapeHeight": self._real_phone_landscape_height,
                    })
                except Exception:
                    pass
            else:
                new_w = max(240, min(1600, int(round(cur_w * scale))))
                new_h = max(360, min(2400, int(round(cur_h * scale))))

            self._window.resize(new_w, new_h)
            self._schedule_reapply_corners()
            return {"ok": True, "width": new_w, "height": new_h}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def minimize(self):
        if self._window:
            self._window.minimize()

    def minimize_to_tray(self):
        if self._window:
            self._hidden_to_tray = True
            hwnd = self._get_hwnd()
            if hwnd and sys.platform == "win32":
                ctypes.windll.user32.ShowWindow(wintypes.HWND(hwnd), 0)  # SW_HIDE
            else:
                self._window.hide()

    def restore_from_tray(self):
        if self._window:
            self._hidden_to_tray = False
            hwnd = self._get_hwnd()
            if hwnd and sys.platform == "win32":
                ctypes.windll.user32.ShowWindow(wintypes.HWND(hwnd), 9)  # SW_RESTORE
                ctypes.windll.user32.SetForegroundWindow(wintypes.HWND(hwnd))
            else:
                self._window.show()
                self._window.restore()

    def toggle_tray_window(self):
        if self._hidden_to_tray:
            self.restore_from_tray()
        else:
            self.minimize_to_tray()

    def close(self):
        if self._settings_window:
            try:
                self._settings_window.destroy()
            except Exception:
                pass
            self._settings_window = None
            self._cached_settings_hwnd = None
        if self._window:
            self._window.destroy()

    def open_settings(self) -> dict:
        """Open or bring to front the standalone macOS-style Settings window."""
        import webview

        with getattr(self, "_settings_lock", threading.Lock()):
            # Singleton pattern: if already open and alive, bring to foreground
            if self._settings_window is not None:
                try:
                    is_closed = False
                    if hasattr(self._settings_window, "events") and hasattr(self._settings_window.events, "closed"):
                        if self._settings_window.events.closed.is_set():
                            is_closed = True
                    if not is_closed:
                        try:
                            self._settings_window.show()
                            self._settings_window.restore()
                        except Exception:
                            pass
                        h = self._get_settings_hwnd()
                        if h and sys.platform == "win32":
                            try:
                                center_window_on_screen(h, 780, 580)
                                ctypes.windll.user32.ShowWindow(wintypes.HWND(h), 9)  # SW_RESTORE
                                ctypes.windll.user32.SetForegroundWindow(wintypes.HWND(h))
                            except Exception:
                                pass
                        return {"ok": True, "action": "focused"}
                except Exception:
                    self._settings_window = None

            settings_url = f"http://{self._host}:{self._port}/settings.html?t={int(time.time())}"

            win_w = 780
            win_h = 580
            spawn_x, spawn_y = None, None
            try:
                if sys.platform == "win32":
                    user32 = ctypes.windll.user32
                    rect_work = wintypes.RECT()
                    if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect_work), 0):
                        work_w = rect_work.right - rect_work.left
                        work_h = rect_work.bottom - rect_work.top
                        spawn_x = rect_work.left + max(20, (work_w - win_w) // 2)
                        spawn_y = rect_work.top + max(20, (work_h - win_h) // 2)
            except Exception:
                pass

            try:
                bg_color = "#18181b" if self._current_theme == "dark" else "#f6f6f8"
                self._settings_window = webview.create_window(
                    title="ip+ - Settings",
                    url=settings_url,
                    js_api=self,
                    width=win_w,
                    height=win_h,
                    min_size=(680, 480),
                    resizable=True,
                    frameless=True,
                    easy_drag=False,
                    on_top=False,
                    background_color=bg_color,
                    x=spawn_x,
                    y=spawn_y,
                )

                def _on_settings_closed():
                    with getattr(self, "_settings_lock", threading.Lock()):
                        self._settings_window = None
                        self._cached_settings_hwnd = None

                if hasattr(self._settings_window, "events"):
                    self._settings_window.events.closed += _on_settings_closed

                def _focus_after_create():
                    for _ in range(30):
                        h = self._get_settings_hwnd()
                        if h and sys.platform == "win32":
                            try:
                                center_window_on_screen(h, win_w, win_h)
                                apply_window_icon(h)
                                ctypes.windll.user32.ShowWindow(wintypes.HWND(h), 9)  # SW_RESTORE
                                ctypes.windll.user32.SetForegroundWindow(wintypes.HWND(h))
                                dwmapi = getattr(ctypes.windll, "dwmapi", None)
                                if dwmapi:
                                    corner_pref = ctypes.c_int(2)  # DWMWCP_ROUND
                                    dwmapi.DwmSetWindowAttribute(
                                        wintypes.HWND(h),
                                        33,  # DWMWA_WINDOW_CORNER_PREFERENCE
                                        ctypes.byref(corner_pref),
                                        ctypes.sizeof(corner_pref),
                                    )
                                break
                            except Exception:
                                pass
                        time.sleep(0.04)

                threading.Thread(target=_focus_after_create, daemon=True).start()

                return {"ok": True, "action": "created"}
            except Exception as e:
                return {"ok": False, "error": str(e)}

    def close_settings(self) -> dict:
        """Close settings window if open."""
        with getattr(self, "_settings_lock", threading.Lock()):
            if self._settings_window is not None:
                try:
                    self._settings_window.destroy()
                except Exception:
                    pass
                self._settings_window = None
                self._cached_settings_hwnd = None
            return {"ok": True}

    def minimize_settings(self) -> dict:
        """Minimize settings window."""
        try:
            if self._settings_window:
                try:
                    self._settings_window.minimize()
                    return {"ok": True}
                except Exception:
                    pass
            h = self._get_settings_hwnd()
            if h and sys.platform == "win32":
                ctypes.windll.user32.ShowWindow(wintypes.HWND(h), 6)  # SW_MINIMIZE
                return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Settings window not open"}

    def maximize_settings(self) -> dict:
        """Toggle maximize or restore for settings window."""
        try:
            h = self._get_settings_hwnd()
            if h and sys.platform == "win32":
                is_zoomed = bool(ctypes.windll.user32.IsZoomed(wintypes.HWND(h)))
                if is_zoomed:
                    ctypes.windll.user32.ShowWindow(wintypes.HWND(h), 9)  # SW_RESTORE
                else:
                    ctypes.windll.user32.ShowWindow(wintypes.HWND(h), 3)  # SW_MAXIMIZE
                return {"ok": True, "maximized": not is_zoomed}
            if self._settings_window:
                return {"ok": True}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "Settings window not open"}

    def toggle_fullscreen(self, target_state: bool = None):
        if not self._window:
            return {"ok": False}
        if target_state is None:
            self._is_fullscreen = not self._is_fullscreen
        else:
            self._is_fullscreen = bool(target_state)

        if self._is_fullscreen:
            self._window.toggle_fullscreen()
        else:
            if getattr(self._window, "fullscreen", False):
                self._window.toggle_fullscreen()
            self._schedule_reapply_corners()
        return {"ok": True, "fullscreen": self._is_fullscreen}

    def set_orientation(self, landscape: bool, drawer_open: bool = None):
        self._is_landscape = bool(landscape)
        self._drawer_open = False

        if self._is_real_phone:
            asp = 2436.0 / 1125.0 if self._is_landscape else 1125.0 / 2436.0
            return self.set_real_phone_mode(True, asp)

        if self._is_landscape:
            target_w = LANDSCAPE_WIDTH_NO_DRAWER
            target_h = LANDSCAPE_HEIGHT
        else:
            dw = getattr(self, "_ideal_display_width", getattr(self, "_current_display_width", PORTRAIT_WIDTH))
            target_w = dw
            target_h = PORTRAIT_HEIGHT

        if self._window:
            self._window.resize(target_w, target_h)
        self._schedule_reapply_corners()
        return {"ok": True, "landscape": self._is_landscape, "width": target_w, "height": target_h}

    def _apply_real_phone_dwm(self, is_real_phone: bool) -> None:
        hwnd = self._get_hwnd()
        if hwnd:
            apply_dwm_transparency(hwnd, is_real_phone, self._current_theme)
            apply_phone_window_region(hwnd, is_real_phone, getattr(self, "_is_landscape", False))

    def set_real_phone_mode(self, is_real_phone: bool, aspect: float = 0.0):
        """Toggle Real Phone Mode with 100% per-pixel transparent background and physical chassis."""
        self._is_real_phone = bool(is_real_phone)

        if not self._window:
            self._apply_real_phone_dwm(self._is_real_phone)
            return {"ok": True, "real_phone": self._is_real_phone}

        if self._is_real_phone:
            asp = float(aspect) if (aspect and 0.2 < float(aspect) < 5.0) else (1125.0 / 2436.0)
            is_land = asp > 1.0
            self._is_landscape = is_land
            self._last_aspect = asp

            saved_h = self._real_phone_landscape_height if is_land else self._real_phone_portrait_height
            target_w, target_h = calculate_real_phone_dimensions(
                asp, is_land, scale_ratio=self._real_phone_scale_ratio, custom_height=saved_h
            )

            try:
                self._window.resize(target_w, target_h)
            except Exception:
                pass
            self._apply_real_phone_dwm(True)
            self._schedule_reapply_corners()
            return {
                "ok": True,
                "real_phone": True,
                "landscape": is_land,
                "width": target_w,
                "height": target_h,
                "scale_ratio": self._real_phone_scale_ratio,
            }
        else:
            if self._is_landscape:
                target_w = LANDSCAPE_WIDTH_NO_DRAWER
                target_h = LANDSCAPE_HEIGHT
            else:
                dw = getattr(self, "_ideal_display_width", getattr(self, "_current_display_width", PORTRAIT_WIDTH))
                target_w = dw
                target_h = PORTRAIT_HEIGHT

            try:
                self._window.resize(target_w, target_h)
            except Exception:
                pass
            self._apply_real_phone_dwm(False)
            self._schedule_reapply_corners()
            return {"ok": True, "real_phone": False, "width": target_w, "height": target_h}

    def reapply_window_region(self) -> dict:
        """Explicitly re-apply window region and DWM corners (callable from JS after layout/orientation transitions)."""
        self._schedule_reapply_corners()
        return {"ok": True}

    def sync_device_aspect(self, display_width: int, drawer_open: bool = False):
        if not self._window or self._is_real_phone or self._is_fullscreen or self._is_landscape:
            return {"ok": True, "skipped": True}
        try:
            self._drawer_open = False
            dw = max(336, min(600, int(display_width)))
            self._ideal_display_width = dw
            target_w = dw
            target_h = PORTRAIT_HEIGHT
            self._window.resize(target_w, target_h)
            self._schedule_reapply_corners()
            return {"ok": True, "width": target_w, "height": target_h}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def set_drawer(self, is_open: bool):
        """Deprecated drawer toggle shim: opens settings window for backward compatibility."""
        self._drawer_open = False
        if is_open:
            return self.open_settings()
        return {"ok": True, "deprecated": True}

    def get_window_rect(self):
        hwnd = self._get_hwnd()
        if hwnd and sys.platform == "win32":
            rect = wintypes.RECT()
            if ctypes.windll.user32.GetWindowRect(wintypes.HWND(hwnd), ctypes.byref(rect)):
                return {"x": rect.left, "y": rect.top, "w": rect.right - rect.left, "h": rect.bottom - rect.top}
        return {"x": 0, "y": 0, "w": PORTRAIT_WIDTH, "h": PORTRAIT_HEIGHT}

    def set_theme(self, theme: str):
        self._current_theme = "light" if theme == "light" else "dark"
        self._apply_real_phone_dwm(self._is_real_phone)
        return {"ok": True, "theme": self._current_theme}

    def is_pywebview(self):
        return True

    def wipe_privacy_data(self):
        return {"ok": True, "wiped": True}

    def get_real_phone_scale(self) -> dict:
        """Return the current persistent Real Phone scale ratio and heights."""
        return {
            "ok": True,
            "scale_ratio": getattr(self, "_real_phone_scale_ratio", 1.0),
            "portrait_height": getattr(self, "_real_phone_portrait_height", 820),
            "landscape_height": getattr(self, "_real_phone_landscape_height", 430),
        }

    def reset_real_phone_scale(self) -> dict:
        """Reset Real Phone scale ratio back to 100% (default 820px portrait / 430px landscape)."""
        self._real_phone_scale_ratio = 1.0
        self._real_phone_portrait_height = 820
        self._real_phone_landscape_height = 430
        try:
            from handset.server import save_user_settings
            save_user_settings({
                "realPhoneScaleRatio": 1.0,
                "realPhonePortraitHeight": 820,
                "realPhoneLandscapeHeight": 430,
            })
        except Exception:
            pass

        if getattr(self, "_is_real_phone", False):
            asp = getattr(self, "_last_aspect", 1125.0 / 2436.0)
            return self.set_real_phone_mode(True, asp)
        return {"ok": True, "scale_ratio": 1.0}

    def get_recording_folder(self) -> dict:
        """Return current configured screen recording folder."""
        try:
            from handset.server import load_user_settings
            st = load_user_settings()
            folder = st.get("recordingFolder")
            if not folder:
                folder = str(Path.home() / "Videos" / "ip+")
            return {"ok": True, "folder": str(folder)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def choose_recording_folder(self) -> dict:
        """Open native Windows folder picker dialog to select recording destination folder."""
        folder = None
        try:
            if self._window:
                import webview
                res = self._window.create_file_dialog(webview.FOLDER_DIALOG)
                if res and len(res) > 0:
                    folder = res[0]
        except Exception:
            pass

        if not folder and sys.platform == "win32":
            try:
                import clr
                clr.AddReference("System.Windows.Forms")
                from System.Windows.Forms import FolderBrowserDialog, DialogResult
                fbd = FolderBrowserDialog()
                fbd.Description = "Pilih Folder Penyimpanan Rekaman Layar ip+"
                if fbd.ShowDialog() == DialogResult.OK:
                    folder = str(fbd.SelectedPath)
            except Exception:
                pass

        if folder:
            try:
                from handset.server import save_user_settings
                folder_str = str(Path(folder).resolve())
                os.makedirs(folder_str, exist_ok=True)
                save_user_settings({"recordingFolder": folder_str})
                return {"ok": True, "folder": folder_str}
            except Exception as e:
                return {"ok": False, "error": str(e)}

        return {"ok": False, "cancelled": True}

    def open_recording_folder(self) -> dict:
        """Open the recording destination directory in Windows File Explorer."""
        try:
            from handset.server import load_user_settings
            st = load_user_settings()
            folder = st.get("recordingFolder") or str(Path.home() / "Videos" / "ip+")
            os.makedirs(folder, exist_ok=True)
            if sys.platform == "win32":
                os.startfile(folder)
            return {"ok": True, "folder": folder}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def save_recording(self, base64_data: str, mime_type: str = "video/webm", duration_ms: float = 0.0) -> dict:
        """Save captured canvas video blob to the configured recording folder."""
        if not base64_data:
            return {"ok": False, "error": "No data"}
        try:
            import base64
            from datetime import datetime
            from handset.server import load_user_settings, patch_webm_duration

            st = load_user_settings()
            folder = st.get("recordingFolder") or str(Path.home() / "Videos" / "ip+")
            folder_path = Path(folder)
            folder_path.mkdir(parents=True, exist_ok=True)

            ext = ".mp4" if "mp4" in str(mime_type).lower() else ".webm"
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ip+_recording_{ts}{ext}"
            file_path = folder_path / filename

            clean_data = str(base64_data)
            if "," in clean_data:
                clean_data = clean_data.split(",", 1)[1]
            file_bytes = base64.b64decode(clean_data)
            if ext == ".webm":
                file_bytes = patch_webm_duration(file_bytes, float(duration_ms or 0))
            file_path.write_bytes(file_bytes)

            return {
                "ok": True,
                "success": True,
                "path": str(file_path),
                "filename": filename,
                "size": len(file_bytes),
                "folder": str(folder_path),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def install_apple_driver(self, source: str = "auto") -> dict:
        """Trigger automated installation of Apple USB drivers via winget / Microsoft Store."""
        try:
            from handset.driver_installer import trigger_apple_driver_install
            return trigger_apple_driver_install(preferred_source=str(source or "auto"))
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_apple_driver_install_status(self) -> dict:
        """Get the current progress/status of Apple USB driver installation."""
        try:
            from handset.driver_installer import get_driver_install_status
            return get_driver_install_status()
        except Exception as e:
            return {"ok": False, "error": str(e)}
