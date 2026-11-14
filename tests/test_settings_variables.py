"""Tests for settings persistence variables and window icon application."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from handset.server import (
    DEFAULT_SETTINGS,
    load_user_settings,
    save_user_settings,
    get_settings_file_path,
)
from handset.gui.dwm import apply_window_icon, set_process_app_user_model_id


class TestSettingsVariablesAndIcon(unittest.TestCase):
    def test_default_settings_schema(self):
        """Verify all essential settings variables are declared in DEFAULT_SETTINGS."""
        expected_keys = [
            "theme",
            "realPhoneMode",
            "realPhoneScaleRatio",
            "realPhonePortraitHeight",
            "realPhoneLandscapeHeight",
            "fitMode",
            "crop",
            "resolution",
            "sharpness",
            "autoRotate",
            "autoRotateGame",
            "audioSinkEnabled",
            "audioVolume",
            "trackpadSpeed",
            "crossPlatformShortcuts",
            "pastePcClipboard",
            "recordingFolder",
            "recordingFps",
            "autoConnectUsb",
            "keepAwake",
        ]
        for key in expected_keys:
            self.assertIn(key, DEFAULT_SETTINGS, f"Key '{key}' missing from DEFAULT_SETTINGS")

    def test_save_and_load_settings_variables(self):
        """Test saving and loading new configuration variables."""
        payload = {
            "theme": "light",
            "realPhoneMode": True,
            "fitMode": "contain",
            "audioVolume": 75,
            "recordingFps": 60,
            "autoConnectUsb": False,
            "keepAwake": True,
            "autoRotateGame": True,
            "trackpadSpeed": 140,
        }
        saved = save_user_settings(payload)
        self.assertEqual(saved["theme"], "light")
        self.assertEqual(saved["realPhoneMode"], True)
        self.assertEqual(saved["fitMode"], "contain")
        self.assertEqual(saved["audioVolume"], 75)
        self.assertEqual(saved["recordingFps"], 60)
        self.assertEqual(saved["autoConnectUsb"], False)
        self.assertEqual(saved["keepAwake"], True)
        self.assertEqual(saved["autoRotateGame"], True)
        self.assertEqual(saved["trackpadSpeed"], 140)

        # Reload and verify persistence
        loaded = load_user_settings(persist_instance=False)
        self.assertEqual(loaded["theme"], "light")
        self.assertEqual(loaded["realPhoneMode"], True)
        self.assertEqual(loaded["audioVolume"], 75)

        # Cleanup: restore dark mode and realPhoneMode False for tests
        save_user_settings({"theme": "dark", "realPhoneMode": False})

    def test_get_settings_file_path_returns_valid_path(self):
        """Ensure get_settings_file_path returns a Path object ending in user_settings.json."""
        p = get_settings_file_path()
        self.assertIsInstance(p, Path)
        self.assertTrue(str(p).endswith("user_settings.json"))

    def test_set_process_app_user_model_id_safe(self):
        """Verify set_process_app_user_model_id does not throw on any platform."""
        res = set_process_app_user_model_id("test.appid.1.0")
        self.assertIsInstance(res, bool)

    def test_apply_window_icon_safe(self):
        """Verify apply_window_icon safely ignores null or invalid handles."""
        self.assertFalse(apply_window_icon(0))
        self.assertFalse(apply_window_icon(-1))
        self.assertFalse(apply_window_icon(None))


if __name__ == "__main__":
    unittest.main()
