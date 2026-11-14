"""iPhone Link - Real Phone Mode Dimension & Layout Calculations."""

from __future__ import annotations

import ctypes
from typing import Any


def calculate_real_phone_dimensions(aspect: float = 0.0, is_landscape: bool = False) -> tuple[int, int]:
    """Calculate authentic 1:1 physical iPhone dimensions based on display aspect ratio and monitor size."""
    user32 = getattr(ctypes.windll, "user32", None) if hasattr(ctypes, "windll") else None
    sh = user32.GetSystemMetrics(1) if user32 else 1080
    sw = user32.GetSystemMetrics(0) if user32 else 1920

    asp = float(aspect) if (aspect and 0.2 < float(aspect) < 5.0) else (1125.0 / 2436.0)

    # Calibrated 12px Space Black Titanium border on all 4 sides = 24px bezel total
    bezel = 24

    if asp > 1.0 or is_landscape:
        # Landscape Mode
        if asp < 1.0:
            asp = 1.0 / asp
        target_h = min(430, max(300, sh - 200))
        inner_h = max(100, target_h - bezel)
        inner_w = int(round(inner_h * asp))
        target_w = inner_w + bezel
        if target_w > (sw - 60):
            target_w = sw - 60
            inner_w = max(100, target_w - bezel)
            inner_h = int(round(inner_w / asp))
            target_h = inner_h + bezel
    else:
        # Portrait Mode
        if asp > 1.0:
            asp = 1.0 / asp
        target_h = min(820, sh - 100)
        inner_h = max(100, target_h - bezel)
        inner_w = int(round(inner_h * asp))
        target_w = inner_w + bezel

    return target_w, target_h
