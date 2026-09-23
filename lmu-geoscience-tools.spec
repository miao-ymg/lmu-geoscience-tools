# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

pyrolite_datas = collect_data_files('pyrolite')

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/tools/qapf/*.yml', 'tools/qapf'),
        ('src/tools/feldspar/*.yml', 'tools/feldspar'),
        ('src/tools/ultramafic/*.yml', 'tools/ultramafic'),
    ] + pyrolite_datas,
    hiddenimports=['pyrolite', 'pyrolite.plot', 'pyrolite.plot.templates', 'PyQt6.QtSvg', 'matplotlib.backends.backend_svg', 'matplotlib.backends.backend_pdf'],
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
        name='GeoPlottr',
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
        name='GeoPlottr',
    )
    
    app = BUNDLE(
        coll,
        name='GeoPlottr.app',
        icon='resources/icons/app-icon.icns',
        bundle_identifier='de.lmu.geoscience-tools',
        info_plist={
            'CFBundleName': 'GeoPlottr',
            'CFBundleDisplayName': 'GeoPlottr',
            'CFBundleExecutable': 'GeoPlottr',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'CFBundleIconFile': 'app-icon.icns',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '11.0',
        },
    )
else:
    # On Windows and Linux, build as a directory (onedir) to avoid the massive 15s self-extraction penalty on every launch
    icon_file = 'resources/icons/app-icon.ico' if sys.platform == 'win32' else 'resources/icons/app-icon.png'
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='lmu-geoscience-tools',
        icon=icon_file,
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
