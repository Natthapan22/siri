# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — Windows onefile .exe / macOS .app (onedir)."""

import sys

from PyInstaller.utils.hooks import collect_all

block_cipher = None

edge_datas, edge_binaries, edge_hidden = collect_all("edge_tts")
try:
    aio_datas, aio_binaries, aio_hidden = collect_all("aiohttp")
except Exception:
    aio_datas, aio_binaries, aio_hidden = [], [], []

hidden = [
    "tkinter",
    "tkinter.ttk",
    "tkinter.messagebox",
    "edge_tts",
    "aiohttp",
    "asyncio",
    *edge_hidden,
    *aio_hidden,
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[*edge_binaries, *aio_binaries],
    datas=[*edge_datas, *aio_datas],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "darwin":
    # onedir + .app (recommended on macOS)
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="HourlyVoiceReminder",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="HourlyVoiceReminder",
    )
    app = BUNDLE(
        coll,
        name="HourlyVoiceReminder.app",
        icon=None,
        bundle_identifier="local.hourly.voice.reminder",
        info_plist={
            "CFBundleName": "Hourly Voice Reminder",
            "CFBundleDisplayName": "Hourly Voice Reminder",
            "CFBundleShortVersionString": "1.1.0",
            "NSHighResolutionCapable": True,
            "LSBackgroundOnly": False,
        },
    )
else:
    # Windows: single .exe
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="HourlyVoiceReminder",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
