from pathlib import Path
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata


root = Path(os.environ["MTGA_PROJECT_ROOT"]).resolve()
icon_dir = root / "build" / "icons"
icon_path = icon_dir / ("app.ico" if sys.platform.startswith("win") else "app.icns")
hidden_imports = collect_submodules("mtga_deck_downloader.providers")
data_files = collect_data_files("mtga_deck_downloader")
data_files += copy_metadata("mtga-deck-downloader")

a = Analysis(
    [str(root / "src" / "mtga_deck_downloader" / "__main__.py")],
    pathex=[str(root / "src")],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="mtga-deck-downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=os.environ.get("MACOS_SIGNING_IDENTITY") or None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="mtga-deck-downloader",
)
