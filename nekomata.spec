# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Nekomata desktop app."""

import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH)
ICON_DIR = PROJECT_ROOT / "assets" / "icon"
ICON_ICNS = ICON_DIR / "nekomata.icns"
ICON_ICO = ICON_DIR / "nekomata.ico"
APP_ICON = ICON_ICO if sys.platform == "win32" else ICON_ICNS if sys.platform == "darwin" else None

# --- Collect data files ---

datas = [
    (str(PROJECT_ROOT / "data"), "data"),
    (str(PROJECT_ROOT / "src" / "nekomata" / "web" / "static"), "static"),
]

# Card images: include base PNG + _detail.png, exclude _origin.png (262MB) and contact_sheet
assets_cards = PROJECT_ROOT / "assets" / "cards"
for arcana_dir in sorted(assets_cards.iterdir()):
    if not arcana_dir.is_dir():
        continue
    for f in sorted(arcana_dir.iterdir()):
        if f.suffix == ".png" and "_origin" not in f.name and "contact_sheet" not in f.name:
            datas.append((str(f), f"assets/cards/{arcana_dir.name}"))

a = Analysis(
    [str(PROJECT_ROOT / "src" / "nekomata" / "desktop.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "nekomata",
        "nekomata._paths",
        "nekomata.desktop",
        "nekomata.strings",
        "nekomata.card.data",
        "nekomata.card.types",
        "nekomata.spread",
        "nekomata.spread.base",
        "nekomata.spread.single",
        "nekomata.spread.three_card",
        "nekomata.spread.five_card",
        "nekomata.storage.config",
        "nekomata.web.server",
        "nekomata.ai.interpreter",
        "nekomata.ai.prompts",
        "nekomata.render.styles",
        "uvicorn.logging",
        "uvicorn.lifespan.on",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "webview.platforms.edgechromium",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "textual",
        "textual_image",
        "rich",
        "PIL",
        "tkinter",
        "clr",
        "pythonnet",
        "matplotlib",
        "numpy",
        "scipy",
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
    name="Nekomata",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=str(APP_ICON) if APP_ICON else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Nekomata",
)

# macOS .app bundle (skipped on other platforms)
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Nekomata.app",
        icon=str(ICON_ICNS),
        bundle_identifier="com.nekomata.app",
        version="0.1.0",
        info_plist={
            "CFBundleName": "Nekomata",
            "CFBundleDisplayName": "Nekomata 猫又",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
