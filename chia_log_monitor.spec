# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\PycharmProjects\\Chia_Log_Monitor\\chia_log_monitor.py'],
    pathex=[],
    binaries=[('C:\\PycharmProjects\\Chia_Log_Monitor\\.venv\\Lib\\site-packages\\tqdm', 'Lib\\site-packages\\tqdm'), ('C:\\PycharmProjects\\Chia_Log_Monitor\\.venv\\Lib\\site-packages\\matplotlib', 'Lib\\site-packages\\matplotlib'), ('C:\\PycharmProjects\\Chia_Log_Monitor\\.venv\\Lib\\site-packages\\mplcursors', 'Lib\\site-packages\\mplcursors')],
    datas=[('C:\\PycharmProjects\\Chia_Log_Monitor\\images', 'images'), ('C:\\PycharmProjects\\Chia_Log_Monitor\\images\\icon.ico', 'images')],
    hiddenimports=['matplotlib', 'mplcursors', 'platform', 'threading', 'tkinter', 'collections', 'datetime', 'tkinter.messagebox', 'tkinter.ttk', 'tkinter.filedialog', 'matplotlib.dates', 'matplotlib.pyplot', 'matplotlib.ticker', 'matplotlib.backends.backend_tkagg'],
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
    name='chia_log_monitor',
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
    icon=['C:\\PycharmProjects\\Chia_Log_Monitor\\images\\icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='chia_log_monitor',
)
