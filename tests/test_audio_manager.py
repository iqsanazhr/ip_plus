import unittest
from unittest.mock import patch, MagicMock
from handset.audio import AudioManager

class TestAudioManager(unittest.TestCase):
    def setUp(self):
        self.mgr = AudioManager()

    def test_initial_state(self):
        st = self.mgr.status()
        self.assertFalse(st["enabled"])
        self.assertFalse(st["active"])
        self.assertEqual(st["state"], "Off")

    def test_toggle_logic(self):
        with patch.object(self.mgr, 'enable') as mock_enable, \
             patch.object(self.mgr, 'disable') as mock_disable:
            mock_enable.return_value = {"enabled": True, "active": True, "state": "Opened"}
            mock_disable.return_value = {"enabled": False, "active": False, "state": "Off"}

            res = self.mgr.toggle(True)
            mock_enable.assert_called_once()
            self.assertTrue(res["enabled"])

            res2 = self.mgr.toggle(False)
            mock_disable.assert_called_once()
            self.assertFalse(res2["enabled"])

            # Toggle without arguments flips state
            self.mgr._enabled = False
            self.mgr.toggle()
            self.assertEqual(mock_enable.call_count, 2)

    def test_volume_clamp(self):
        with patch.object(self.mgr, 'set_volume', wraps=self.mgr.set_volume):
            # Test volume bounds
            res = self.mgr.set_volume(150)
            self.assertEqual(res["volume"], 100)
            res = self.mgr.set_volume(-10)
            self.assertEqual(res["volume"], 0)

if __name__ == "__main__":
    unittest.main()
