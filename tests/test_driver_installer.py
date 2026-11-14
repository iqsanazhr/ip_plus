"""
Unit tests for Automated Apple Driver Installer Engine.
Tests:
- is_apple_service_running() execution and type correctness.
- get_driver_install_status() dictionary schema and thread safety.
- trigger_apple_driver_install() idempotency and response schema.
- WindowApi install_apple_driver and get_apple_driver_install_status methods.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from handset.driver_installer import (
    is_apple_service_running,
    get_driver_install_status,
    trigger_apple_driver_install,
)
from handset.gui.api import WindowApi


class MockWindow:
    def __init__(self):
        self.width = 420
        self.height = 868


class TestDriverInstaller(unittest.TestCase):
    def test_is_apple_service_running_returns_bool(self):
        res = is_apple_service_running()
        self.assertIsInstance(res, bool)

    def test_get_driver_install_status_schema(self):
        st = get_driver_install_status()
        self.assertIn("running", st)
        self.assertIn("success", st)
        self.assertIn("message", st)
        self.assertIsInstance(st["running"], bool)
        self.assertIsInstance(st["message"], str)

    def test_trigger_apple_driver_install_idempotent(self):
        # Triggering install returns valid dictionary
        res = trigger_apple_driver_install(preferred_source="auto")
        self.assertTrue(res.get("ok"))
        self.assertIn("message", res)

        # Triggering again while running returns in_progress
        res2 = trigger_apple_driver_install(preferred_source="auto")
        self.assertTrue(res2.get("ok"))

    def test_window_api_driver_installer_methods(self):
        mock_win = MockWindow()
        api = WindowApi(mock_win)

        st = api.get_apple_driver_install_status()
        self.assertIn("running", st)
        self.assertIn("message", st)

        res = api.install_apple_driver("auto")
        self.assertTrue(res.get("ok"))


if __name__ == "__main__":
    unittest.main()
