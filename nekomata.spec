# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Nekomata desktop app."""

import sys
from pathlib import Path

block_cipher = None

PROJECT_ROOT = Path(SPECPATH)
PKG_DIR = PROJECT_ROOT / "src" / "nekomata"
ICON_DIR = PKG_DIR / "assets" / "icon"
ICON_ICNS = ICON_DIR / "nekomata.icns"
ICON_ICO = ICON_DIR / "nekomata.ico"
APP_ICON = ICON_ICO if sys.platform == "win32" else ICON_ICNS if sys.platform == "darwin" else None

# UPX can corrupt some bundled native DLLs on Windows
_USE_UPX = sys.platform != "win32"

# --- Collect data files ---
#
# Keep this whitelist tight. Runtime bundles need locale/prompt data, web static
# files, optimized card images, and fonts. README-only images and reference
# photos under assets/brand, assets/screenshots, assets/cats, and icon source
# images are intentionally excluded from packaged builds.
# Keep in sync with [tool.setuptools.exclude-package-data] in pyproject.toml.

datas = [
    (str(PKG_DIR / "data"), "data"),
    (str(PKG_DIR / "web" / "static"), "static"),
]

# Card images: include base PNG + _detail.png, exclude _origin.png and contact_sheet.
# Mirrored in pyproject.toml [tool.setuptools.exclude-package-data].
assets_cards = PKG_DIR / "assets" / "cards"
for arcana_dir in sorted(assets_cards.iterdir()):
    if not arcana_dir.is_dir():
        continue
    for f in sorted(arcana_dir.iterdir()):
        if f.suffix == ".png" and "_origin" not in f.name and "contact_sheet" not in f.name:
            datas.append((str(f), f"assets/cards/{arcana_dir.name}"))

# Font files (WOFF2 + TTF)
assets_fonts = PKG_DIR / "assets" / "fonts"
if assets_fonts.is_dir():
    for f in sorted(assets_fonts.iterdir()):
        if f.suffix in (".ttf", ".woff2"):
            datas.append((str(f), "assets/fonts"))

_EXCLUDED_ASSET_PREFIXES = (
    Path("assets/brand"),
    Path("assets/screenshots"),
    Path("assets/cats"),
)
for _src, _dest in datas:
    _dest_path = Path(_dest)
    if any(_dest_path == p or p in _dest_path.parents for p in _EXCLUDED_ASSET_PREFIXES):
        raise RuntimeError(f"Non-runtime asset included in package data: {_src} -> {_dest}")

a = Analysis(
    [str(PROJECT_ROOT / "src" / "nekomata" / "desktop.py")],
    pathex=[str(PROJECT_ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "nekomata",
        "nekomata._paths",
        "nekomata.desktop",
        "nekomata.card.data",
        "nekomata.card.types",
        "nekomata.spread",
        "nekomata.spread.base",
        "nekomata.storage.config",
        "nekomata.web.server",
        "nekomata.ai.interpreter",
        "nekomata.ai.prompts",
        "nekomata.render.styles",
        "uvicorn.logging",
        "uvicorn.lifespan.on",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        *(
            ["webview.platforms.winforms", "webview.platforms.edgechromium"]
            if sys.platform == "win32"
            else []
        ),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "textual",
        "textual_image",
        "tkinter",
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
    a.binaries if sys.platform == "win32" else [],
    a.zipfiles if sys.platform == "win32" else [],
    a.datas if sys.platform == "win32" else [],
    exclude_binaries=sys.platform != "win32",
    name="Nekomata",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=_USE_UPX,
    console=False,
    icon=str(APP_ICON) if APP_ICON else None,
)

if sys.platform != "win32":
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=_USE_UPX,
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
        version="0.1.1",
        info_plist={
            "CFBundleName": "Nekomata",
            "CFBundleDisplayName": "Nekomata",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
