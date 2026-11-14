"""iPhone Link - Process Isolation, Job Objects & Anti-Zombie Management."""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .config import REPO_ROOT, DEFAULT_HOST, DEFAULT_PORT

_SERVER_PROCESS: subprocess.Popen | None = None
_SERVER_JOB_OBJECT: Any = None


def make_child_job_object() -> Any:
    """Create a Win32 Job Object configured to kill child processes when parent terminates."""
    if sys.platform != "win32":
        return None
    try:
        kernel32 = ctypes.windll.kernel32
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
                ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryLimit", ctypes.c_size_t),
                ("PeakJobMemoryLimit", ctypes.c_size_t),
            ]

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        kernel32.SetInformationJobObject(
            job, 9, ctypes.byref(info), ctypes.sizeof(info)  # JobObjectExtendedLimitInformation = 9
        )
        return job
    except Exception:
        return None


def is_port_listening(host: str, port: int) -> bool:
    """Check if TCP port is active and responding."""
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def ensure_backend_server_running(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 10.0) -> None:
    """Spawn backend server child process in background if not already running."""
    global _SERVER_PROCESS, _SERVER_JOB_OBJECT

    if is_port_listening(host, port):
        return

    python_exe = sys.executable
    cmd = [python_exe, "-m", "handset", "--server-child", "--host", host, "--port", str(port)]

    creationflags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        creationflags=creationflags,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _SERVER_PROCESS = proc

    job = make_child_job_object()
    if job and sys.platform == "win32":
        try:
            ctypes.windll.kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(proc._handle))
            _SERVER_JOB_OBJECT = job
        except Exception:
            pass

    start_t = time.time()
    while time.time() - start_t < timeout:
        if is_port_listening(host, port):
            return
        time.sleep(0.1)


def shutdown_backend_server() -> None:
    """Safely terminate backend server process on application exit."""
    global _SERVER_PROCESS
    if _SERVER_PROCESS and _SERVER_PROCESS.poll() is None:
        try:
            _SERVER_PROCESS.terminate()
            _SERVER_PROCESS.wait(timeout=2.0)
        except Exception:
            try:
                _SERVER_PROCESS.kill()
            except Exception:
                pass
        _SERVER_PROCESS = None
