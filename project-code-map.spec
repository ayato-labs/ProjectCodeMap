# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/project_code_map/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('C:/Users/saiha/My_Service/programing/ProjectCodeMap/.venv/Lib/site-packages/tree_sitter_python', 'tree_sitter_python'),
        ('C:/Users/saiha/My_Service/programing/ProjectCodeMap/.venv/Lib/site-packages/tree_sitter_php', 'tree_sitter_php'),
    ],
    hiddenimports=[
        'tree_sitter_python',
        'tree_sitter_php',
    ],
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
    name='project-code-map',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)