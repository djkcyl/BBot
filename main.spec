# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import copy_metadata

datas = [
    ('bbot/static/font', 'bbot/static/font'), 
    ('bbot/static/bot_config.exp.yaml', 'bbot/static'), 
    ('bbot/website/static', 'bbot/website/static'), 
    ('bbot/static/mobile_style.js', 'bbot/static'), 
    ('pyproject.toml', './')
]
datas += copy_metadata('graia-ariadne')
datas += copy_metadata('graia-amnesia')
datas += copy_metadata('graia-saya')
datas += copy_metadata('graia-scheduler')
datas += copy_metadata('graia-broadcast')
datas += copy_metadata('creart-graia')
datas += copy_metadata('graiax-playwright')


block_cipher = None


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['graia.creart', 'graia.creart.broadcast', 'graia.creart.saya', 'graia.ariadne.message.commander.creart'],
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='tv.png',
)
