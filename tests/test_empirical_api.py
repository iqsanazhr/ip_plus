"""Empirical Stress Tests for WindowApi in handset/gui/api.py.

Conducted by Challenger 1.
Verifies:
1. Singleton focus pattern in open_settings() and close_settings().
2. URL formatting and creation parameters.
3. Backward-compatibility of set_drawer().
4. Window sizing logic across orientation, real phone mode, and sync_device_aspect,
   empirically proving that DRAWER_WIDTH is never inadvertently added.
"""

from __future__ import annotations

import os
import re
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from handset.gui.api import WindowApi
from handset.gui.config import (
    PORTRAIT_WIDTH,
    PORTRAIT_HEIGHT,
    DRAWER_WIDTH,
    LANDSCAPE_HEIGHT,
    LANDSCAPE_WIDTH_NO_DRAWER,
    LANDSCAPE_WIDTH_DRAWER,
)


class MockEvent:
    """Mock for pywebview window event with += operator support."""

    def __init__(self):
        self._handlers = []
        self._set = False

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def is_set(self):
        return self._set

    def fire(self):
        self._set = True
        for h in list(self._handlers):
            h()


class MockPywebviewWindow:
    """Mock for pywebview window object."""

    def __init__(self, title="test", width=100, height=100):
        self.title = title
        self.width = width
        self.height = height
        self.uid = "test-uid-123"
        self.events = MagicMock()
        self.events.closed = MockEvent()
        self.show = MagicMock()
        self.restore = MagicMock()
        self.destroy = MagicMock()
        self.resize = MagicMock(side_effect=self._on_resize)
        self.minimize = MagicMock()
        self.hide = MagicMock()

    def _on_resize(self, w, h):
        self.width = w
        self.height = h


class TestWindowApiEmpirical(unittest.TestCase):
    """Empirical test suite for WindowApi."""

    def setUp(self):
        self.api = WindowApi(host="127.0.0.1", port=8765)
        self.mock_main_window = MockPywebviewWindow(
            title="ip+", width=PORTRAIT_WIDTH, height=PORTRAIT_HEIGHT
        )
        self.api.set_window(self.mock_main_window)

    def test_01_open_settings_singleton_focus_pattern(self):
        """Empirically test that open_settings() enforces strict singleton pattern:

        - First call: creates settings window instance.
        - Subsequent calls while alive: focuses/restores existing window without re-creating.
        - After closed event: recreates new window.
        - After close_settings(): recreates new window.
        """
        created_windows = []

        def fake_create_window(**kwargs):
            win = MockPywebviewWindow(
                title=kwargs.get("title"),
                width=kwargs.get("width"),
                height=kwargs.get("height"),
            )
            win.create_kwargs = kwargs
            created_windows.append(win)
            return win

        with patch("webview.create_window", side_effect=fake_create_window):
            # --- Call 1: First invocation creates window ---
            res1 = self.api.open_settings()
            self.assertTrue(res1.get("ok"), "open_settings call 1 failed")
            self.assertEqual(res1.get("action"), "created")
            self.assertEqual(len(created_windows), 1, "Exactly 1 window must be created")
            first_win = created_windows[0]
            self.assertIs(self.api._settings_window, first_win)

            # --- Call 2: Second invocation while window is alive ---
            res2 = self.api.open_settings()
            self.assertTrue(res2.get("ok"), "open_settings call 2 failed")
            self.assertEqual(res2.get("action"), "focused")
            self.assertEqual(len(created_windows), 1, "Must NOT create second window instance")
            first_win.show.assert_called_once()
            first_win.restore.assert_called_once()

            # --- Call 3: User closes window via UI (events.closed fires) ---
            first_win.events.closed.fire()
            self.assertIsNone(self.api._settings_window, "Window reference must clear on closed event")
            self.assertIsNone(self.api._cached_settings_hwnd, "Cached HWND must clear on closed event")

            # --- Call 4: Invocation after close creates fresh window ---
            res4 = self.api.open_settings()
            self.assertTrue(res4.get("ok"), "open_settings call 4 failed")
            self.assertEqual(res4.get("action"), "created")
            self.assertEqual(len(created_windows), 2, "Second window should be created after closure")
            second_win = created_windows[1]
            self.assertIs(self.api._settings_window, second_win)

            # --- Call 5: close_settings() destroys and resets ---
            res5 = self.api.close_settings()
            self.assertTrue(res5.get("ok"))
            second_win.destroy.assert_called_once()
            self.assertIsNone(self.api._settings_window)

            # --- Call 6: open_settings() after explicit close_settings() ---
            res6 = self.api.open_settings()
            self.assertEqual(res6.get("action"), "created")
            self.assertEqual(len(created_windows), 3)

        print("[PASS] open_settings singleton focus pattern verified")

    def test_02_settings_url_and_creation_parameters(self):
        """Verify URL format, cache buster timestamp, and window dimensions/properties."""
        captured_kwargs = {}

        def fake_create_window(**kwargs):
            captured_kwargs.update(kwargs)
            return MockPywebviewWindow()

        with patch("webview.create_window", side_effect=fake_create_window):
            # Test Dark Mode (default)
            self.api._current_theme = "dark"
            self.api.open_settings()

            self.assertEqual(captured_kwargs.get("title"), "ip+ - Settings")
            self.assertEqual(captured_kwargs.get("width"), 780)
            self.assertEqual(captured_kwargs.get("height"), 580)
            self.assertEqual(captured_kwargs.get("min_size"), (680, 480))
            self.assertTrue(captured_kwargs.get("resizable"))
            self.assertTrue(captured_kwargs.get("frameless"))
            self.assertFalse(captured_kwargs.get("easy_drag"))
            self.assertFalse(captured_kwargs.get("on_top"))
            self.assertEqual(captured_kwargs.get("background_color"), "#18181b")

            url = captured_kwargs.get("url", "")
            match = re.match(r"^http://127\.0\.0\.1:8765/settings\.html\?t=(\d+)$", url)
            self.assertIsNotNone(match, f"Invalid settings URL format: {url}")
            ts = int(match.group(1))
            self.assertAlmostEqual(ts, int(time.time()), delta=5)

            # Test Light Mode background
            self.api.close_settings()
            captured_kwargs.clear()
            self.api._current_theme = "light"
            self.api.open_settings()
            self.assertEqual(captured_kwargs.get("background_color"), "#f6f6f8")

        print("[PASS] Settings URL, cache-busting, and geometry parameters verified")

    def test_03_set_drawer_backward_compatibility(self):
        """Empirically test that set_drawer() maintains backward compatibility:

        - set_drawer(True) delegates to open_settings()
        - set_drawer(False) safely returns {"ok": True, "deprecated": True}
        - _drawer_open remains False
        """
        with patch.object(self.api, "open_settings", return_value={"ok": True, "action": "created"}) as mock_open:
            res_open = self.api.set_drawer(True)
            mock_open.assert_called_once()
            self.assertEqual(res_open.get("action"), "created")
            self.assertFalse(self.api._drawer_open)

            res_close = self.api.set_drawer(False)
            self.assertTrue(res_close.get("ok"))
            self.assertTrue(res_close.get("deprecated"))
            self.assertFalse(self.api._drawer_open)

        print("[PASS] set_drawer backwards compatibility verified")

    def test_04_window_sizing_no_drawer_width_inadvertently_added(self):
        """CRITICAL: Empirically verify that DRAWER_WIDTH (360px) is NEVER added to window dimensions.

        Test matrix:
        1. set_orientation(False): Portrait -> width must be 346 (PORTRAIT_WIDTH), not 706 (346 + 360).
        2. set_orientation(True): Landscape -> width must be 840 (LANDSCAPE_WIDTH_NO_DRAWER), not 1200.
        3. set_orientation(False, drawer_open=True): drawer_open ignored -> width must be 346, not 706.
        4. set_orientation(True, drawer_open=True): drawer_open ignored -> width must be 840, not 1200.
        5. sync_device_aspect(400, drawer_open=True): width must be 400, not 760.
        """
        with patch.object(self.api, "_schedule_reapply_corners"):
            # 1. Portrait default
            res1 = self.api.set_orientation(False)
            self.assertEqual(res1["width"], PORTRAIT_WIDTH)
            self.assertEqual(res1["height"], PORTRAIT_HEIGHT)
            self.assertEqual(self.mock_main_window.width, PORTRAIT_WIDTH)
            self.assertNotEqual(res1["width"], PORTRAIT_WIDTH + DRAWER_WIDTH)

            # 2. Landscape default
            res2 = self.api.set_orientation(True)
            self.assertEqual(res2["width"], LANDSCAPE_WIDTH_NO_DRAWER)
            self.assertEqual(res2["height"], LANDSCAPE_HEIGHT)
            self.assertEqual(self.mock_main_window.width, LANDSCAPE_WIDTH_NO_DRAWER)
            self.assertNotEqual(res2["width"], LANDSCAPE_WIDTH_DRAWER)
            self.assertNotEqual(res2["width"], LANDSCAPE_WIDTH_NO_DRAWER + DRAWER_WIDTH)

            # 3. Portrait with legacy drawer_open=True
            res3 = self.api.set_orientation(False, drawer_open=True)
            self.assertEqual(res3["width"], PORTRAIT_WIDTH)
            self.assertEqual(res3["height"], PORTRAIT_HEIGHT)
            self.assertEqual(self.mock_main_window.width, PORTRAIT_WIDTH)
            self.assertFalse(self.api._drawer_open)

            # 4. Landscape with legacy drawer_open=True
            res4 = self.api.set_orientation(True, drawer_open=True)
            self.assertEqual(res4["width"], LANDSCAPE_WIDTH_NO_DRAWER)
            self.assertEqual(res4["height"], LANDSCAPE_HEIGHT)
            self.assertEqual(self.mock_main_window.width, LANDSCAPE_WIDTH_NO_DRAWER)
            self.assertFalse(self.api._drawer_open)

            # 5. sync_device_aspect with drawer_open=True
            self.api._is_landscape = False
            self.api._is_real_phone = False
            self.api._is_fullscreen = False
            res5 = self.api.sync_device_aspect(display_width=412, drawer_open=True)
            self.assertEqual(res5["width"], 412)
            self.assertEqual(res5["height"], PORTRAIT_HEIGHT)
            self.assertEqual(self.mock_main_window.width, 412)
            self.assertFalse(self.api._drawer_open)
            self.assertNotEqual(res5["width"], 412 + DRAWER_WIDTH)

            # 6. Clamp checks in sync_device_aspect
            res_clamp_min = self.api.sync_device_aspect(display_width=150)
            self.assertEqual(res_clamp_min["width"], 336)  # clamped to MIN 336

            res_clamp_max = self.api.sync_device_aspect(display_width=1200)
            self.assertEqual(res_clamp_max["width"], 600)  # clamped to MAX 600

        print("[PASS] Window sizing logic: DRAWER_WIDTH is NEVER added across all orientations and sync calls")

    def test_05_real_phone_mode_sizing_and_orientation_switch(self):
        """Test sizing behavior when toggling Real Phone mode and switching orientation during Real Phone mode."""
        with patch.object(self.api, "_apply_real_phone_dwm"), \
             patch.object(self.api, "_schedule_reapply_corners"):

            # Enable real phone mode (portrait iPhone 1125 / 2436 aspect)
            res_rp = self.api.set_real_phone_mode(True, aspect=1125.0 / 2436.0)
            self.assertTrue(res_rp["ok"])
            self.assertTrue(res_rp["real_phone"])
            self.assertFalse(res_rp["landscape"])
            rp_w = res_rp["width"]
            rp_h = res_rp["height"]
            self.assertGreater(rp_w, 200)
            self.assertLess(rp_w, 600)
            self.assertEqual(self.mock_main_window.width, rp_w)
            self.assertEqual(self.mock_main_window.height, rp_h)

            # Now rotate to landscape while in Real Phone Mode
            res_rp_land = self.api.set_orientation(True)
            self.assertTrue(res_rp_land["ok"])
            self.assertTrue(res_rp_land["real_phone"])
            self.assertTrue(res_rp_land["landscape"])
            self.assertGreater(res_rp_land["width"], res_rp_land["height"])
            self.assertEqual(self.mock_main_window.width, res_rp_land["width"])

            # Disable Real Phone Mode (should restore standard landscape)
            res_std = self.api.set_real_phone_mode(False)
            self.assertTrue(res_std["ok"])
            self.assertFalse(res_std["real_phone"])
            self.assertEqual(res_std["width"], LANDSCAPE_WIDTH_NO_DRAWER)
            self.assertEqual(res_std["height"], LANDSCAPE_HEIGHT)

            # Rotate back to portrait
            res_port = self.api.set_orientation(False)
            self.assertEqual(res_port["width"], PORTRAIT_WIDTH)
            self.assertEqual(res_port["height"], PORTRAIT_HEIGHT)

        print("[PASS] Real Phone Mode sizing and orientation transitions verified")

    def test_06_adversarial_aspect_ratios_in_real_phone_mode(self):
        """Adversarial stress-test: invalid, negative, extreme, or malformed aspect ratios."""
        with patch.object(self.api, "_apply_real_phone_dwm"):
            # Aspect 0.0 -> Should fall back gracefully to standard iPhone aspect (1125/2436)
            res0 = self.api.set_real_phone_mode(True, aspect=0.0)
            self.assertTrue(res0["ok"])
            self.assertFalse(res0["landscape"])

            # Negative aspect -> Should fall back gracefully
            res_neg = self.api.set_real_phone_mode(True, aspect=-0.5)
            self.assertTrue(res_neg["ok"])
            self.assertFalse(res_neg["landscape"])

            # Extreme aspect (9999.0) -> Out of (0.2, 5.0) bounds, should fallback
            res_ext = self.api.set_real_phone_mode(True, aspect=9999.0)
            self.assertTrue(res_ext["ok"])
            self.assertFalse(res_ext["landscape"])

            # Non-float string representation or None
            res_none = self.api.set_real_phone_mode(True, aspect=None)
            self.assertTrue(res_none["ok"])

        print("[PASS] Adversarial aspect ratios handled robustly with zero exceptions")

    def test_07_resize_window_and_finish_resize(self):
        """Test real-time window resizing and corner settlement."""
        with patch.object(self.api, "_get_hwnd", return_value=12345), \
             patch("handset.gui.api.apply_phone_window_region") as mock_region, \
             patch.object(self.api, "_schedule_reapply_corners") as mock_schedule:
            
            # Active drag frame (is_final=False): should resize & apply region immediately, NOT schedule timers
            res = self.api.resize_window(450, 950, is_final=False)
            self.assertTrue(res["ok"])
            self.assertEqual(res["width"], 450)
            self.assertEqual(res["height"], 950)
            self.assertEqual(self.mock_main_window.width, 450)
            self.assertEqual(self.mock_main_window.height, 950)
            mock_region.assert_called_once()
            mock_schedule.assert_not_called()

            # Final release frame (is_final=True): should schedule reapply corners
            res_final = self.api.resize_window(480, 1020, is_final=True)
            self.assertTrue(res_final["ok"])
            self.assertEqual(res_final["width"], 480)
            self.assertEqual(res_final["height"], 1020)
            mock_schedule.assert_called_once()

            # Explicit finish_window_resize
            mock_schedule.reset_mock()
            res_finish = self.api.finish_window_resize()
            self.assertTrue(res_finish["ok"])
            mock_schedule.assert_called_once()

        print("[PASS] resize_window and finish_window_resize verified")


if __name__ == "__main__":
    unittest.main()
