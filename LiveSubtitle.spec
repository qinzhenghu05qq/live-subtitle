# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for LiveSubtitle (Windows)."""
from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
)

block_cipher = None

datas = [
    ("models", "models"),
    ("argos-packages", "argos-packages"),
]
# argos-translate 运行时依赖 ctranslate2 + sentencepiece + 内嵌资源
datas += collect_data_files("argostranslate")
datas += collect_data_files("ctranslate2")
datas += collect_data_files("sentencepiece")
datas += collect_data_files("vosk")

binaries = []
binaries += collect_dynamic_libs("ctranslate2")
binaries += collect_dynamic_libs("sentencepiece")
binaries += collect_dynamic_libs("vosk")
binaries += collect_dynamic_libs("sounddevice")

hiddenimports = []
hiddenimports += collect_submodules("argostranslate")
hiddenimports += ["sentencepiece", "ctranslate2", "vosk"]


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    name="LiveSubtitle",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                 # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="LiveSubtitle",
)
