"""
Сервис печати этикеток.

Режимы работы:
  ROUTE   — маршрутная этикетка Ozon (готовый PDF, не редактировать)
  INNER   — внутренняя этикетка (генерируем PDF по шаблону)
  ALL     — оба

Печать:
  Windows + pywin32 → ShellExecute "printto" / win32api
  Windows без pywin32 → os.startfile("print")
  Linux/macOS / нет принтера → сохранить в output/print_jobs + лог
"""
from __future__ import annotations

import logging
import os
import platform
import subprocess
import tempfile
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "print_jobs"


class PrintMode(str, Enum):
    ROUTE = "route"      # только маршрутные
    INNER = "inner"      # только внутренние
    ALL   = "all"        # всё


class PrintResult:
    def __init__(self, success: bool, message: str, saved_path: Optional[str] = None):
        self.success = success
        self.message = message
        self.saved_path = saved_path

    def __repr__(self):
        return f"PrintResult(success={self.success}, message={self.message!r})"


class PrintService:
    """
    Сервис печати. Определяет среду (Windows/Linux) и выбирает метод.
    """

    def __init__(self, printer_name: str = "", output_dir: Optional[Path] = None):
        self.printer_name = printer_name
        self.output_dir = output_dir or OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._is_windows = platform.system() == "Windows"
        self._pywin32_available = self._check_pywin32()

    @staticmethod
    def _check_pywin32() -> bool:
        try:
            import win32print  # noqa: F401
            import win32api   # noqa: F401
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Публичное API
    # ------------------------------------------------------------------

    def print_pdf(self, pdf_bytes: bytes, job_name: str = "label") -> PrintResult:
        """Распечатать PDF (байты). Fallback — сохранить файл."""
        path = self._save_temp_pdf(pdf_bytes, job_name)

        if self._is_windows:
            if self._pywin32_available and self.printer_name:
                return self._win32_print(path, job_name)
            else:
                return self._shell_print(path)
        else:
            # Linux/macOS sandbox: сохраняем в output/print_jobs
            return self._save_to_output(pdf_bytes, job_name)

    def save_pdf(self, pdf_bytes: bytes, job_name: str = "label") -> PrintResult:
        """Сохранить PDF в output/print_jobs без печати."""
        return self._save_to_output(pdf_bytes, job_name)

    def get_printers(self) -> List[str]:
        """Получить список доступных принтеров."""
        if self._is_windows and self._pywin32_available:
            try:
                import win32print
                printers = win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                )
                return [p[2] for p in printers]
            except Exception as e:
                logger.warning("Ошибка получения принтеров: %s", e)
        # Linux: lpstat
        try:
            result = subprocess.run(
                ["lpstat", "-p"], capture_output=True, text=True, timeout=5
            )
            printers = []
            for line in result.stdout.splitlines():
                if line.startswith("printer "):
                    printers.append(line.split()[1])
            return printers
        except Exception:
            pass
        return []

    # ------------------------------------------------------------------
    # Методы печати
    # ------------------------------------------------------------------

    def _win32_print(self, pdf_path: str, job_name: str) -> PrintResult:
        """Печать через win32api (Windows + pywin32)."""
        try:
            import win32api
            win32api.ShellExecute(
                0,
                "printto",
                pdf_path,
                f'"{self.printer_name}"',
                ".",
                0,
            )
            logger.info("win32 печать отправлена: %s → %s", job_name, self.printer_name)
            return PrintResult(True, f"Задание отправлено на принтер: {self.printer_name}", pdf_path)
        except Exception as e:
            logger.error("win32_print error: %s", e)
            return PrintResult(False, f"Ошибка win32 печати: {e}", pdf_path)

    def _shell_print(self, pdf_path: str) -> PrintResult:
        """Печать через os.startfile (Windows без pywin32)."""
        try:
            os.startfile(pdf_path, "print")
            logger.info("Shell print: %s", pdf_path)
            return PrintResult(True, f"Файл отправлен на печать через Shell: {pdf_path}", pdf_path)
        except Exception as e:
            logger.error("shell_print error: %s", e)
            # Fallback: сохранить
            return PrintResult(False, f"Ошибка shell печати: {e}. Файл сохранён: {pdf_path}", pdf_path)

    def _save_to_output(self, pdf_bytes: bytes, job_name: str) -> PrintResult:
        """Сохранить PDF в output/print_jobs (Linux/sandbox/fallback)."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in job_name)
        filename = f"{ts}_{safe_name}.pdf"
        out_path = self.output_dir / filename
        try:
            with open(out_path, "wb") as f:
                f.write(pdf_bytes)
            logger.info("[SAVE] %s → %s", job_name, out_path)
            return PrintResult(True, f"Файл сохранён: {out_path}", str(out_path))
        except Exception as e:
            logger.error("save_to_output error: %s", e)
            return PrintResult(False, f"Ошибка сохранения: {e}")

    def _save_temp_pdf(self, pdf_bytes: bytes, job_name: str) -> str:
        """Сохранить PDF во временный файл для печати."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in job_name)
        tmp = tempfile.NamedTemporaryFile(
            suffix=".pdf",
            prefix=f"ozon_{safe}_{ts}_",
            delete=False,
        )
        tmp.write(pdf_bytes)
        tmp.close()
        return tmp.name

    # ------------------------------------------------------------------
    # Лог
    # ------------------------------------------------------------------

    def log_job(self, posting_number: str, mode: str, result: PrintResult):
        """Записать в лог-файл результат задания."""
        log_path = self.output_dir / "print_log.txt"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "OK" if result.success else "ERR"
        line = f"{ts} [{status}] {mode} | {posting_number} | {result.message}\n"
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass
