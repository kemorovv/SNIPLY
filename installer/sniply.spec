# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification File for SNIPLY (Windows 10 & Windows 11 64-bit).
Produces a distributable one-folder build (`dist/SNIPLY/SNIPLY.exe`) bundling all
icons, logos, QSS themes, English/Russian translation dictionaries, and Qt plugins.
"""

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).resolve().parent
RESOURCES_DIR = PROJECT_ROOT / "resources"
ICON_FILE = RESOURCES_DIR / "logo" / "sniply.ico"

block_cipher = None

datas = [
    (str(RESOURCES_DIR / "icons"), "resources/icons"),
    (str(RESOURCES_DIR / "logo"), "resources/logo"),
    (str(RESOURCES_DIR / "styles"), "resources/styles"),
    (str(RESOURCES_DIR / "translations"), "resources/translations"),
]

hiddenimports = [
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtSvg",
    "PIL",
    "PIL.Image",
    "pygments",
    "pygments.lexers",
    "pygments.formatters",
    "pygments.styles.monokai",
    "sqlite3",
]

a = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "scipy", "pandas"],
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
    name="SNIPLY",
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
    icon=str(ICON_FILE) if ICON_FILE.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SNIPLY",
)
