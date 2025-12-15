# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/media/sounds/sound.mp3', 'assets/media/sounds'), ('assets/media/icons/shield_extrected.png', 'assets/media/icons'), ('assets/media/figures', 'assets/media/figures')],
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='EyeGuard',
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
    icon=['assets\\media\\icons\\shield_extrected.png'],
)
