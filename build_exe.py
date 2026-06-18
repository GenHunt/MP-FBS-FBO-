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
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=Ozon-FBS-Label-Printer',
        '--windowed',
        '--icon=icon.ico',
        '--onefile',
        '--add-data=data:data',
        '--add-data=logs:logs',
        '--hidden-import=PyQt6',
        '--hidden-import=PyQt6.QtCore',
        '--hidden-import=PyQt6.QtGui',
        '--hidden-import=PyQt6.QtWidgets',
        '--hidden-import=PyQt6.QtChart',
        '--hidden-import=requests',
        '--hidden-import=PIL',
        '--hidden-import=barcode',
        '--hidden-import=sqlite3',
        '--collect-all=PyQt6',
        '--distpath=dist',
        '--buildpath=build',
        '--specpath=build',
        '--noconfirm',
    ]
    
    print("🔨 Building executable...")
    print("This may take a few minutes...")
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build successful!")
        print(f"📦 Executable created: dist/Ozon-FBS-Label-Printer.exe")
        print("\n📋 You can now distribute this .exe file!")
        print("   No Python installation needed on target machines!")
        return True
    
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        return False

if __name__ == '__main__':
    success = build_exe()
    sys.exit(0 if success else 1)
