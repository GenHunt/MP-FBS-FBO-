"""
Logs tab - live view of application log file
"""
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QCheckBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QTextCursor

logger = logging.getLogger(__name__)

_MAX_LINES = 2000  # Maximum lines to keep in the text area


class LogsTab(QWidget):
    """Tab that displays the application log file with auto-refresh."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._last_pos = 0

        self._create_ui()
        self._setup_timer()
        self._load_log()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _create_ui(self) -> None:
        layout = QVBoxLayout()

        # Toolbar
        toolbar = QHBoxLayout()

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(self._load_log)
        toolbar.addWidget(self.refresh_btn)

        self.clear_btn = QPushButton("Очистить отображение")
        self.clear_btn.clicked.connect(self._clear_display)
        toolbar.addWidget(self.clear_btn)

        self.export_btn = QPushButton("Экспортировать лог")
        self.export_btn.clicked.connect(self._export_log)
        toolbar.addWidget(self.export_btn)

        toolbar.addStretch()

        self.auto_refresh_cb = QCheckBox("Автообновление (5 сек)")
        self.auto_refresh_cb.setChecked(True)
        toolbar.addWidget(self.auto_refresh_cb)

        layout.addLayout(toolbar)

        # Status label
        self.status_label = QLabel("Загрузка логов...")
        layout.addWidget(self.status_label)

        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier New", 9))
        self.log_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.log_text)

        self.setLayout(layout)

    # ------------------------------------------------------------------
    # Timer
    # ------------------------------------------------------------------

    def _setup_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(5000)
        self._timer.timeout.connect(self._auto_refresh)
        self._timer.start()

    def _auto_refresh(self) -> None:
        if self.auto_refresh_cb.isChecked():
            self._append_new_lines()

    # ------------------------------------------------------------------
    # Log loading
    # ------------------------------------------------------------------

    def _get_log_path(self) -> Path:
        try:
            import config
            return config.LOG_FILE
        except Exception:
            return Path('logs') / 'ozon_label_printer.log'

    def _load_log(self) -> None:
        """Load the full log file content."""
        log_path = self._get_log_path()
        self.log_text.clear()
        self._last_pos = 0

        if not log_path.exists():
            self.log_text.setPlainText("Лог-файл не найден.")
            self.status_label.setText(f"Файл: {log_path} (не найден)")
            return

        try:
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                self._last_pos = f.tell()

            lines = content.splitlines()
            if len(lines) > _MAX_LINES:
                lines = lines[-_MAX_LINES:]
            self.log_text.setPlainText('\n'.join(lines))
            self._scroll_to_bottom()
            self.status_label.setText(f"Файл: {log_path} | Строк: {len(lines)}")
        except Exception as e:
            self.log_text.setPlainText(f"Ошибка чтения лога: {e}")
            logger.error(f"Failed to read log file: {e}")

    def _append_new_lines(self) -> None:
        """Append only new lines written since the last read."""
        log_path = self._get_log_path()
        if not log_path.exists():
            return
        try:
            size = log_path.stat().st_size
            if size <= self._last_pos:
                return
            with open(log_path, 'r', encoding='utf-8', errors='replace') as f:
                f.seek(self._last_pos)
                new_content = f.read()
                self._last_pos = f.tell()

            if new_content.strip():
                self.log_text.moveCursor(QTextCursor.MoveOperation.End)
                self.log_text.insertPlainText(new_content)
                self._scroll_to_bottom()
        except Exception as e:
            logger.warning(f"Failed to append new log lines: {e}")

    def _scroll_to_bottom(self) -> None:
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _clear_display(self) -> None:
        self.log_text.clear()
        self._last_pos = 0
        self.status_label.setText("Отображение очищено")

    def _export_log(self) -> None:
        """Save a copy of the log file to a user-chosen location."""
        log_path = self._get_log_path()
        if not log_path.exists():
            QMessageBox.warning(self, "Ошибка", "Лог-файл не найден")
            return

        dest, _ = QFileDialog.getSaveFileName(
            self, "Сохранить лог", "ozon_log.txt", "Text files (*.txt);;All files (*)"
        )
        if not dest:
            return
        try:
            import shutil
            shutil.copy2(str(log_path), dest)
            QMessageBox.information(self, "Успех", f"Лог сохранён: {dest}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить лог: {e}")
