# -*- mode: python ; coding: utf-8 -*-
import os

onefile = os.environ.get('PIXELLOCK_ONEFILE') == '1'


a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
# Qt 6.12 uses the Windows ICU API. A different icuuc.dll on PATH (e.g.
# Poppler's ICU 78) exports incompatible names and breaks QtCore at startup.
# Let Windows resolve its own ICU; do not ship the accidentally collected pair.
a.binaries = [entry for entry in a.binaries
              if os.path.basename(entry[0]).lower() not in {'icuuc.dll', 'icudt78.dll'}]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries if onefile else [],
    a.datas if onefile else [],
    exclude_binaries=not onefile,
    name='PixelLockPortable' if onefile else 'PixelLock',
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
if not onefile:
    coll = COLLECT(
        exe, a.binaries, a.datas,
        strip=False, upx=True, upx_exclude=[], name='PixelLock',
    )
