#!/usr/bin/env python3
"""
Точка входа — запуск Ozon FBS Label App.

Использование:
    python run.py              # Запустить GUI
    python run.py --mock       # Запустить в mock-режиме (явно)
    python run.py --no-gui     # Headless-проверка (для тестов/CI)
    python run.py --help       # Справка
"""
import argparse
import logging
import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_gui(mock_mode: bool = None):
    """Запустить GUI-приложение."""
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
    except ImportError:
        print(
            "PySide6 не установлен. Установите: pip install PySide6\n"
            "Или запустите в headless-режиме: python run.py --no-gui",
            file=sys.stderr,
        )
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("Ozon FBS Label")
    app.setOrganizationName("OzonFBSLabel")
    app.setApplicationVersion("1.0.0")

    # Тема
    app.setStyle("Fusion")

    from app.ui.main_window import MainWindow
    from app.services.settings_manager import SettingsManager

    window = MainWindow()

    # Перезаписать mock_mode из аргументов командной строки если задан
    if mock_mode is not None:
        window.mock_check.setChecked(mock_mode)
        window._settings.mock_mode = mock_mode

    window.show()

    # Автозагрузка отправлений
    from PySide6.QtCore import QTimer
    QTimer.singleShot(500, window._on_refresh)

    sys.exit(app.exec())


def run_headless():
    """Headless-проверка без GUI (для CI/тестов)."""
    print("=== Ozon FBS Label — Headless Check ===")

    # 1. Проверка зависимостей
    missing = []
    for pkg in ["requests", "reportlab"]:
        try:
            __import__(pkg)
            print(f"  [OK] {pkg}")
        except ImportError:
            print(f"  [MISS] {pkg}")
            missing.append(pkg)

    # 2. Mock-режим: загрузить данные
    from app.api.ozon_client import OzonClient
    from app.models.label_context import LabelContext
    from app.models.template import default_template

    client = OzonClient(mock_mode=True)
    postings = client.list_unfulfilled_postings()
    print(f"  [OK] Mock postings: {len(postings)}")

    contexts = []
    for raw in postings:
        for d in client.normalize_posting(raw):
            contexts.append(LabelContext.from_dict(d))
    print(f"  [OK] Contexts: {len(contexts)}")

    # 3. Генерация этикеток
    if "reportlab" not in missing:
        from app.services.label_generator import LabelGenerator
        gen = LabelGenerator()
        tpl = default_template()
        for ctx in contexts:
            pdf = gen.generate(tpl, ctx)
            assert pdf[:4] == b"%PDF", "Невалидный PDF!"
        print(f"  [OK] PDF labels generated: {len(contexts)}")

        # Сохранить в output
        output_dir = PROJECT_ROOT / "output" / "print_jobs"
        output_dir.mkdir(parents=True, exist_ok=True)
        sample_ctx = contexts[0] if contexts else LabelContext(posting_number="SAMPLE")
        sample_pdf = gen.generate(tpl, sample_ctx)
        out_path = output_dir / "sample_label.pdf"
        gen.save(sample_pdf, str(out_path))
        print(f"  [OK] Sample saved: {out_path}")

    print("\n=== Готово ===")


def main():
    parser = argparse.ArgumentParser(
        description="Ozon FBS Label App — печать этикеток для FBS-отправлений"
    )
    parser.add_argument("--mock", action="store_true", help="Запустить в mock-режиме")
    parser.add_argument("--no-gui", action="store_true", help="Headless-режим (без GUI)")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Уровень логирования",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    # Убедиться что нужные директории существуют
    for d in ["output/print_jobs", "templates"]:
        (PROJECT_ROOT / d).mkdir(parents=True, exist_ok=True)

    if args.no_gui:
        run_headless()
    else:
        run_gui(mock_mode=True if args.mock else None)


if __name__ == "__main__":
    main()
