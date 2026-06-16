# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('resources/style.qss', 'resources')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    # On macOS, build as onedir (exclude_binaries=True) and wrap in BUNDLE
    exe = EXE(
        pyz,
        a.scripts,
        exclude_binaries=True,
        name='LMU Geoscience Tools',
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
    
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='LMU Geoscience Tools',
    )
    
    app = BUNDLE(
        coll,
        name='LMU Geoscience Tools.app',
        bundle_identifier='de.lmu.geoscience-tools',
        info_plist={
            'CFBundleName': 'LMU Geoscience Tools',
            'CFBundleDisplayName': 'LMU Geoscience Tools',
            'CFBundleExecutable': 'LMU Geoscience Tools',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '11.0',
        },
    )
else:
    # On Windows and Linux, build as a directory (onedir) to avoid the massive 15s self-extraction penalty on every launch
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='lmu-geoscience-tools',
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
        name='lmu-geoscience-tools',
    )
