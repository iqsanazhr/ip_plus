# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None
PROJECT_ROOT = Path(SPECPATH).parent.resolve()

datas = [
    (str(PROJECT_ROOT / "handset" / "web"), "handset/web"),
    (str(PROJECT_ROOT / "handset" / "_shims"), "handset/_shims"),
    (str(PROJECT_ROOT / "handset" / "ocr_extractor.ps1"), "handset"),
    (str(PROJECT_ROOT / "assets"), "assets"),
]

binaries = []
hiddenimports = [
    "handset",
    "handset.gui",
    "handset.server",
    "handset.screen",
    "handset.device",
    "handset.audio",
    "handset.wifi",
    "handset.mux",
    "handset.ocr",
    "handset.keyboard",
    "clr",
    "pythonnet",
    "clr_loader",
    "comtypes",
    "comtypes.client",
    "pycaw",
    "pycaw.pycaw",
]

packages_to_collect = [
    "webview",
    "pythonnet",
    "clr_loader",
    "pycaw",
    "comtypes",
    "pymobiledevice3",
    "pmd_pytcp",
    "pytun_pmd3",
    "qh3",
    "pyimg4",
    "ipsw_parser",
    "developer_disk_image",
    "opack2",
    "bpylist2",
    "construct",
    "srptools",
    "ifaddr",
]

for pkg in packages_to_collect:
    try:
        p_datas, p_binaries, p_hidden = collect_all(pkg)
        datas += p_datas
        binaries += p_binaries
        hiddenimports += p_hidden
    except Exception as e:
        print(f"Warning collecting {pkg}: {e}")

a = Analysis(
    [str(PROJECT_ROOT / "handset" / "gui.py")],
    pathex=[str(PROJECT_ROOT), str(PROJECT_ROOT / "handset" / "_shims")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "IPython",
        "jedi",
        "pytest",
        "unittest",
        "av",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

icon_path = str(PROJECT_ROOT / "assets" / "ip_plus.ico")
if not os.path.exists(icon_path):
    icon_path = str(PROJECT_ROOT / "assets" / "iphone_link.ico")

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ip+",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ip+",
)
