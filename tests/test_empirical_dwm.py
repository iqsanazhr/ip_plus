"""Empirical Stress Tests for DWM Transparency & WinForms Safety in handset/gui/dwm.py.

Conducted by Challenger 1.
"""

from __future__ import annotations

import ast
import ctypes
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from handset.gui.dwm import (
    apply_dwm_transparency,
    reapply_dwm_rounded_corners,
    find_webview_controls,
    MARGINS,
    ACCENT_POLICY,
    WINCOMPATTRDATA,
)


class TestDwmEmpirical(unittest.TestCase):
    """Stress tests and empirical verifications for DWM module."""

    def test_01_ast_no_form_backcolor_assignment(self):
        """CRITICAL: Empirically verify via AST that form.BackColor is NEVER assigned in dwm.py.

        Assigning form.BackColor in WinForms causes:
        System.ArgumentException: Control does not support transparent background colors.
        """
        dwm_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "handset", "gui", "dwm.py"))
        with open(dwm_file, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
        backcolor_assignments = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Attribute) and target.attr == "BackColor":
                        backcolor_assignments.append(ast.unparse(target))

        self.assertEqual(
            len(backcolor_assignments),
            0,
            f"VULNERABILITY DETECTED: form.BackColor assignment found in dwm.py: {backcolor_assignments}",
        )
        print("[PASS] AST check: Zero form.BackColor assignments exist in dwm.py")

    def test_02_find_webview_controls_resilience(self):
        """Stress-test find_webview_controls with edge cases and malformed trees."""
        # Case 1: None
        self.assertEqual(find_webview_controls(None), [])

        # Case 2: Direct control with DefaultBackgroundColor
        c1 = MagicMock()
        c1.DefaultBackgroundColor = 0
        c1.browser = None
        c1.Controls = []
        res = find_webview_controls(c1)
        self.assertIn(c1, res)

        # Case 3: Nested controls via browser.webview
        c2 = MagicMock()
        del c2.DefaultBackgroundColor  # Not directly on parent
        wv = MagicMock()
        wv.DefaultBackgroundColor = 0
        c2.browser.webview = wv
        c2.Controls = []
        res = find_webview_controls(c2)
        self.assertIn(wv, res)

        # Case 4: Deep tree with multiple controls and malformed Controls iterable
        c3 = MagicMock()
        del c3.DefaultBackgroundColor
        c3.browser = None

        class BadControls:
            def __iter__(self):
                raise RuntimeError("Corrupted WinForms control collection")

        c3.Controls = BadControls()
        # Should not raise exception
        res = find_webview_controls(c3)
        self.assertEqual(res, [])

        print("[PASS] find_webview_controls edge cases handled gracefully without exceptions")

    def test_03_dwm_transparency_mode_switches(self):
        """Empirically test mode switching between Standard and Real Phone modes."""
        recorded_calls = []

        mock_dwmapi = MagicMock()
        mock_user32 = MagicMock()

        def fake_DwmSetWindowAttribute(hwnd, attr, p_val, size):
            val = ctypes.cast(p_val, ctypes.POINTER(ctypes.c_int)).contents.value
            recorded_calls.append(("DwmSetWindowAttribute", attr, val))
            return 0

        def fake_DwmExtendFrameIntoClientArea(hwnd, p_margins):
            m = ctypes.cast(p_margins, ctypes.POINTER(MARGINS)).contents
            recorded_calls.append(("DwmExtendFrameIntoClientArea", (m.cxLeftWidth, m.cxRightWidth, m.cyTopHeight, m.cyBottomHeight)))
            return 0

        def fake_SetWindowCompositionAttribute(hwnd, p_data):
            data = ctypes.cast(p_data, ctypes.POINTER(WINCOMPATTRDATA)).contents
            accent = ctypes.cast(data.Data, ctypes.POINTER(ACCENT_POLICY)).contents
            recorded_calls.append(("SetWindowCompositionAttribute", data.Attribute, (accent.AccentState, accent.AccentFlags, hex(accent.GradientColor), accent.AnimationId)))
            return 1

        mock_dwmapi.DwmSetWindowAttribute.side_effect = fake_DwmSetWindowAttribute
        mock_dwmapi.DwmExtendFrameIntoClientArea.side_effect = fake_DwmExtendFrameIntoClientArea
        mock_user32.SetWindowCompositionAttribute.side_effect = fake_SetWindowCompositionAttribute

        fake_form = MagicMock()
        fake_form.InvokeRequired = False
        fake_wv = MagicMock()
        fake_wv.DefaultBackgroundColor = 0
        fake_form.Controls = [fake_wv]

        mock_system = MagicMock()
        mock_system.Drawing.Color.FromArgb.return_value = 0
        mock_winforms = MagicMock()

        mock_winforms_module = MagicMock()
        mock_winforms_module.BrowserView.instances = {1: fake_form}

        with patch("ctypes.windll.dwmapi", mock_dwmapi), \
             patch("ctypes.windll.user32", mock_user32), \
             patch.dict("sys.modules", {
                 "webview.platforms.winforms": mock_winforms_module,
                 "System": mock_system,
                 "System.Drawing": mock_system.Drawing,
                 "System.Windows.Forms": mock_winforms,
             }):

            # --- Switch 1: Standard Mode (Dark) ---
            recorded_calls.clear()
            apply_dwm_transparency(12345, is_real_phone=False, current_theme="dark")
            # Verify margins == (-1, -1, -1, -1)
            self.assertIn(("DwmExtendFrameIntoClientArea", (-1, -1, -1, -1)), recorded_calls)
            # Verify DWMWCP_ROUND == 2
            self.assertIn(("DwmSetWindowAttribute", 33, 2), recorded_calls)
            # Verify ACCENT_ENABLE_ACRYLICBLURBEHIND == 4
            accent_call = [c for c in recorded_calls if c[0] == "SetWindowCompositionAttribute"][0]
            self.assertEqual(accent_call[2][0], 4)  # AccentState == 4

            # --- Switch 2: Real Phone Mode (Dark) ---
            recorded_calls.clear()
            apply_dwm_transparency(12345, is_real_phone=True, current_theme="dark")
            # Verify margins == (0, 0, 0, 0)
            self.assertIn(("DwmExtendFrameIntoClientArea", (0, 0, 0, 0)), recorded_calls)
            # Verify DWMWCP_DONOTROUND == 1
            self.assertIn(("DwmSetWindowAttribute", 33, 1), recorded_calls)
            # Verify ACCENT_DISABLED == 0
            accent_call = [c for c in recorded_calls if c[0] == "SetWindowCompositionAttribute"][0]
            self.assertEqual(accent_call[2][0], 0)  # AccentState == 0

            # --- Switch 3: Transition Back to Standard Mode (Light Theme) ---
            recorded_calls.clear()
            apply_dwm_transparency(12345, is_real_phone=False, current_theme="light")
            self.assertIn(("DwmExtendFrameIntoClientArea", (-1, -1, -1, -1)), recorded_calls)
            self.assertIn(("DwmSetWindowAttribute", 33, 2), recorded_calls)
            # Light mode frame attr: 20 -> 0
            self.assertIn(("DwmSetWindowAttribute", 20, 0), recorded_calls)
            accent_call = [c for c in recorded_calls if c[0] == "SetWindowCompositionAttribute"][0]
            self.assertEqual(accent_call[2][0], 4)  # Acrylic blur
            self.assertEqual(accent_call[2][2], "0x45f4f2f0")  # Light gradient

            # --- Switch 4: Transition Back to Real Phone Mode (Light Theme) ---
            recorded_calls.clear()
            apply_dwm_transparency(12345, is_real_phone=True, current_theme="light")
            self.assertIn(("DwmExtendFrameIntoClientArea", (0, 0, 0, 0)), recorded_calls)
            self.assertIn(("DwmSetWindowAttribute", 33, 1), recorded_calls)
            accent_call = [c for c in recorded_calls if c[0] == "SetWindowCompositionAttribute"][0]
            self.assertEqual(accent_call[2][0], 0)  # ACCENT_DISABLED

        print("[PASS] DWM transparency toggles: margins, accent policy, and corner preferences verified")

    def test_04_stress_rapid_mode_toggles(self):
        """Stress-test 100 rapid mode toggles to verify stability and zero state pollution."""
        mock_dwmapi = MagicMock()
        mock_user32 = MagicMock()
        fake_form = MagicMock()
        fake_form.InvokeRequired = False
        fake_wv = MagicMock()
        fake_form.Controls = [fake_wv]

        mock_system = MagicMock()
        mock_system.Drawing.Color.FromArgb.return_value = 0
        mock_winforms = MagicMock()

        mock_winforms_module = MagicMock()
        mock_winforms_module.BrowserView.instances = {1: fake_form}

        with patch("ctypes.windll.dwmapi", mock_dwmapi), \
             patch("ctypes.windll.user32", mock_user32), \
             patch.dict("sys.modules", {
                 "webview.platforms.winforms": mock_winforms_module,
                 "System": mock_system,
                 "System.Drawing": mock_system.Drawing,
                 "System.Windows.Forms": mock_winforms,
             }):

            for i in range(100):
                is_rp = (i % 2 == 0)
                theme = "dark" if (i % 4 < 2) else "light"
                apply_dwm_transparency(99999, is_real_phone=is_rp, current_theme=theme)

            # Invalidate should have been called 100 times
            self.assertEqual(fake_form.Invalidate.call_count, 100)

        print("[PASS] 100 rapid mode toggles executed without failure")

    def test_05_reapply_dwm_rounded_corners_guards(self):
        """Verify reapply_dwm_rounded_corners respects guards for Real Phone mode and null HWND."""
        mock_dwmapi = MagicMock()
        mock_user32 = MagicMock()

        with patch("ctypes.windll.dwmapi", mock_dwmapi), \
             patch("ctypes.windll.user32", mock_user32):

            # Guard 1: hwnd is None or 0
            reapply_dwm_rounded_corners(None, is_real_phone=False)
            reapply_dwm_rounded_corners(0, is_real_phone=False)
            mock_dwmapi.DwmSetWindowAttribute.assert_not_called()

            # Guard 2: is_real_phone is True -> MUST NOT TOUCH CORNERS
            reapply_dwm_rounded_corners(54321, is_real_phone=True)
            mock_dwmapi.DwmSetWindowAttribute.assert_not_called()

            # Normal Standard Mode: SHOULD apply rounding
            reapply_dwm_rounded_corners(54321, is_real_phone=False)
            mock_dwmapi.DwmSetWindowAttribute.assert_called_once()

        print("[PASS] reapply_dwm_rounded_corners guards verified")


if __name__ == "__main__":
    unittest.main()
