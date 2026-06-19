"""
Template editor tab - visual editor for label templates
"""
import logging
import uuid
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QListWidget, QListWidgetItem, QFormLayout, QGroupBox, QLineEdit,
    QDoubleSpinBox, QSpinBox, QCheckBox, QMessageBox, QSplitter,
    QInputDialog
)
from PyQt6.QtCore import Qt

from src.models.template import Template, TemplateElement, ElementType, TextAlignment

logger = logging.getLogger(__name__)


class TemplateEditorTab(QWidget):
    """Tab for creating and editing label templates"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._current_template: Optional[Template] = None
        self._current_element: Optional[TemplateElement] = None

        self._create_ui()
        self._load_template_list()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _create_ui(self) -> None:
        layout = QHBoxLayout()
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: template/element list
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right panel: element properties
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setSizes([350, 500])
        layout.addWidget(splitter)
        self.setLayout(layout)

    def _create_left_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        # Template selector
        tpl_group = QGroupBox("Шаблон")
        tpl_layout = QVBoxLayout()

        self.template_combo = QComboBox()
        self.template_combo.currentTextChanged.connect(self._on_template_changed)
        tpl_layout.addWidget(self.template_combo)

        tpl_btn_layout = QHBoxLayout()
        self.new_tpl_btn = QPushButton("Новый")
        self.new_tpl_btn.clicked.connect(self._create_template)
        tpl_btn_layout.addWidget(self.new_tpl_btn)

        self.copy_tpl_btn = QPushButton("Копировать")
        self.copy_tpl_btn.clicked.connect(self._copy_template)
        tpl_btn_layout.addWidget(self.copy_tpl_btn)

        self.delete_tpl_btn = QPushButton("Удалить")
        self.delete_tpl_btn.clicked.connect(self._delete_template)
        tpl_btn_layout.addWidget(self.delete_tpl_btn)

        tpl_layout.addLayout(tpl_btn_layout)
        tpl_group.setLayout(tpl_layout)
        layout.addWidget(tpl_group)

        # Template dimensions
        dim_group = QGroupBox("Размеры этикетки (мм)")
        dim_layout = QFormLayout()

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(10, 300)
        self.width_spin.setValue(58)
        self.width_spin.valueChanged.connect(self._save_template)
        dim_layout.addRow("Ширина:", self.width_spin)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(10, 300)
        self.height_spin.setValue(40)
        self.height_spin.valueChanged.connect(self._save_template)
        dim_layout.addRow("Высота:", self.height_spin)

        dim_group.setLayout(dim_layout)
        layout.addWidget(dim_group)

        # Element list
        elem_group = QGroupBox("Элементы")
        elem_layout = QVBoxLayout()

        self.element_list = QListWidget()
        self.element_list.currentRowChanged.connect(self._on_element_selected)
        elem_layout.addWidget(self.element_list)

        elem_btn_layout = QHBoxLayout()
        self.add_text_btn = QPushButton("+ Текст")
        self.add_text_btn.clicked.connect(self._add_text_element)
        elem_btn_layout.addWidget(self.add_text_btn)

        self.add_barcode_btn = QPushButton("+ Штрихкод")
        self.add_barcode_btn.clicked.connect(self._add_barcode_element)
        elem_btn_layout.addWidget(self.add_barcode_btn)

        self.delete_elem_btn = QPushButton("Удалить")
        self.delete_elem_btn.clicked.connect(self._delete_element)
        elem_btn_layout.addWidget(self.delete_elem_btn)

        elem_layout.addLayout(elem_btn_layout)
        elem_group.setLayout(elem_layout)
        layout.addWidget(elem_group)

        widget.setLayout(layout)
        return widget

    def _create_right_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout()

        props_group = QGroupBox("Свойства элемента")
        form = QFormLayout()

        self.elem_id_label = QLabel("-")
        form.addRow("ID:", self.elem_id_label)

        self.elem_type_label = QLabel("-")
        form.addRow("Тип:", self.elem_type_label)

        self.variable_input = QLineEdit()
        self.variable_input.textChanged.connect(self._on_property_changed)
        form.addRow("Переменная:", self.variable_input)

        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(0, 300)
        self.x_spin.valueChanged.connect(self._on_property_changed)
        form.addRow("X (мм):", self.x_spin)

        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(0, 300)
        self.y_spin.valueChanged.connect(self._on_property_changed)
        form.addRow("Y (мм):", self.y_spin)

        self.w_spin = QDoubleSpinBox()
        self.w_spin.setRange(1, 300)
        self.w_spin.setValue(20)
        self.w_spin.valueChanged.connect(self._on_property_changed)
        form.addRow("Ширина (мм):", self.w_spin)

        self.h_spin = QDoubleSpinBox()
        self.h_spin.setRange(1, 300)
        self.h_spin.setValue(10)
        self.h_spin.valueChanged.connect(self._on_property_changed)
        form.addRow("Высота (мм):", self.h_spin)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(6, 72)
        self.font_size_spin.setValue(10)
        self.font_size_spin.valueChanged.connect(self._on_property_changed)
        form.addRow("Размер шрифта:", self.font_size_spin)

        self.bold_cb = QCheckBox()
        self.bold_cb.stateChanged.connect(self._on_property_changed)
        form.addRow("Жирный:", self.bold_cb)

        self.visible_cb = QCheckBox()
        self.visible_cb.setChecked(True)
        self.visible_cb.stateChanged.connect(self._on_property_changed)
        form.addRow("Видимый:", self.visible_cb)

        props_group.setLayout(form)
        layout.addWidget(props_group)
        layout.addStretch()

        self.save_btn = QPushButton("Сохранить шаблон")
        self.save_btn.clicked.connect(self._save_template)
        layout.addWidget(self.save_btn)

        widget.setLayout(layout)
        return widget

    # ------------------------------------------------------------------
    # Template operations
    # ------------------------------------------------------------------

    def _load_template_list(self) -> None:
        mgr = self.main_window.get_template_manager()
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        for tpl_id in mgr.list_templates():
            self.template_combo.addItem(tpl_id)
        self.template_combo.blockSignals(False)

        if self.template_combo.count() > 0:
            self._on_template_changed(self.template_combo.currentText())

    def _on_template_changed(self, template_id: str) -> None:
        if not template_id:
            return
        mgr = self.main_window.get_template_manager()
        self._current_template = mgr.load_template(template_id)
        if self._current_template:
            self.width_spin.blockSignals(True)
            self.height_spin.blockSignals(True)
            self.width_spin.setValue(self._current_template.label_width)
            self.height_spin.setValue(self._current_template.label_height)
            self.width_spin.blockSignals(False)
            self.height_spin.blockSignals(False)
            self._refresh_element_list()

    def _create_template(self) -> None:
        name, ok = QInputDialog.getText(self, "Новый шаблон", "Название шаблона:")
        if not ok or not name.strip():
            return
        tpl_id = name.strip().lower().replace(' ', '_')
        mgr = self.main_window.get_template_manager()
        tpl = Template(
            template_id=tpl_id,
            name=name.strip(),
            label_width=self.width_spin.value(),
            label_height=self.height_spin.value(),
        )
        if mgr.save_template(tpl):
            self._load_template_list()
            idx = self.template_combo.findText(tpl_id)
            if idx >= 0:
                self.template_combo.setCurrentIndex(idx)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось создать шаблон")

    def _copy_template(self) -> None:
        if not self._current_template:
            return
        new_name, ok = QInputDialog.getText(
            self, "Копировать шаблон", "Название копии:"
        )
        if not ok or not new_name.strip():
            return
        new_id = new_name.strip().lower().replace(' ', '_')
        mgr = self.main_window.get_template_manager()
        tpl = mgr.copy_template(self._current_template.template_id, new_id, new_name.strip())
        if tpl:
            self._load_template_list()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось скопировать шаблон")

    def _delete_template(self) -> None:
        if not self._current_template:
            return
        reply = QMessageBox.question(
            self, "Удаление", f"Удалить шаблон '{self._current_template.template_id}'?"
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        mgr = self.main_window.get_template_manager()
        if mgr.delete_template(self._current_template.template_id):
            self._current_template = None
            self._load_template_list()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось удалить шаблон")

    def _save_template(self) -> None:
        if not self._current_template:
            return
        self._current_template.label_width = self.width_spin.value()
        self._current_template.label_height = self.height_spin.value()
        mgr = self.main_window.get_template_manager()
        mgr.save_template(self._current_template)

    # ------------------------------------------------------------------
    # Element operations
    # ------------------------------------------------------------------

    def _refresh_element_list(self) -> None:
        self.element_list.clear()
        if not self._current_template:
            return
        for elem in self._current_template.elements:
            label = f"{elem.element_type.value}: {elem.variable or elem.element_id}"
            self.element_list.addItem(QListWidgetItem(label))

    def _on_element_selected(self, row: int) -> None:
        if not self._current_template or row < 0:
            self._current_element = None
            return
        self._current_element = self._current_template.elements[row]
        self._populate_properties()

    def _populate_properties(self) -> None:
        elem = self._current_element
        if not elem:
            return
        self.elem_id_label.setText(elem.element_id)
        self.elem_type_label.setText(elem.element_type.value)
        self.variable_input.blockSignals(True)
        self.variable_input.setText(elem.variable or '')
        self.variable_input.blockSignals(False)
        for spin, val in [
            (self.x_spin, elem.x), (self.y_spin, elem.y),
            (self.w_spin, elem.width), (self.h_spin, elem.height),
        ]:
            spin.blockSignals(True)
            spin.setValue(val)
            spin.blockSignals(False)
        self.font_size_spin.blockSignals(True)
        self.font_size_spin.setValue(elem.font_size)
        self.font_size_spin.blockSignals(False)
        self.bold_cb.blockSignals(True)
        self.bold_cb.setChecked(elem.font_bold)
        self.bold_cb.blockSignals(False)
        self.visible_cb.blockSignals(True)
        self.visible_cb.setChecked(elem.visible)
        self.visible_cb.blockSignals(False)

    def _on_property_changed(self) -> None:
        if not self._current_element:
            return
        self._current_element.variable = self.variable_input.text() or None
        self._current_element.x = self.x_spin.value()
        self._current_element.y = self.y_spin.value()
        self._current_element.width = self.w_spin.value()
        self._current_element.height = self.h_spin.value()
        self._current_element.font_size = self.font_size_spin.value()
        self._current_element.font_bold = self.bold_cb.isChecked()
        self._current_element.visible = self.visible_cb.isChecked()

    def _add_text_element(self) -> None:
        if not self._current_template:
            return
        elem = TemplateElement(
            element_id=f'text_{uuid.uuid4().hex[:6]}',
            element_type=ElementType.TEXT,
            x=5, y=5, width=40, height=8,
            variable='product_name',
        )
        self._current_template.add_element(elem)
        self._save_template()
        self._refresh_element_list()

    def _add_barcode_element(self) -> None:
        if not self._current_template:
            return
        elem = TemplateElement(
            element_id=f'barcode_{uuid.uuid4().hex[:6]}',
            element_type=ElementType.BARCODE,
            x=5, y=5, width=48, height=20,
            variable='barcode',
        )
        self._current_template.add_element(elem)
        self._save_template()
        self._refresh_element_list()

    def _delete_element(self) -> None:
        if not self._current_template or not self._current_element:
            return
        self._current_template.remove_element(self._current_element.element_id)
        self._current_element = None
        self._save_template()
        self._refresh_element_list()
