# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# OzonFbsLabelPrinter.spec — PyInstaller spec-файл
#
# Сборка:
#   pyinstaller --clean OzonFbsLabelPrinter.spec
#
# Результат:
#   dist\OzonFbsLabelPrinter\OzonFbsLabelPrinter.exe
# =============================================================================

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

# ---------------------------------------------------------------------------
# Данные, которые нужно включить в сборку
# ---------------------------------------------------------------------------
datas = [
    # Шаблоны этикеток
    (str(ROOT / "templates"), "templates"),
]

# Проверяем наличие папки assets (если добавят в будущем)
if (ROOT / "assets").exists():
    datas.append((str(ROOT / "assets"), "assets"))

# ---------------------------------------------------------------------------
# Скрытые импорты
# ---------------------------------------------------------------------------
hiddenimports = [
    # PySide6 — модули, которые PyInstaller не всегда находит автоматически
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtXml",
    "PySide6.QtPrintSupport",
    "PySide6.QtNetwork",
    "PySide6.QtSvg",
    "PySide6.QtOpenGL",

    # reportlab
    "reportlab",
    "reportlab.pdfgen",
    "reportlab.pdfgen.canvas",
    "reportlab.lib",
    "reportlab.lib.units",
    "reportlab.lib.pagesizes",
    "reportlab.lib.colors",
    "reportlab.lib.utils",
    "reportlab.lib.enums",
    "reportlab.lib.styles",
    "reportlab.platypus",
    "reportlab.platypus.paragraph",
    "reportlab.graphics",
    "reportlab.graphics.barcode",
    "reportlab.graphics.barcode.code128",
    "reportlab.graphics.barcode.code93",
    "reportlab.graphics.barcode.eanbc",

    # python-barcode
    "barcode",
    "barcode.writer",
    "barcode.base",
    "barcode.codex",
    "barcode.ean",
    "barcode.isxn",
    "barcode.itf",
    "barcode.upc",

    # Pillow
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    "PIL.BmpImagePlugin",
    "PIL.PngImagePlugin",
    "PIL.JpegImagePlugin",
    "PIL.GifImagePlugin",
    "PIL.TiffImagePlugin",

    # Windows-печать (опционально, не падать если нет)
    "win32api",
    "win32print",
    "win32con",
    "pywintypes",

    # Стандартные модули, иногда пропускаемые
    "json",
    "uuid",
    "dataclasses",
    "typing",
    "pathlib",
    "logging",
    "io",
    "tempfile",
    "subprocess",
    "platform",
    "enum",
    "datetime",
    "requests",
    "urllib3",
    "charset_normalizer",
    "certifi",
    "idna",
]

# ---------------------------------------------------------------------------
# Исключения — уменьшаем размер сборки
# ---------------------------------------------------------------------------
excludes = [
    "tkinter",
    "matplotlib",
    "scipy",
    "numpy",
    "pandas",
    "IPython",
    "jupyter",
    "notebook",
    "pytest",
    "pytest_qt",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# ---------------------------------------------------------------------------
# EXE (onedir — папка dist\OzonFbsLabelPrinter\ с exe внутри)
#
# Почему onedir, а не onefile:
#   - Быстрее запускается (нет распаковки во временную папку)
#   - Антивирус реже блокирует (нет самораспаковки)
#   - Проще отлаживать — все файлы видны рядом с exe
# ---------------------------------------------------------------------------
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="OzonFbsLabelPrinter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # GUI-приложение, без консольного окна
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon="assets/icon.ico",  # Раскомментировать когда добавите иконку
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="OzonFbsLabelPrinter",
)
