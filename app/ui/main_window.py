"""
Главное окно приложения Ozon FBS Label.

Функционал:
  - Ввод Client-Id / API-Key, переключатель Mock-режима
  - Кнопка «Обновить список» — загрузить отправления
  - Таблица отправлений с чекбоксами
  - Выбор режима печати: маршрутные / внутренние / всё
  - Выбор шаблона
  - Кнопки «Печать всех» / «Печать выбранных» / «Повторная печать»
  - Лог операций
  - Открытие редактора шаблонов
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
    from PySide6.QtGui import QFont, QColor, QIcon
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QLabel, QLineEdit, QCheckBox, QComboBox, QTableWidget,
        QTableWidgetItem, QTextEdit, QGroupBox, QSplitter,
        QHeaderView, QMessageBox, QFileDialog, QAbstractItemView,
        QStatusBar, QProgressBar, QFrame, QSizePolicy,
    )
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False

from app.api.ozon_client import OzonClient
from app.models.label_context import LabelContext
from app.models.template import Template, load_templates, save_templates, default_template
from app.services.label_generator import LabelGenerator
from app.services.print_service import PrintService, PrintMode, PrintResult
from app.services.settings_manager import SettingsManager

TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "templates" / "templates.json"
OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output" / "print_jobs"

COL_CHECK   = 0
COL_POSTING = 1
COL_ORDER   = 2
COL_PRODUCT = 3
COL_ARTICLE = 4
COL_SKU     = 5
COL_BARCODE = 6
COL_QTY     = 7
COL_STATUS  = 8


# ---------------------------------------------------------------------------
# Worker thread для загрузки отправлений
# ---------------------------------------------------------------------------
if PYSIDE6_AVAILABLE:
    class FetchWorker(QObject):
        finished = Signal(list, str)   # contexts_list, error_msg

        def __init__(self, client: OzonClient):
            super().__init__()
            self._client = client

        def run(self):
            try:
                raw_list = self._client.list_unfulfilled_postings()
                contexts = []
                for raw in raw_list:
                    normalized = self._client.normalize_posting(raw)
                    for d in normalized:
                        contexts.append(LabelContext.from_dict(d))
                self.finished.emit(contexts, "")
            except Exception as e:
                self.finished.emit([], str(e))

    class PrintWorker(QObject):
        log_signal = Signal(str)
        finished = Signal()

        def __init__(self, jobs, gen: LabelGenerator, svc: PrintService,
                     mode: str, client: OzonClient):
            super().__init__()
            self._jobs: List[LabelContext] = jobs
            self._gen = gen
            self._svc = svc
            self._mode = mode
            self._client = client

        def run(self):
            for ctx in self._jobs:
                try:
                    if self._mode in (PrintMode.INNER, PrintMode.ALL):
                        self._print_inner(ctx)
                    if self._mode in (PrintMode.ROUTE, PrintMode.ALL):
                        self._print_route(ctx)
                except Exception as e:
                    self.log_signal.emit(f"[ERR] {ctx.posting_number}: {e}")
            self.finished.emit()

        def _print_inner(self, ctx: LabelContext):
            from app.models.template import load_templates, default_template
            tpls = load_templates(str(TEMPLATES_PATH))
            tpl = next((t for t in tpls if t.default), tpls[0] if tpls else default_template())
            pdf = self._gen.generate(tpl, ctx)
            job_name = f"inner_{ctx.posting_number}"
            result = self._svc.print_pdf(pdf, job_name)
            self._svc.log_job(ctx.posting_number, "inner", result)
            status = "OK" if result.success else "ERR"
            self.log_signal.emit(f"[{status}] Внутренняя этикетка {ctx.posting_number}: {result.message}")

        def _print_route(self, ctx: LabelContext):
            pdf_bytes = self._client.get_package_label([ctx.posting_number])
            if not pdf_bytes:
                self.log_signal.emit(f"[ERR] Маршрутная этикетка не получена: {ctx.posting_number}")
                return
            job_name = f"route_{ctx.posting_number}"
            result = self._svc.print_pdf(pdf_bytes, job_name)
            self._svc.log_job(ctx.posting_number, "route", result)
            status = "OK" if result.success else "ERR"
            self.log_signal.emit(f"[{status}] Маршрутная этикетка {ctx.posting_number}: {result.message}")


# ---------------------------------------------------------------------------
# Главное окно
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ozon FBS Label — Печать этикеток")
        self.resize(1200, 700)

        self._settings = SettingsManager()
        self._contexts: List[LabelContext] = []
        self._fetch_thread: Optional[QThread] = None
        self._print_thread: Optional[QThread] = None
        self._gen: Optional[LabelGenerator] = None
        self._svc = PrintService(
            printer_name=self._settings.printer_inner,
            output_dir=OUTPUT_DIR,
        )

        self._build_ui()
        self._load_settings_to_ui()
        self._try_init_generator()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(6)

        # ---- Верхняя панель: API настройки ----
        top_grp = QGroupBox("Подключение к Ozon Seller API")
        top_layout = QHBoxLayout(top_grp)

        top_layout.addWidget(QLabel("Client-Id:"))
        self.client_id_edit = QLineEdit()
        self.client_id_edit.setPlaceholderText("Ваш Client-Id")
        self.client_id_edit.setMaximumWidth(180)
        top_layout.addWidget(self.client_id_edit)

        top_layout.addWidget(QLabel("API-Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("Ваш API-Key")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setMaximumWidth(280)
        top_layout.addWidget(self.api_key_edit)

        self.mock_check = QCheckBox("Mock-режим (без Ozon)")
        self.mock_check.setChecked(True)
        self.mock_check.setToolTip(
            "В mock-режиме используются тестовые данные.\n"
            "Для работы с реальными заказами снимите галочку и введите ключи."
        )
        top_layout.addWidget(self.mock_check)

        self.btn_refresh = QPushButton("⟳ Обновить список")
        self.btn_refresh.setMinimumWidth(140)
        self.btn_refresh.clicked.connect(self._on_refresh)
        top_layout.addWidget(self.btn_refresh)

        top_layout.addStretch()

        self.btn_settings_save = QPushButton("Сохранить настройки")
        self.btn_settings_save.clicked.connect(self._on_save_settings)
        top_layout.addWidget(self.btn_settings_save)

        main_layout.addWidget(top_grp)

        # ---- Основное содержимое: таблица + лог ----
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)

        # Таблица отправлений
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        hdr_row = QHBoxLayout()
        hdr_row.addWidget(QLabel("<b>Отправления FBS</b>"))
        hdr_row.addStretch()

        hdr_row.addWidget(QLabel("Шаблон:"))
        self.template_combo = QComboBox()
        self.template_combo.setMinimumWidth(200)
        self.template_combo.currentIndexChanged.connect(self._on_template_changed)
        hdr_row.addWidget(self.template_combo)

        hdr_row.addWidget(QLabel("Режим:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Внутренние", "Маршрутные (Ozon)", "Всё"])
        self.mode_combo.setToolTip(
            "Внутренние — ваши этикетки по шаблону 58×40 мм\n"
            "Маршрутные — этикетки от Ozon (не редактируются)\n"
            "Всё — оба типа"
        )
        hdr_row.addWidget(self.mode_combo)

        hdr_row.addWidget(QLabel("Принтер:"))
        self.printer_combo = QComboBox()
        self.printer_combo.setMinimumWidth(180)
        self.printer_combo.addItem("(сохранить в файл)")
        self._populate_printers()
        hdr_row.addWidget(self.printer_combo)

        table_layout.addLayout(hdr_row)

        self.table = QTableWidget(0, 9)
        self.table.setHorizontalHeaderLabels([
            "", "Отправление", "Заказ", "Наименование", "Артикул", "SKU", "Штрихкод", "Кол-во", "Статус"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(COL_PRODUCT, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)

        # Кнопки действий
        act_row = QHBoxLayout()
        self.btn_check_all = QPushButton("Выбрать все")
        self.btn_check_all.clicked.connect(self._on_check_all)
        self.btn_uncheck_all = QPushButton("Снять все")
        self.btn_uncheck_all.clicked.connect(self._on_uncheck_all)
        self.btn_print_selected = QPushButton("Печать выбранных")
        self.btn_print_selected.setStyleSheet("QPushButton { font-weight: bold; color: #005a00; }")
        self.btn_print_selected.clicked.connect(self._on_print_selected)
        self.btn_print_all = QPushButton("Печать всех")
        self.btn_print_all.setStyleSheet("QPushButton { font-weight: bold; }")
        self.btn_print_all.clicked.connect(self._on_print_all)
        self.btn_reprint = QPushButton("Повторная печать")
        self.btn_reprint.setToolTip("Открыть папку output/print_jobs для повторной печати")
        self.btn_reprint.clicked.connect(self._on_reprint)
        self.btn_editor = QPushButton("Редактор шаблонов")
        self.btn_editor.clicked.connect(self._on_open_editor)

        for b in [self.btn_check_all, self.btn_uncheck_all,
                  self.btn_print_selected, self.btn_print_all,
                  self.btn_reprint, self.btn_editor]:
            act_row.addWidget(b)
        act_row.addStretch()

        table_layout.addLayout(act_row)
        splitter.addWidget(table_widget)

        # Лог
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.addWidget(QLabel("<b>Лог операций</b>"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        self.log_text.setFont(QFont("Courier New", 9))
        log_layout.addWidget(self.log_text)
        btn_clear_log = QPushButton("Очистить лог")
        btn_clear_log.setMaximumWidth(120)
        btn_clear_log.clicked.connect(self.log_text.clear)
        log_layout.addWidget(btn_clear_log, 0, Qt.AlignRight)
        splitter.addWidget(log_widget)

        splitter.setSizes([480, 180])

        # Статусбар + прогресс
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(200)
        self.progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress)
        self.status_bar.showMessage("Готов. Нажмите «Обновить список».")

        self._refresh_templates()

    def _populate_printers(self):
        printers = self._svc.get_printers()
        for p in printers:
            self.printer_combo.addItem(p)

    # ------------------------------------------------------------------
    # Настройки
    # ------------------------------------------------------------------

    def _load_settings_to_ui(self):
        self.client_id_edit.setText(self._settings.client_id)
        self.api_key_edit.setText(self._settings.api_key)
        self.mock_check.setChecked(self._settings.mock_mode)
        # printer
        idx = self.printer_combo.findText(self._settings.printer_inner)
        if idx >= 0:
            self.printer_combo.setCurrentIndex(idx)
        # mode
        mode_map = {"inner": 0, "route": 1, "all": 2}
        self.mode_combo.setCurrentIndex(mode_map.get(self._settings.print_mode, 0))

    def _on_save_settings(self):
        self._settings.update_and_save({
            "client_id": self.client_id_edit.text().strip(),
            "api_key": self.api_key_edit.text().strip(),
            "mock_mode": self.mock_check.isChecked(),
            "printer_inner": self.printer_combo.currentText(),
            "print_mode": ["inner", "route", "all"][self.mode_combo.currentIndex()],
        })
        self._log("Настройки сохранены в settings.json")
        self.status_bar.showMessage("Настройки сохранены.", 3000)

    # ------------------------------------------------------------------
    # Шаблоны
    # ------------------------------------------------------------------

    def _refresh_templates(self):
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        tpls = load_templates(str(TEMPLATES_PATH))
        for t in tpls:
            label = f"{'★ ' if t.default else ''}{t.name}"
            self.template_combo.addItem(label, t.id)
        # Выбрать default или первый
        default_id = self._settings.default_template_id
        if default_id:
            for i in range(self.template_combo.count()):
                if self.template_combo.itemData(i) == default_id:
                    self.template_combo.setCurrentIndex(i)
                    break
        self.template_combo.blockSignals(False)

    def _on_template_changed(self, idx: int):
        tid = self.template_combo.itemData(idx)
        if tid:
            self._settings.set_and_save("default_template_id", tid)

    # ------------------------------------------------------------------
    # Загрузка отправлений
    # ------------------------------------------------------------------

    def _on_refresh(self):
        self._on_save_settings()
        self._try_init_generator()
        client = OzonClient(
            client_id=self.client_id_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            mock_mode=self.mock_check.isChecked(),
        )
        self._log("Загрузка отправлений...")
        self.btn_refresh.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        self._fetch_thread = QThread()
        self._fetch_worker = FetchWorker(client)
        self._fetch_worker.moveToThread(self._fetch_thread)
        self._fetch_thread.started.connect(self._fetch_worker.run)
        self._fetch_worker.finished.connect(self._on_fetch_done)
        self._fetch_worker.finished.connect(self._fetch_thread.quit)
        self._fetch_thread.start()

    def _on_fetch_done(self, contexts: List[LabelContext], error: str):
        self.btn_refresh.setEnabled(True)
        self.progress.setVisible(False)
        if error:
            self._log(f"[ERR] Ошибка загрузки: {error}")
            self.status_bar.showMessage(f"Ошибка: {error}", 5000)
            return
        self._contexts = contexts
        self._fill_table(contexts)
        self._log(f"Загружено {len(contexts)} отправлений/позиций")
        self.status_bar.showMessage(f"Загружено: {len(contexts)} позиций", 5000)

    def _fill_table(self, contexts: List[LabelContext]):
        self.table.setRowCount(0)
        for ctx in contexts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            chk = QTableWidgetItem()
            chk.setCheckState(Qt.Checked)
            chk.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            self.table.setItem(row, COL_CHECK, chk)

            for col, val in [
                (COL_POSTING, ctx.posting_number),
                (COL_ORDER, ctx.order_number),
                (COL_PRODUCT, ctx.product_name),
                (COL_ARTICLE, ctx.article),
                (COL_SKU, ctx.sku),
                (COL_BARCODE, ctx.barcode),
                (COL_QTY, str(ctx.quantity)),
                (COL_STATUS, "ожидает упаковки"),
            ]:
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, col, item)

    # ------------------------------------------------------------------
    # Чекбоксы
    # ------------------------------------------------------------------

    def _on_check_all(self):
        for row in range(self.table.rowCount()):
            self.table.item(row, COL_CHECK).setCheckState(Qt.Checked)

    def _on_uncheck_all(self):
        for row in range(self.table.rowCount()):
            self.table.item(row, COL_CHECK).setCheckState(Qt.Unchecked)

    def _get_checked_contexts(self) -> List[LabelContext]:
        result = []
        for row in range(self.table.rowCount()):
            chk = self.table.item(row, COL_CHECK)
            if chk and chk.checkState() == Qt.Checked:
                if row < len(self._contexts):
                    result.append(self._contexts[row])
        return result

    # ------------------------------------------------------------------
    # Печать
    # ------------------------------------------------------------------

    def _try_init_generator(self):
        try:
            self._gen = LabelGenerator()
        except ImportError as e:
            self._log(f"[WARN] LabelGenerator недоступен: {e}")
            self._gen = None

    def _on_print_selected(self):
        jobs = self._get_checked_contexts()
        if not jobs:
            QMessageBox.information(self, "Нет выбранных", "Выберите отправления для печати.")
            return
        self._start_print(jobs)

    def _on_print_all(self):
        if not self._contexts:
            QMessageBox.information(self, "Нет данных", "Сначала загрузите список отправлений.")
            return
        self._start_print(self._contexts)

    def _start_print(self, jobs: List[LabelContext]):
        if not self._gen:
            QMessageBox.warning(
                self, "Ошибка",
                "Генератор этикеток недоступен. Установите: pip install reportlab"
            )
            return

        mode_map = {0: PrintMode.INNER, 1: PrintMode.ROUTE, 2: PrintMode.ALL}
        mode = mode_map.get(self.mode_combo.currentIndex(), PrintMode.INNER)

        printer = self.printer_combo.currentText()
        if printer == "(сохранить в файл)":
            printer = ""
        self._svc.printer_name = printer

        client = OzonClient(
            client_id=self.client_id_edit.text().strip(),
            api_key=self.api_key_edit.text().strip(),
            mock_mode=self.mock_check.isChecked(),
        )

        self._log(f"Запуск печати {len(jobs)} позиций, режим: {mode.value}, принтер: {printer or 'файл'}")
        self.btn_print_all.setEnabled(False)
        self.btn_print_selected.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)

        self._print_thread = QThread()
        self._print_worker = PrintWorker(jobs, self._gen, self._svc, mode, client)
        self._print_worker.moveToThread(self._print_thread)
        self._print_thread.started.connect(self._print_worker.run)
        self._print_worker.log_signal.connect(self._log)
        self._print_worker.finished.connect(self._on_print_done)
        self._print_worker.finished.connect(self._print_thread.quit)
        self._print_thread.start()

    def _on_print_done(self):
        self.btn_print_all.setEnabled(True)
        self.btn_print_selected.setEnabled(True)
        self.progress.setVisible(False)
        self.status_bar.showMessage("Печать завершена.", 5000)
        self._log("Печать завершена.")

    def _on_reprint(self):
        output_dir = str(OUTPUT_DIR)
        if os.path.isdir(output_dir):
            try:
                import subprocess, platform
                if platform.system() == "Windows":
                    os.startfile(output_dir)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", output_dir])
                else:
                    subprocess.Popen(["xdg-open", output_dir])
            except Exception as e:
                self._log(f"Не удалось открыть папку: {e}")
        else:
            QMessageBox.information(self, "Папка пуста", f"Нет сохранённых файлов: {output_dir}")

    # ------------------------------------------------------------------
    # Редактор шаблонов
    # ------------------------------------------------------------------

    def _on_open_editor(self):
        try:
            from app.ui.template_editor import TemplateEditorDialog
            dlg = TemplateEditorDialog(self)
            dlg.template_saved.connect(self._refresh_templates)
            dlg.exec()
            self._refresh_templates()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть редактор: {e}")
            logger.exception("open editor error")

    # ------------------------------------------------------------------
    # Лог
    # ------------------------------------------------------------------

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")
        logger.info(msg)

    # ------------------------------------------------------------------
    # Закрытие
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        self._on_save_settings()
        event.accept()
