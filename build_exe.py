"""
build_exe.py - Script to build standalone .exe file using PyInstaller
"""

import os
import sys
from pathlib import Path
import PyInstaller.__main__


def build_exe():
    """Build executable with PyInstaller"""

    # Get project root
    root_dir = Path(__file__).parent

    # Ensure required directories exist
    (root_dir / 'data').mkdir(exist_ok=True)
    (root_dir / 'logs').mkdir(exist_ok=True)

    # Use ';' as separator on Windows, ':' on other platforms
    sep = ';' if sys.platform == 'win32' else ':'

    # PyInstaller arguments
    args = [
        'main.py',
        '--name=Ozon-FBS-Label-Printer',
        '--windowed',
        '--onefile',
        f'--add-data=data{sep}data',
        f'--add-data=logs{sep}logs',
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtCharts',
        '--hidden-import=requests',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=barcode',
        '--hidden-import=barcode.writer',
        '--hidden-import=sqlite3',
        '--hidden-import=win32print',
        '--hidden-import=win32api',
        '--hidden-import=pywintypes',
        '--collect-all=PyQt6',
        '--distpath=dist',
        '--workpath=build',
        '--specpath=build',
        '--noconfirm',
    ]

    print("[*] Building Ozon FBS Label Printer executable...")
    print("[*] This may take a few minutes...")

    try:
        PyInstaller.__main__.run(args)
        print("")
        print("[OK] Build successful!")
        print("[OK] Executable created: dist/Ozon-FBS-Label-Printer.exe")
        print("")
        print("[*] You can now distribute this .exe file!")
        print("[*] No Python installation needed on target machines!")
        return True

    except Exception as e:
        print(f"")
        print(f"[ERROR] Build failed: {e}")
        return False


if __name__ == '__main__':
    success = build_exe()
    sys.exit(0 if success else 1)
