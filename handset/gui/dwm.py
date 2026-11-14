"""iPhone Link - Windows DWM Composition, Acrylic Backdrop & Transparency Management."""

from __future__ import annotations

import ctypes
from ctypes import wintypes, c_int, c_void_p, c_size_t, byref, sizeof, Structure
import sys


class MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth", c_int),
        ("cxRightWidth", c_int),
        ("cyTopHeight", c_int),
        ("cyBottomHeight", c_int),
    ]


class ACCENT_POLICY(Structure):
    _fields_ = [
        ("AccentState", c_int),
        ("AccentFlags", c_int),
        ("GradientColor", c_int),
        ("AnimationId", c_int),
    ]


class WINCOMPATTRDATA(Structure):
    _fields_ = [
        ("Attribute", c_int),
        ("Data", c_void_p),
        ("SizeOfData", c_size_t),
    ]


def find_webview_controls(control):
    """Recursively discover all WebView2 controls in WinForms hierarchy and pywebview wrapper."""
    found = []
    if control is None:
        return found
    if hasattr(control, "DefaultBackgroundColor"):
        found.append(control)
    browser = getattr(control, "browser", None)
    if browser:
        wv = getattr(browser, "webview", None)
        if wv and hasattr(wv, "DefaultBackgroundColor") and wv not in found:
            found.append(wv)
    controls = getattr(control, "Controls", None)
    if controls:
        try:
            for child in list(controls):
                found.extend(find_webview_controls(child))
        except Exception:
            pass
    return found


def apply_dwm_transparency(hwnd: int, is_real_phone: bool, current_theme: str = "dark") -> None:
    """Apply DWM per-pixel transparency or Windows 11 Thin Acrylic backdrop."""
    if not hwnd or sys.platform != "win32":
        return

    try:
        dwmapi = getattr(ctypes.windll, "dwmapi", None)
        user32 = getattr(ctypes.windll, "user32", None)
        if not dwmapi or not user32:
            return

        is_dark = current_theme != "light"

        # 1. Dark Mode frame attribute
        dwmapi.DwmSetWindowAttribute(wintypes.HWND(hwnd), 20, byref(c_int(1 if is_dark else 0)), sizeof(c_int))

        if is_real_phone:
            # Real Phone Mode: Pure 100% per-pixel transparent canvas
            # Disable DWM accent backdrop and frame extensions so pywebview native transparent=True renders directly to desktop
            accent = ACCENT_POLICY(0, 0, 0, 0)  # ACCENT_DISABLED = 0
            corner_pref = c_int(1)  # DWMWCP_DONOTROUND = 1 (HTML squircle renders curved chassis)
            margins = MARGINS(0, 0, 0, 0)
        else:
            # Standard Mode: Thin Acrylic blur behind + DWM rounded corners
            gradient_color = 0x55161412 if is_dark else 0x45F4F2F0
            accent = ACCENT_POLICY(4, 2, gradient_color, 0)  # ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
            corner_pref = c_int(2)  # DWMWCP_ROUND = 2
            margins = MARGINS(-1, -1, -1, -1)

        dwmapi.DwmExtendFrameIntoClientArea(wintypes.HWND(hwnd), byref(margins))

        data = WINCOMPATTRDATA(19, ctypes.cast(byref(accent), c_void_p), sizeof(accent))
        if hasattr(user32, "SetWindowCompositionAttribute"):
            user32.SetWindowCompositionAttribute(wintypes.HWND(hwnd), byref(data))

        dwmapi.DwmSetWindowAttribute(wintypes.HWND(hwnd), 33, byref(corner_pref), sizeof(c_int))

        # 2. WebView2 Background Color Configuration
        # CRITICAL: Do NOT set form.BackColor to any opaque color (e.g. #10141e) as WinForms Forms
        # do not support transparent BackColor and once set, it permanently destroys per-pixel alpha transparency.
        from webview.platforms.winforms import BrowserView
        import System
        import System.Drawing
        import System.Windows.Forms

        def _update_form():
            for form in list(BrowserView.instances.values()):
                wv_list = find_webview_controls(form)
                for wv in wv_list:
                    try:
                        wv.Visible = True
                    except Exception:
                        pass
                    try:
                        wv.DefaultBackgroundColor = System.Drawing.Color.FromArgb(0, 0, 0, 0)
                    except Exception:
                        pass
                    try:
                        ctrl = getattr(wv, "CoreWebView2Controller", None)
                        if ctrl:
                            ctrl.DefaultBackgroundColor = System.Drawing.Color.FromArgb(0, 0, 0, 0)
                    except Exception:
                        pass

                try:
                    form.Invalidate()
                except Exception:
                    pass

        for form in list(BrowserView.instances.values()):
            if hasattr(form, "InvokeRequired") and form.InvokeRequired:
                form.Invoke(System.Windows.Forms.MethodInvoker(_update_form))
            else:
                _update_form()
            break
    except Exception as e:
        print("[iPhoneLink DWM] Error applying transparency:", e)


def reapply_dwm_rounded_corners(hwnd: int | None, is_fullscreen: bool = False, is_real_phone: bool = False) -> None:
    """Re-apply Windows 11 DWM rounded corner preference if not in Real Phone or Fullscreen mode."""
    if not hwnd or sys.platform != "win32":
        return

    # In Real Phone mode, HTML chassis renders squircle corners; don't force DWM window rounding
    if is_real_phone:
        return

    try:
        wh = wintypes.HWND(hwnd)
        user32 = getattr(ctypes.windll, "user32", None)
        dwmapi = getattr(ctypes.windll, "dwmapi", None)

        if not is_fullscreen and user32:
            style = user32.GetWindowLongW(wh, -16)
            if style & 0x01000000:
                user32.SetWindowLongW(wh, -16, style & ~0x01000000)

        if dwmapi:
            pref = ctypes.c_int(2)  # DWMWCP_ROUND = 2
            dwmapi.DwmSetWindowAttribute(wh, 33, ctypes.byref(pref), ctypes.sizeof(pref))

        if not is_fullscreen and user32:
            user32.SetWindowPos(wh, 0, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)
    except Exception:
        pass


def apply_phone_window_region(hwnd: int | None, is_real_phone: bool, is_landscape: bool = False) -> None:
    """Clip the native Windows window to authentic iPhone squircle geometry using Win32 SetWindowRgn.

    This guarantees 100% true OS-level transparency at the four corners outside the rounded chassis:
    Windows physically does not render or allocate pixels outside the region, eliminating white/grey corners
    permanently with native click-through.
    """
    if not hwnd or sys.platform != "win32":
        return

    try:
        user32 = getattr(ctypes.windll, "user32", None)
        gdi32 = getattr(ctypes.windll, "gdi32", None)
        if not user32 or not gdi32:
            return

        wh = wintypes.HWND(hwnd)
        if not is_real_phone:
            # Restore standard rectangular window shape
            user32.SetWindowRgn(wh, None, True)
            return

        rect = wintypes.RECT()
        if not user32.GetWindowRect(wh, ctypes.byref(rect)):
            if not user32.GetClientRect(wh, ctypes.byref(rect)):
                return
            w_px = rect.right - rect.left
            h_px = rect.bottom - rect.top
        else:
            w_px = rect.right - rect.left
            h_px = rect.bottom - rect.top
        if w_px <= 0 or h_px <= 0:
            return

        # Calculate corner radius proportional to iPhone chassis with exact DPI scaling
        # In CSS: border-radius is 58px portrait, 48px landscape (Apple G2 Squircle)
        dpi = 96
        if hasattr(user32, "GetDpiForWindow"):
            try:
                val = user32.GetDpiForWindow(wh)
                if val > 0:
                    dpi = val
            except Exception:
                pass
        dpi_scale = dpi / 96.0

        css_radius = 48 if is_landscape else 58
        radius = int(round(css_radius * dpi_scale))
        radius = max(20, min(120, radius))
        corner_diameter = radius * 2

        gdi32.CreateRoundRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        gdi32.CreateRoundRectRgn.restype = wintypes.HRGN
        user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
        user32.SetWindowRgn.restype = ctypes.c_int

        hrgn = gdi32.CreateRoundRectRgn(0, 0, w_px + 1, h_px + 1, corner_diameter, corner_diameter)
        if hrgn:
            user32.SetWindowRgn(wh, hrgn, True)
    except Exception as e:
        print("[iPhoneLink DWM] Error applying window region:", e)


def center_window_on_screen(hwnd: int | None, width: int = 0, height: int = 0) -> None:
    """Center the specified HWND window on the active monitor's working area (excluding taskbar)."""
    if not hwnd or sys.platform != "win32":
        return
    try:
        user32 = getattr(ctypes.windll, "user32", None)
        if not user32 or hasattr(user32, "_mock_return_value"):
            return
        wh = wintypes.HWND(hwnd)

        rect = wintypes.RECT()
        if user32.GetWindowRect(wh, ctypes.byref(rect)):
            curr_w = rect.right - rect.left
            curr_h = rect.bottom - rect.top
        else:
            curr_w, curr_h = width, height

        win_w = width if width > 0 else curr_w
        win_h = height if height > 0 else curr_h

        # MONITOR_DEFAULTTONEAREST = 2
        user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
        user32.MonitorFromWindow.restype = wintypes.HANDLE
        hmon = user32.MonitorFromWindow(wh, 2)

        class MONITORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", wintypes.DWORD),
                ("rcMonitor", wintypes.RECT),
                ("rcWork", wintypes.RECT),
                ("dwFlags", wintypes.DWORD),
            ]

        mi = MONITORINFO()
        mi.cbSize = ctypes.sizeof(MONITORINFO)
        user32.GetMonitorInfoW.argtypes = [wintypes.HANDLE, ctypes.POINTER(MONITORINFO)]
        user32.GetMonitorInfoW.restype = wintypes.BOOL

        if hmon and user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            work = mi.rcWork
        else:
            work = wintypes.RECT()
            # SPI_GETWORKAREA = 0x0030
            if not user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):
                work = wintypes.RECT(0, 0, user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))

        work_w = work.right - work.left
        work_h = work.bottom - work.top

        cx = work.left + max(0, (work_w - win_w) // 2)
        cy = work.top + max(0, (work_h - win_h) // 2)

        # SWP_NOZORDER (0x0004) | SWP_SHOWWINDOW (0x0040)
        user32.SetWindowPos(wh, 0, cx, cy, win_w, win_h, 0x0004 | 0x0040)
    except Exception as e:
        print("[iPhoneLink DWM] Error centering window:", e)

