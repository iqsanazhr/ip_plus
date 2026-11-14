"""
Unit tests for Real Phone Scaling Persistence and Screen Recording Engine.
Tests:
- Default settings contain recordingFolder, realPhoneScaleRatio, realPhonePortraitHeight, realPhoneLandscapeHeight.
- save_user_settings correctly persists and validates custom scale ratio and recording folder.
- calculate_real_phone_dimensions preserves proportional bezel and scaling math.
- WindowApi methods get_real_phone_scale, reset_real_phone_scale, get_recording_folder, save_recording.
- Base64 data URL handling with and without prefix for clean video writing.
"""

import os
import sys
import json
import base64
import tempfile
import unittest
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handset.server import (
    DEFAULT_SETTINGS,
    load_user_settings,
    save_user_settings,
    SETTINGS_FILE,
)
from handset.gui.real_phone import calculate_real_phone_dimensions
from handset.gui.api import WindowApi


class MockWindow:
    def __init__(self, width=420, height=868):
        self.width = width
        self.height = height
        self.x = 100
        self.y = 100

    def resize(self, w, h):
        self.width = int(w)
        self.height = int(h)

    def move(self, x, y):
        self.x = int(x)
        self.y = int(y)


class TestRealPhoneAndRecording(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self._temp_settings = Path(self._temp_dir.name) / "test_user_settings.json"
        import handset.server as srv
        self._orig_settings_file = srv.SETTINGS_FILE
        srv.SETTINGS_FILE = self._temp_settings
        self._orig_get_settings_file_path = srv.get_settings_file_path
        srv.get_settings_file_path = lambda: self._temp_settings

    def tearDown(self):
        import handset.server as srv
        srv.SETTINGS_FILE = self._orig_settings_file
        srv.get_settings_file_path = self._orig_get_settings_file_path
        self._temp_dir.cleanup()

    def test_default_settings_include_real_phone_and_recording(self):
        st = load_user_settings()
        self.assertIn("recordingFolder", st)
        self.assertIn("realPhoneScaleRatio", st)
        self.assertIn("realPhonePortraitHeight", st)
        self.assertIn("realPhoneLandscapeHeight", st)
        self.assertEqual(st["realPhoneScaleRatio"], 1.0)
        self.assertEqual(st["realPhonePortraitHeight"], 820)
        self.assertEqual(st["realPhoneLandscapeHeight"], 430)

    def test_save_and_load_real_phone_scale_settings(self):
        new_settings = {
            "realPhoneScaleRatio": 1.35,
            "realPhonePortraitHeight": 980,
            "realPhoneLandscapeHeight": 520,
        }
        saved = save_user_settings(new_settings)
        self.assertAlmostEqual(saved["realPhoneScaleRatio"], 1.35)
        self.assertEqual(saved["realPhonePortraitHeight"], 980)
        self.assertEqual(saved["realPhoneLandscapeHeight"], 520)

        # Reload from disk
        loaded = load_user_settings()
        self.assertAlmostEqual(loaded["realPhoneScaleRatio"], 1.35)
        self.assertEqual(loaded["realPhonePortraitHeight"], 980)
        self.assertEqual(loaded["realPhoneLandscapeHeight"], 520)

    def test_calculate_real_phone_dimensions_scaling(self):
        # 1.0 base ratio
        w1, h1 = calculate_real_phone_dimensions(aspect=0.0, is_landscape=False, scale_ratio=1.0)
        self.assertGreater(h1, 360)
        self.assertGreater(w1, 100)

        # 1.25 scale ratio should produce larger dimensions or hit screen bounds safely
        w125, h125 = calculate_real_phone_dimensions(aspect=0.0, is_landscape=False, scale_ratio=1.25)
        self.assertGreaterEqual(h125, h1)
        self.assertGreaterEqual(w125, w1)

        # Custom explicit height
        w_custom, h_custom = calculate_real_phone_dimensions(aspect=0.0, is_landscape=False, custom_height=750)
        self.assertEqual(h_custom, 750)
        self.assertGreater(w_custom, 100)

        # Landscape scaling
        wl, hl = calculate_real_phone_dimensions(aspect=0.0, is_landscape=True, scale_ratio=1.0)
        self.assertGreaterEqual(hl, 240)
        self.assertGreater(wl, hl)

    def test_window_api_real_phone_scale_and_reset(self):
        mock_win = MockWindow()
        api = WindowApi(mock_win)

        # Initial scale
        scale_info = api.get_real_phone_scale()
        self.assertTrue(scale_info["ok"])
        self.assertEqual(scale_info["scale_ratio"], 1.0)

        # Reset scale
        reset_res = api.reset_real_phone_scale()
        self.assertTrue(reset_res["ok"])
        self.assertEqual(reset_res["scale_ratio"], 1.0)

    def test_save_recording_with_data_url_prefix(self):
        mock_win = MockWindow()
        api = WindowApi(mock_win)

        rec_dir = Path(self._temp_dir.name) / "recordings"
        save_user_settings({"recordingFolder": str(rec_dir)})

        dummy_bytes = b"RIFF....WEBM-TEST-BYTES-12345678"
        b64_content = base64.b64encode(dummy_bytes).decode("ascii")
        data_url = f"data:video/webm;codecs=vp9;base64,{b64_content}"

        res = api.save_recording(data_url, "video/webm")
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("success"))

        saved_file = Path(res["path"])
        self.assertTrue(saved_file.exists())
        self.assertEqual(saved_file.read_bytes(), dummy_bytes)
        self.assertTrue(res["filename"].endswith(".webm"))

    def test_save_recording_mp4(self):
        mock_win = MockWindow()
        api = WindowApi(mock_win)

        rec_dir = Path(self._temp_dir.name) / "recordings_mp4"
        save_user_settings({"recordingFolder": str(rec_dir)})

        dummy_bytes = b"MP4-SIMULATED-VIDEO-CHUNKS"
        b64_content = base64.b64encode(dummy_bytes).decode("ascii")

        res = api.save_recording(b64_content, "video/mp4")
        self.assertTrue(res.get("ok"))
        self.assertTrue(res.get("success"))

        saved_file = Path(res["path"])
        self.assertTrue(saved_file.exists())
        self.assertEqual(saved_file.read_bytes(), dummy_bytes)
        self.assertTrue(res["filename"].endswith(".mp4"))


if __name__ == "__main__":
    unittest.main()
