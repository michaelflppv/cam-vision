#!/usr/bin/env python3
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

project_root = Path(SPECPATH).resolve().parent

datas = [
    (str(project_root / "data"), "resources/data"),
    (str(project_root / "weights"), "resources/weights"),
    (
        str(project_root / "cam_vision" / "qt_ui" / "styles" / "stylesheet.qss"),
        "cam_vision/qt_ui/styles",
    ),
]

tesseract_dir = os.environ.get("SECUREVISION_TESSERACT_DIR")
if tesseract_dir:
    tesseract_path = Path(tesseract_dir).expanduser().resolve()
    if tesseract_path.exists():
        datas.append((str(tesseract_path), "resources/tesseract"))
    else:
        print(f"[spec] Skipping tesseract bundle; path not found: {tesseract_path}")

insightface_dir = os.environ.get("SECUREVISION_INSIGHTFACE_DIR")
if insightface_dir:
    insightface_path = Path(insightface_dir).expanduser().resolve()
    if insightface_path.exists():
        datas.append((str(insightface_path), "resources/insightface"))
    else:
        print(f"[spec] Skipping InsightFace bundle; path not found: {insightface_path}")

hiddenimports = []
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("insightface")
hiddenimports += collect_submodules("onnxruntime")
hiddenimports += collect_submodules("pydantic_settings")
hiddenimports += collect_submodules("sqlmodel")
hiddenimports += collect_submodules("ultralytics")
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("websockets")

binaries = []
binaries += collect_dynamic_libs("onnxruntime")
binaries += collect_dynamic_libs("cv2")

block_cipher = None

a = Analysis(
    [str(project_root / "cam_vision" / "cli" / "run_desktop_app.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "pytest_asyncio", "matplotlib", "seaborn", "jupyter"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="SecureVision",
    debug=False,
    bootloader_ignore_signals=False,
    exclude_binaries=True,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if os.name == "nt":
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="SecureVision",
    )
elif sys.platform == "darwin":
    coll = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name="SecureVision.app",
        bundle_identifier="local.securevision",
    )
else:
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="SecureVision",
    )
