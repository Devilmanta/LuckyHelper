# -*- mode: python ; coding: utf-8 -*-
"""
LuckyHelper - PyInstaller Spec File
Builds a single-folder Windows executable (onedir mode for faster startup).
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Collect all PyQt6 plugins needed for a proper dark-theme app ──────────────
qt_plugins = collect_data_files("PyQt6", includes=["Qt6/plugins/*"])

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        # Include our assets folder (icon, etc.)
        ("assets", "assets"),
    ] + qt_plugins,
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "PyQt6.sip",
        "sqlite3",
        "database",
        "database.db_manager",
        "ui",
        "ui.main_window",
        "ui.sidebar",
        "ui.styles",
        "ui.calendar_view",
        "ui.trade_dialog",
        "ui.statistics_view",
        "ui.risk_calculator",
        "ui.avg_cost_calculator",
        "ui.winrate_calculator",
        "ui.settings_view",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PIL",         # not needed at runtime
        "unittest",
        "email",
        "html",
        "http",
        "urllib",
        "xml",
        "xmlrpc",
        "pydoc",
        "doctest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LuckyHelper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,           # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets\\icon.ico",
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LuckyHelper",
)
