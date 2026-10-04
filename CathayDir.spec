# -*- mode: python ; coding: utf-8 -*-
"""CathayDir 打包配置。

一次生成两个 exe，共用同一份 _internal，体积不翻倍：
  - CathayDir PDF横竖排识别工具.exe   窗口版（console=False），双击就用
  - CathayDir命令行.exe               控制台版（console=True），批量 / 存 CSV 用

注意：spec 里不要写 '\' 字面量，会被当成转义吃掉。
"""
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['CathayDir.py'],
    pathex=['.'],
    binaries=[],
    datas=[('app.ico', '.')],
    hiddenimports=collect_submodules('PIL'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'scipy', 'pandas', 'PyQt5', 'PyQt6',
        'pytest', 'notebook', 'PIL.ImageQt',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CathayDir PDF横竖排识别工具',
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
    icon='app.ico',
)

exe_cli = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CathayDir命令行',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)

coll = COLLECT(
    exe_gui,
    exe_cli,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CathayDir',
)
