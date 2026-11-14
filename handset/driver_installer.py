"""Apple USB Driver Automated Installer Engine for Windows.

Automates the installation of Apple Mobile Device Support (AMDS) and Apple Devices
from Apple's official CDN or Microsoft Store via Windows Package Manager (winget)
or direct Windows Store URI protocol.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import threading
from typing import Any

logger = logging.getLogger("handset.driver_installer")

_INSTALL_LOCK = threading.Lock()
_INSTALL_IN_PROGRESS = False
_INSTALL_STATUS = {"running": False, "success": None, "message": "Idle"}


def is_apple_service_running() -> bool:
    """Check if Apple Mobile Device Service is running or listening."""
    if sys.platform != "win32":
        return True
    try:
        res = subprocess.run(
            ["sc", "query", "Apple Mobile Device Service"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return "RUNNING" in (res.stdout or "")
    except Exception:
        return False


def get_driver_install_status() -> dict[str, Any]:
    """Return the current installation status."""
    with _INSTALL_LOCK:
        return dict(_INSTALL_STATUS)


def trigger_apple_driver_install(preferred_source: str = "auto") -> dict[str, Any]:
    """Start automated background installation of Apple USB drivers.

    preferred_source: 'auto', 'driver' (AppleMobileDeviceSupport), 'store' (Apple Devices)
    """
    global _INSTALL_IN_PROGRESS, _INSTALL_STATUS

    with _INSTALL_LOCK:
        if _INSTALL_IN_PROGRESS:
            return {"ok": True, "in_progress": True, "message": "Installation already in progress"}
        _INSTALL_IN_PROGRESS = True
        _INSTALL_STATUS = {
            "running": True,
            "success": None,
            "message": "Memulai pemasangan driver Apple...",
        }

    thread = threading.Thread(
        target=_run_install_worker,
        args=(preferred_source,),
        name="AppleDriverInstallWorker",
        daemon=True,
    )
    thread.start()
    return {"ok": True, "started": True, "message": "Pemasangan driver Apple dimulai di latar belakang"}


def _run_install_worker(preferred_source: str) -> None:
    global _INSTALL_IN_PROGRESS, _INSTALL_STATUS

    success = False
    message = "Gagal memasang driver Apple."

    try:
        # Check if already running
        if is_apple_service_running():
            success = True
            message = "Layanan Apple Mobile Device sudah aktif."
            return

        winget_path = shutil.which("winget")

        if winget_path:
            # 1. Try official standalone driver from Apple CDN (Apple.AppleMobileDeviceSupport)
            logger.info("Attempting to install Apple.AppleMobileDeviceSupport via winget...")
            with _INSTALL_LOCK:
                _INSTALL_STATUS["message"] = "Mengunduh & memasang Apple Mobile Device Support dari Apple CDN..."

            cmd = [
                winget_path,
                "install",
                "--id",
                "Apple.AppleMobileDeviceSupport",
                "-e",
                "--silent",
                "--accept-package-agreements",
                "--accept-source-agreements",
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
                if proc.returncode == 0 or is_apple_service_running():
                    success = True
                    message = "Apple Mobile Device Support berhasil terpasang!"
            except Exception as e:
                logger.warning("winget Apple.AppleMobileDeviceSupport failed: %s", e)

            # 2. Fallback to Microsoft Store Apple Devices (9NP83LWLPZ9K) if driver package failed
            if not success:
                logger.info("Attempting fallback to Apple Devices via Microsoft Store...")
                with _INSTALL_LOCK:
                    _INSTALL_STATUS["message"] = "Memasang aplikasi Apple Devices dari Microsoft Store..."

                cmd_store = [
                    winget_path,
                    "install",
                    "--id",
                    "9NP83LWLPZ9K",
                    "-s",
                    "msstore",
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                ]
                try:
                    proc2 = subprocess.run(cmd_store, capture_output=True, text=True, timeout=240)
                    if proc2.returncode == 0 or is_apple_service_running():
                        success = True
                        message = "Aplikasi Apple Devices dari Microsoft Store berhasil terpasang!"
                except Exception as e:
                    logger.warning("winget Apple Devices msstore failed: %s", e)

        # 3. Final Fallback: Open Microsoft Store URI protocol directly so user clicks 'Get'
        if not success:
            logger.info("Opening Microsoft Store directly to Apple Devices page...")
            with _INSTALL_LOCK:
                _INSTALL_STATUS["message"] = "Membuka halaman Apple Devices di Microsoft Store..."
            try:
                if sys.platform == "win32":
                    os.startfile("ms-windows-store://pdp/?ProductId=9NP83LWLPZ9K")
                success = True
                message = "Halaman Apple Devices di Microsoft Store telah dibuka. Klik 'Dapatkan' untuk memasang."
            except Exception as e:
                message = f"Gagal membuka Microsoft Store: {e}"

    except Exception as exc:
        logger.error("Driver installer error: %s", exc)
        message = f"Kesalahan instalasi: {exc}"
    finally:
        with _INSTALL_LOCK:
            _INSTALL_IN_PROGRESS = False
            _INSTALL_STATUS = {
                "running": False,
                "success": success,
                "message": message,
            }
