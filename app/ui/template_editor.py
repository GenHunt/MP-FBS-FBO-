"""
Редактор шаблонов этикеток.

Позволяет:
  - Просматривать список шаблонов
  - Создавать / копировать / удалять шаблоны
  - Редактировать элементы шаблона в таблице (координаты, переменные, шрифты)
  - Предпросматривать результат (схематично или PDF→PNG)
  - Устанавливать шаблон по умолчанию
  - Сохранять в templates/templates.json

TODO (drag-and-drop): Поддержка перетаскивания элементов по предпросмотру будет добавлена
в следующей версии. Пока координаты вводятся вручную в таблице.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    from PySide6.QtCore import Qt, QSize, Signal, QThread
    from PySide6.QtGui import QPixmap, QImage, QColor, QFont
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
        QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
        QSplitter, QWidget, QLineEdit, QDoubleSpinBox, QSpinBox,
        QComboBox, QCheckBox, QMessageBox, QHeaderView, QGroupBox,
        QScrollArea, QSizePolicy, QToolBar, QAbstractItemView,
    )
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False
    logger.warning("PySide6 недоступен — редактор шаблонов работает только в mock/headless-режиме")

from app.models.template import (
    Template, TemplateElement, load_templates, save_templates, default_template
)
from app.models.label_context import LabelContext

TEMPLATES_PATH = Path(__file__).resolve().parent.parent.parent / "templates" / "templates.json"

# Тестовый контекст для предпросмотра
_PREVIEW_CTX = LabelContext(
    posting_number="89750178-0001-1",
    order_number="89750178-0001",
    product_name="Держатель для телефона автомобильный Premium",
    article="ART-001",
    offer_id="ART-001",
    sku="123456789",
    barcode="4607050394357",
    quantity=2,
)

ELEMENT_COLUMNS = [
    ("Тип", "type"),
    ("X мм", "x_mm"),
    ("Y мм", "y_mm"),
    ("Ш мм", "w_mm"),
    ("В мм", "h_mm"),
    ("Переменная", "variable"),
    ("Статический текст", "static_text"),
    ("Шрифт", "font_family"),
    ("Размер", "font_size"),
    ("Жирный", "bold"),
    ("Выравн.", "align"),
    ("Видимый", "visible"),
    ("Обязат.", "required"),
]

VARIABLES = [
    "", "article", "product_name", "barcode", "manufacturer_part_number",
    "offer_id", "sku", "posting_number", "order_number", "quantity", "date", "time",
]

TYPES = ["text", "barcode"]
ALIGNS = ["left", "center", "right"]


class TemplateEditorDialog(QDialog):
    """Главный диалог редактора шаблонов."""

    template_saved = Signal(str)   # id выбранного шаблона

    def __init__(self, parent=None, templates_path: Optional[Path] = None):
        super().__init__(parent)
        self.setWindowTitle("Редактор шаблонов этикеток")
        self.resize(1100, 700)
        self._path = templates_path or TEMPLATES_PATH
        self._templates: List[Template] = load_templates(str(self._path))
        self._current: Optional[Template] = None
        self._dirty = False
        self._build_ui()
        self._refresh_list()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # ---- Левая панель: список шаблонов ----
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)

        left_layout.addWidget(QLabel("<b>Шаблоны</b>"))
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.currentRowChanged.connect(self._on_template_selected)
        left_layout.addWidget(self.list_widget)

        btn_row = QHBoxLayout()
        self.btn_new = QPushButton("Создать")
        self.btn_copy = QPushButton("Копировать")
        self.btn_del = QPushButton("Удалить")
        for b in [self.btn_new, self.btn_copy, self.btn_del]:
            btn_row.addWidget(b)
        self.btn_new.clicked.connect(self._on_new)
        self.btn_copy.clicked.connect(self._on_copy)
        self.btn_del.clicked.connect(self._on_delete)
        left_layout.addLayout(btn_row)

        self.btn_set_default = QPushButton("Сделать по умолчанию")
        self.btn_set_default.clicked.connect(self._on_set_default)
        left_layout.addWidget(self.btn_set_default)

        splitter.addWidget(left)

        # ---- Центральная панель: редактор элементов ----
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(4, 4, 4, 4)

        # Заголовок шаблона
        meta_grp = QGroupBox("Параметры шаблона")
        meta_layout = QHBoxLayout(meta_grp)
        meta_layout.addWidget(QLabel("Название:"))
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(lambda _: self._mark_dirty())
        meta_layout.addWidget(self.name_edit)
        meta_layout.addWidget(QLabel("Ш мм:"))
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(20, 300)
        self.width_spin.setValue(58)
        self.width_spin.valueChanged.connect(lambda _: self._mark_dirty())
        meta_layout.addWidget(self.width_spin)
        meta_layout.addWidget(QLabel("В мм:"))
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(15, 300)
        self.height_spin.setValue(40)
        self.height_spin.valueChanged.connect(lambda _: self._mark_dirty())
        meta_layout.addWidget(self.height_spin)
        center_layout.addWidget(meta_grp)

        # Таблица элементов
        center_layout.addWidget(QLabel("<b>Элементы шаблона</b>"))
        self.table = QTableWidget(0, len(ELEMENT_COLUMNS))
        self.table.setHorizontalHeaderLabels([c[0] for c in ELEMENT_COLUMNS])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.itemChanged.connect(lambda _: self._mark_dirty())
        center_layout.addWidget(self.table)

        elem_btn_row = QHBoxLayout()
        self.btn_add_elem = QPushButton("Добавить элемент")
        self.btn_del_elem = QPushButton("Удалить элемент")
        self.btn_add_elem.clicked.connect(self._on_add_element)
        self.btn_del_elem.clicked.connect(self._on_del_element)
        elem_btn_row.addWidget(self.btn_add_elem)
        elem_btn_row.addWidget(self.btn_del_elem)
        elem_btn_row.addStretch()
        center_layout.addLayout(elem_btn_row)

        # Кнопки сохранения
        save_row = QHBoxLayout()
        self.btn_save = QPushButton("Сохранить шаблон")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; }")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_preview = QPushButton("Предпросмотр")
        self.btn_preview.clicked.connect(self._on_preview)
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self._on_close)
        save_row.addWidget(self.btn_save)
        save_row.addWidget(self.btn_preview)
        save_row.addStretch()
        save_row.addWidget(self.btn_close)
        center_layout.addLayout(save_row)

        splitter.addWidget(center)

        # ---- Правая панель: предпросмотр ----
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.addWidget(QLabel("<b>Предпросмотр</b>"))
        self.preview_label = QLabel("(нажмите «Предпросмотр»)")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(232, 160)
        self.preview_label.setStyleSheet("border: 1px solid #aaa; background: #f5f5f5;")
        right_layout.addWidget(self.preview_label)
        right_layout.addStretch()
        splitter.addWidget(right)

        splitter.setSizes([220, 620, 260])

    # ------------------------------------------------------------------
    # Шаблоны
    # ------------------------------------------------------------------

    def _refresh_list(self):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for t in self._templates:
            suffix = " [по умолч.]" if t.default else ""
            item = QListWidgetItem(f"{t.name}{suffix}")
            item.setData(Qt.UserRole, t.id)
            self.list_widget.addItem(item)
        self.list_widget.blockSignals(False)
        if self._templates:
            self.list_widget.setCurrentRow(0)

    def _on_template_selected(self, row: int):
        if 0 <= row < len(self._templates):
            self._load_template(self._templates[row])

    def _load_template(self, t: Template):
        if self._dirty:
            ans = QMessageBox.question(
                self, "Несохранённые изменения",
                "Сохранить текущий шаблон перед переключением?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if ans == QMessageBox.Cancel:
                return
            if ans == QMessageBox.Yes:
                self._save_current()

        self._current = t
        self.name_edit.setText(t.name)
        self.width_spin.setValue(t.width_mm)
        self.height_spin.setValue(t.height_mm)
        self._fill_table(t.elements)
        self._dirty = False

    def _fill_table(self, elements: List[TemplateElement]):
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for elem in elements:
            self._append_row(elem)
        self.table.blockSignals(False)

    def _append_row(self, elem: TemplateElement):
        row = self.table.rowCount()
        self.table.insertRow(row)
        col_map = {c[1]: i for i, c in enumerate(ELEMENT_COLUMNS)}

        # type
        combo_type = QComboBox()
        combo_type.addItems(TYPES)
        combo_type.setCurrentText(elem.type)
        combo_type.currentTextChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["type"], combo_type)

        # floats
        for attr in ["x_mm", "y_mm", "w_mm", "h_mm"]:
            spin = QDoubleSpinBox()
            spin.setRange(0, 500)
            spin.setDecimals(1)
            spin.setValue(getattr(elem, attr))
            spin.valueChanged.connect(lambda _: self._mark_dirty())
            self.table.setCellWidget(row, col_map[attr], spin)

        # variable combo
        combo_var = QComboBox()
        combo_var.addItems(VARIABLES)
        if elem.variable in VARIABLES:
            combo_var.setCurrentText(elem.variable)
        else:
            combo_var.addItem(elem.variable)
            combo_var.setCurrentText(elem.variable)
        combo_var.currentTextChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["variable"], combo_var)

        # static_text
        self.table.setItem(row, col_map["static_text"], QTableWidgetItem(elem.static_text))

        # font_family
        self.table.setItem(row, col_map["font_family"], QTableWidgetItem(elem.font_family))

        # font_size
        spin_fs = QDoubleSpinBox()
        spin_fs.setRange(4, 72)
        spin_fs.setValue(elem.font_size)
        spin_fs.valueChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["font_size"], spin_fs)

        # bold
        chk_bold = QCheckBox()
        chk_bold.setChecked(elem.bold)
        chk_bold.stateChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["bold"], chk_bold)

        # align
        combo_align = QComboBox()
        combo_align.addItems(ALIGNS)
        combo_align.setCurrentText(elem.align)
        combo_align.currentTextChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["align"], combo_align)

        # visible
        chk_vis = QCheckBox()
        chk_vis.setChecked(elem.visible)
        chk_vis.stateChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["visible"], chk_vis)

        # required
        chk_req = QCheckBox()
        chk_req.setChecked(elem.required)
        chk_req.stateChanged.connect(lambda _: self._mark_dirty())
        self.table.setCellWidget(row, col_map["required"], chk_req)

    def _read_elements_from_table(self) -> List[TemplateElement]:
        col_map = {c[1]: i for i, c in enumerate(ELEMENT_COLUMNS)}
        elements = []
        for row in range(self.table.rowCount()):
            def get_widget(attr):
                return self.table.cellWidget(row, col_map[attr])
            def get_item_text(attr):
                item = self.table.item(row, col_map[attr])
                return item.text() if item else ""

            elem = TemplateElement(
                type=get_widget("type").currentText(),
                x_mm=get_widget("x_mm").value(),
                y_mm=get_widget("y_mm").value(),
                w_mm=get_widget("w_mm").value(),
                h_mm=get_widget("h_mm").value(),
                variable=get_widget("variable").currentText(),
                static_text=get_item_text("static_text"),
                font_family=get_item_text("font_family") or "Helvetica",
                font_size=get_widget("font_size").value(),
                bold=get_widget("bold").isChecked(),
                align=get_widget("align").currentText(),
                visible=get_widget("visible").isChecked(),
                required=get_widget("required").isChecked(),
            )
            elements.append(elem)
        return elements

    # ------------------------------------------------------------------
    # Кнопки
    # ------------------------------------------------------------------

    def _on_new(self):
        t = default_template()
        t.name = "Новый шаблон"
        t.default = False
        self._templates.append(t)
        self._refresh_list_preserve_selection(len(self._templates) - 1)

    def _on_copy(self):
        if self._current:
            t = self._current.copy()
            self._templates.append(t)
            self._refresh_list_preserve_selection(len(self._templates) - 1)

    def _on_delete(self):
        row = self.list_widget.currentRow()
        if row < 0 or row >= len(self._templates):
            return
        t = self._templates[row]
        ans = QMessageBox.question(
            self, "Удалить шаблон",
            f"Удалить шаблон «{t.name}»?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ans == QMessageBox.Yes:
            self._templates.pop(row)
            if not self._templates:
                self._templates.append(default_template())
            self._refresh_list_preserve_selection(max(0, row - 1))

    def _on_set_default(self):
        if self._current:
            for t in self._templates:
                t.default = (t.id == self._current.id)
            self._refresh_list()
            self._mark_dirty()

    def _on_add_element(self):
        elem = TemplateElement(type="text", x_mm=1.0, y_mm=1.0, w_mm=40.0, h_mm=6.0)
        self._append_row(elem)
        self._mark_dirty()

    def _on_del_element(self):
        rows = sorted(set(i.row() for i in self.table.selectedIndexes()), reverse=True)
        for r in rows:
            self.table.removeRow(r)
        self._mark_dirty()

    def _on_save(self):
        self._save_current()
        save_templates(str(self._path), self._templates)
        QMessageBox.information(self, "Сохранено", "Шаблоны сохранены.")
        if self._current:
            self.template_saved.emit(self._current.id)

    def _save_current(self):
        if not self._current:
            return
        self._current.name = self.name_edit.text() or "Шаблон"
        self._current.width_mm = self.width_spin.value()
        self._current.height_mm = self.height_spin.value()
        self._current.elements = self._read_elements_from_table()
        # Обновить в списке
        for i, t in enumerate(self._templates):
            if t.id == self._current.id:
                self._templates[i] = self._current
                break
        self._dirty = False
        self._refresh_list()

    def _on_preview(self):
        self._save_current()
        if not self._current:
            return
        try:
            from app.services.label_generator import LabelGenerator
            gen = LabelGenerator()
            img_bytes = gen.generate_preview_image(self._current, _PREVIEW_CTX)
            if img_bytes:
                pix = QPixmap()
                pix.loadFromData(img_bytes, "PNG")
                scaled = pix.scaled(
                    self.preview_label.width() - 4,
                    self.preview_label.height() - 4,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
                self.preview_label.setPixmap(scaled)
            else:
                self.preview_label.setText("Предпросмотр недоступен")
        except Exception as e:
            self.preview_label.setText(f"Ошибка: {e}")

    def _on_close(self):
        if self._dirty:
            ans = QMessageBox.question(
                self, "Несохранённые изменения",
                "Сохранить изменения перед закрытием?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            )
            if ans == QMessageBox.Cancel:
                return
            if ans == QMessageBox.Yes:
                self._save_current()
                save_templates(str(self._path), self._templates)
        self.accept()

    def _mark_dirty(self):
        self._dirty = True

    def _refresh_list_preserve_selection(self, select_row: int = 0):
        self._refresh_list()
        if 0 <= select_row < self.list_widget.count():
            self.list_widget.setCurrentRow(select_row)

    def get_templates(self) -> List[Template]:
        return self._templates

    def closeEvent(self, event):
        self._on_close()
        event.accept()
