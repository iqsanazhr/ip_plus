"""Concurrency and Adversarial Edge-Case Stress Testing for WindowApi & DWM.

Conducted by Challenger 1.
Tests:
1. Concurrent multi-threaded invocations of open_settings() - testing unprotected race conditions vs serialized locks.
2. Disposed Form objects in BrowserView.instances (ObjectDisposedException resilience).
3. Null HWND, invalid window handles, and missing window references.
4. Rapid interleaved state transitions across themes, real phone modes, and fullscreen toggles.
"""

from __future__ import annotations

import concurrent.futures
import os
import sys
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from handset.gui.api import WindowApi
from handset.gui.dwm import apply_dwm_transparency, reapply_dwm_rounded_corners


class MockEvent:
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
    def __init__(self, title="test"):
        self.title = title
        self.width = 346
        self.height = 832
        self.uid = "test-concurrent-uid"
        self.events = MagicMock()
        self.events.closed = MockEvent()
        self.show = MagicMock()
        self.restore = MagicMock()
        self.destroy = MagicMock()
        self.resize = MagicMock()


class TestConcurrencyStressEmpirical(unittest.TestCase):
    """Adversarial stress-test cases."""

    def test_01_sequential_and_rapid_burst_open_settings(self):
        """Test sequential invocations vs rapid bursts."""
        api = WindowApi(host="127.0.0.1", port=8765)
        created_count = 0

        def fake_create_window(**kwargs):
            nonlocal created_count
            created_count += 1
            win = MockPywebviewWindow(title=kwargs.get("title"))
            return win

        with patch("webview.create_window", side_effect=fake_create_window):
            # Sequential: 5 calls in sequence
            for i in range(5):
                res = api.open_settings()
                if i == 0:
                    self.assertEqual(res["action"], "created")
                else:
                    self.assertEqual(res["action"], "focused")
            self.assertEqual(created_count, 1, "Sequential calls must create exactly 1 window")

        print("[PASS] Sequential open_settings calls created exactly 1 window and focused 4 times")

    def test_02_concurrent_race_condition_demonstration(self):
        """Demonstrate that concurrent un-locked threads can enter create_window before assignment.

        This identifies the exact thread-safety caveat for the singleton pattern.
        """
        api = WindowApi(host="127.0.0.1", port=8765)
        created_count = 0

        def fake_create_window(**kwargs):
            nonlocal created_count
            time.sleep(0.01)  # Window creation latency
            created_count += 1
            win = MockPywebviewWindow(title=kwargs.get("title"))
            return win

        with patch("webview.create_window", side_effect=fake_create_window):
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(api.open_settings) for _ in range(5)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            actions = [r["action"] for r in results]
            # When unprotected by a mutex, multiple threads detect _settings_window as None
            race_condition_detected = (created_count > 1)
            print(f"  Concurrent test: created_count={created_count}, actions={actions}")
            if race_condition_detected:
                print("  [FINDING CONFIRMED] Concurrency vulnerability: open_settings() lacks a threading.Lock(), "
                      "allowing simultaneous rapid requests to instantiate multiple window handles.")

    def test_03_disposed_forms_in_browserview_instances(self):
        """Verify DWM and api._get_hwnd safely handle disposed or broken WinForms Form handles."""
        api = WindowApi(host="127.0.0.1", port=8765)

        class DisposedForm:
            @property
            def Handle(self):
                raise RuntimeError("System.ObjectDisposedException: Cannot access a disposed object.")

        mock_winforms_module = MagicMock()
        mock_winforms_module.BrowserView.instances = {99: DisposedForm()}

        with patch.dict("sys.modules", {"webview.platforms.winforms": mock_winforms_module}):
            hwnd = api._get_hwnd()
            print(f"  _get_hwnd returned: {hwnd} without raising unhandled exception")
            apply_dwm_transparency(1234, is_real_phone=True, current_theme="dark")

        print("[PASS] Disposed WinForms Form handled with zero unhandled exceptions")

    def test_04_interleaved_state_chaos_monkey(self):
        """Chaos Monkey: rapidly alternate orientation, theme, fullscreen, and real phone mode."""
        api = WindowApi(host="127.0.0.1", port=8765)
        mock_win = MockPywebviewWindow()
        api.set_window(mock_win)

        with patch.object(api, "_apply_real_phone_dwm"), \
             patch.object(api, "_schedule_reapply_corners"), \
             patch("webview.create_window", return_value=MockPywebviewWindow()):

            import random
            random.seed(42)

            for step in range(100):
                op = random.choice([
                    lambda: api.set_orientation(random.choice([True, False])),
                    lambda: api.set_theme(random.choice(["light", "dark"])),
                    lambda: api.set_real_phone_mode(random.choice([True, False]), aspect=random.uniform(0.3, 2.5)),
                    lambda: api.sync_device_aspect(random.randint(300, 700)),
                    lambda: api.set_drawer(random.choice([True, False])),
                ])
                res = op()
                self.assertTrue(res.get("ok"), f"Failed at step {step}: {res}")

        print("[PASS] 100 interleaved state transitions completed cleanly")


if __name__ == "__main__":
    unittest.main()
