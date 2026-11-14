import unittest
import json
from pathlib import Path
from handset.server import DEFAULT_SETTINGS, save_user_settings, load_user_settings, get_settings_file_path
from handset.screen import update_stream_resolution

class TestResolutionSettings(unittest.TestCase):
    def setUp(self):
        self.settings_path = get_settings_file_path()
        if self.settings_path.is_file():
            self._backup = self.settings_path.read_text(encoding="utf-8")
        else:
            self._backup = None

    def tearDown(self):
        if self._backup is not None:
            self.settings_path.write_text(self._backup, encoding="utf-8")
        elif self.settings_path.is_file():
            self.settings_path.unlink()

    def test_default_settings_contains_resolution_and_sharpness(self):
        self.assertIn("resolution", DEFAULT_SETTINGS)
        self.assertIn("sharpness", DEFAULT_SETTINGS)
        self.assertEqual(DEFAULT_SETTINGS["resolution"], "1080p")
        self.assertEqual(DEFAULT_SETTINGS["sharpness"], "crisp")

    def test_save_user_settings_resolution_tiers(self):
        # 720p
        res = save_user_settings({"resolution": "720p"})
        self.assertEqual(res["resolution"], "720p")

        # 1080p
        res = save_user_settings({"resolution": "1080p"})
        self.assertEqual(res["resolution"], "1080p")

        # 2K / 1440p
        res = save_user_settings({"resolution": "2k"})
        self.assertEqual(res["resolution"], "2k")
        res = save_user_settings({"resolution": "1440p"})
        self.assertEqual(res["resolution"], "2k")

        # 3K
        res = save_user_settings({"resolution": "3k"})
        self.assertEqual(res["resolution"], "3k")

        # 4K
        res = save_user_settings({"resolution": "4k"})
        self.assertEqual(res["resolution"], "4k")

        # Native
        res = save_user_settings({"resolution": "native"})
        self.assertEqual(res["resolution"], "native")

    def test_save_user_settings_sharpness(self):
        res = save_user_settings({"sharpness": "crisp"})
        self.assertEqual(res["sharpness"], "crisp")
        res = save_user_settings({"sharpness": "standard"})
        self.assertEqual(res["sharpness"], "standard")

    def test_update_stream_resolution_invocations(self):
        self.assertTrue(update_stream_resolution("720p"))
        self.assertTrue(update_stream_resolution("1080p"))
        self.assertTrue(update_stream_resolution("2k"))
        self.assertTrue(update_stream_resolution("3k"))
        self.assertTrue(update_stream_resolution("4k"))
        self.assertTrue(update_stream_resolution("native"))

if __name__ == "__main__":
    unittest.main()
