"""
Менеджер настроек приложения.

Хранит настройки в settings.json (рядом с исполняемым файлом или в папке проекта).
Реальные ключи API НЕ должны коммититься в репозиторий.
settings.json добавлен в .gitignore.

Структура settings.json:
{
  "client_id": "",
  "api_key": "",
  "mock_mode": true,
  "default_template_id": null,
  "printer_inner": "",
  "printer_route": "",
  "print_mode": "inner",
  "output_dir": "output/print_jobs",
  "log_level": "INFO"
}
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Определяем путь к settings.json: рядом с run.py (корень проекта)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SETTINGS_PATH = _PROJECT_ROOT / "settings.json"

DEFAULTS = {
    "client_id": "",
    "api_key": "",
    "mock_mode": True,
    "default_template_id": None,
    "printer_inner": "",
    "printer_route": "",
    "print_mode": "inner",
    "output_dir": str(_PROJECT_ROOT / "output" / "print_jobs"),
    "log_level": "INFO",
}


class SettingsManager:
    """CRUD для settings.json."""

    def __init__(self, path: Optional[Path] = None):
        self._path = path or SETTINGS_PATH
        self._data: dict = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        """Загрузить настройки из файла."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    stored = json.load(f)
                # Merge: дефолты + сохранённые (новые ключи не пропадут)
                for k, v in stored.items():
                    self._data[k] = v
                logger.debug("Настройки загружены из %s", self._path)
            except Exception as e:
                logger.warning("Ошибка загрузки настроек: %s (используются дефолты)", e)
        else:
            self.save()  # создать файл с дефолтами

    def save(self) -> None:
        """Сохранить настройки в файл."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.debug("Настройки сохранены в %s", self._path)
        except Exception as e:
            logger.error("Ошибка сохранения настроек: %s", e)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def set_and_save(self, key: str, value: Any) -> None:
        self.set(key, value)
        self.save()

    def update(self, data: dict) -> None:
        self._data.update(data)

    def update_and_save(self, data: dict) -> None:
        self.update(data)
        self.save()

    # Shortcuts
    @property
    def client_id(self) -> str:
        return self.get("client_id", "")

    @client_id.setter
    def client_id(self, v: str):
        self.set("client_id", v)

    @property
    def api_key(self) -> str:
        return self.get("api_key", "")

    @api_key.setter
    def api_key(self, v: str):
        self.set("api_key", v)

    @property
    def mock_mode(self) -> bool:
        return bool(self.get("mock_mode", True))

    @mock_mode.setter
    def mock_mode(self, v: bool):
        self.set("mock_mode", v)

    @property
    def printer_inner(self) -> str:
        return self.get("printer_inner", "")

    @printer_inner.setter
    def printer_inner(self, v: str):
        self.set("printer_inner", v)

    @property
    def printer_route(self) -> str:
        return self.get("printer_route", "")

    @printer_route.setter
    def printer_route(self, v: str):
        self.set("printer_route", v)

    @property
    def print_mode(self) -> str:
        return self.get("print_mode", "inner")

    @print_mode.setter
    def print_mode(self, v: str):
        self.set("print_mode", v)

    @property
    def default_template_id(self) -> Optional[str]:
        return self.get("default_template_id")

    @default_template_id.setter
    def default_template_id(self, v: Optional[str]):
        self.set("default_template_id", v)
