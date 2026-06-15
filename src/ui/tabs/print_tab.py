"""
Print tab for printing labels
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QRadioButton,
    QButtonGroup, QLabel, QMessageBox, QProgressBar, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.printing import LabelGenerator
from src.models.template import PrintType

logger = logging.getLogger(__name__)


class PrintThread(QThread):
    """Thread for printing labels"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, main_window, print_type, template):
        super().__init__()
        self.main_window = main_window
        self.print_type = print_type
        self.template = template
    
    def run(self):
        try:
            from win32print import OpenPrinter, ClosePrinter, StartDocPrinter, EndDocPrinter, WritePrinter, StartPagePrinter, EndPagePrinter
            from PIL import Image
            import io
            
            selected_shipments = self.main_window.shipments_tab.get_selected_shipments()
            total_labels = 0
            
            # Calculate total labels
            for shipment in selected_shipments:
                if self.print_type in ['routing', 'both']:
                    total_labels += 1
                if self.print_type in ['internal', 'both']:
                    total_labels += len(shipment.items)
            
            if total_labels == 0:
                self.error.emit("Нет выбранных заказов для печати")
                return
            
            label_generator = LabelGenerator()
            current_label = 0
            
            for shipment in selected_shipments:
                # Print routing label
                if self.print_type in ['routing', 'both']:
                    try:
                        self.progress.emit(current_label, f"Печать маршрутной этикетки: {shipment.shipment_id}")
                        
                        if shipment.label_data:
                            # Print PDF label from Ozon
                            self._print_pdf(shipment.label_data)
                        
                        current_label += 1
                    except Exception as e:
                        logger.error(f"Failed to print routing label: {e}")
                
                # Print internal labels
                if self.print_type in ['internal', 'both']:
                    for item in shipment.items:
                        try:
                            self.progress.emit(
                                current_label,
                                f"Печать внутренней этикетки: {item.product_name}"
                            )
                            
                            # Prepare data for template
                            data = item.to_dict()
                            data.update(shipment.to_dict())
                            
                            # Generate label
                            label_image = label_generator.generate_label(self.template, data)
                            
                            if label_image:
                                self._print_image(label_image)
                            
                            current_label += 1
                        except Exception as e:
                            logger.error(f"Failed to print internal label: {e}")
            
            self.progress.emit(total_labels, "Печать завершена")
            self.finished.emit()
        
        except Exception as e:
            self.error.emit(str(e))
            logger.error(f"Print error: {e}")
    
    def _print_pdf(self, pdf_data: bytes) -> None:
        """Print PDF data"""
        try:
            import tempfile
            import os
            from win32print import OpenPrinter, ClosePrinter, StartDocPrinter, EndDocPrinter, WritePrinter
            
            # Save PDF to temp file
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(pdf_data)
                temp_path = f.name
            
            try:
                # Use Windows print dialog
                import subprocess
                printer_name = "Xprinter XP-365B"
                subprocess.run([
                    'powershell', '-Command',
                    f'(New-Object -ComObject WScript.Shell).CreateShortCut("C:\\temp\\print.lnk").TargetPath = "C:\\Program Files\\SumatraPDF\\SumatraPDF.exe"; ' +
                    f'& "C:\\Program Files\\SumatraPDF\\SumatraPDF.exe" -print-to "{printer_name}" "{temp_path}"'
                ])
            finally:
                os.unlink(temp_path)
        
        except Exception as e:
            logger.warning(f"Failed to print PDF: {e}")
    
    def _print_image(self, image) -> None:
        """Print image to Windows printer"""
        try:
            from win32print import OpenPrinter, ClosePrinter, StartDocPrinter, EndDocPrinter, WritePrinter
            import tempfile
            import os
            
            # Save image to temp file
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name
                image.save(temp_path, 'PNG')
            
            try:
                # Print using Windows
                import subprocess
                printer_name = "Xprinter XP-365B"
                subprocess.run([
                    'powershell', '-Command',
                    f'Add-Type -AssemblyName System.Drawing; ' +
                    f'$img = [System.Drawing.Image]::FromFile("{temp_path}"); ' +
                    f'$pd = New-Object System.Drawing.Printing.PrintDocument; ' +
                    f'$pd.PrinterSettings.PrinterName = "{printer_name}"; ' +
                    f'$pd.Print()'
                ])
            finally:
                os.unlink(temp_path)
        
        except Exception as e:
            logger.warning(f"Failed to print image: {e}")


class PrintTab(QWidget):
    """Tab for printing labels"""
    
    def __init__(self, main_window):
        """Initialize print tab"""
        super().__init__()
        self.main_window = main_window
        self.print_thread = None
        
        self.create_ui()
    
    def create_ui(self) -> None:
        """Create UI"""
        layout = QVBoxLayout()
        
        # Print type selection
        print_type_layout = QHBoxLayout()
        print_type_layout.addWidget(QLabel("Тип печати:"))
        
        self.print_type_group = QButtonGroup()
        
        self.routing_radio = QRadioButton("Только маршрутные этикетки")
        self.internal_radio = QRadioButton("Только внутренние этикетки")
        self.both_radio = QRadioButton("Маршрутные + внутренние")
        self.both_radio.setChecked(True)
        
        self.print_type_group.addButton(self.routing_radio, 0)
        self.print_type_group.addButton(self.internal_radio, 1)
        self.print_type_group.addButton(self.both_radio, 2)
        
        print_type_layout.addWidget(self.routing_radio)
        print_type_layout.addWidget(self.internal_radio)
        print_type_layout.addWidget(self.both_radio)
        print_type_layout.addStretch()
        
        layout.addLayout(print_type_layout)
        
        # Template selection
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Шаблон внутренней этикетки:"))
        
        self.template_combo = QComboBox()
        self.update_template_list()
        template_layout.addWidget(self.template_combo)
        template_layout.addStretch()
        
        layout.addLayout(template_layout)
        
        # Options
        options_layout = QHBoxLayout()
        self.print_routing_cb = QCheckBox("Печать маршрутной этикетки (Ozon)")
        self.print_routing_cb.setChecked(True)
        options_layout.addWidget(self.print_routing_cb)
        
        self.print_internal_cb = QCheckBox("Печать внутренней этикетки")
        self.print_internal_cb.setChecked(True)
        options_layout.addWidget(self.print_internal_cb)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Print buttons
        buttons_layout = QHBoxLayout()
        
        self.print_selected_btn = QPushButton("🖨️ Печать выбранных")
        self.print_selected_btn.clicked.connect(self.print_selected)
        self.print_selected_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.print_selected_btn)
        
        self.print_all_btn = QPushButton("🖨️ Печать всех")
        self.print_all_btn.clicked.connect(self.print_all)
        self.print_all_btn.setMinimumHeight(40)
        buttons_layout.addWidget(self.print_all_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Готово к печати")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_template_list(self) -> None:
        """Update template list in combobox"""
        self.template_combo.clear()
        templates = self.main_window.get_template_manager().list_templates()
        self.template_combo.addItems(templates)
    
    def get_print_type(self) -> str:
        """Get selected print type"""
        checked = self.print_type_group.checkedId()
        if checked == 0:
            return 'routing'
        elif checked == 1:
            return 'internal'
        else:
            return 'both'
    
    def print_selected(self) -> None:
        """Print selected shipments"""
        self._do_print(True)
    
    def print_all(self) -> None:
        """Print all shipments"""
        # Select all shipments
        self.main_window.shipments_tab.select_all()
        self._do_print(False)
    
    def _do_print(self, selected_only: bool) -> None:
        """Execute print operation"""
        if not self.main_window.is_connected():
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала подключитесь к Ozon API")
            return
        
        selected_shipments = self.main_window.shipments_tab.get_selected_shipments()
        
        if not selected_shipments:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите заказы для печати")
            return
        
        # Load template
        template_id = self.template_combo.currentText()
        template = self.main_window.get_template_manager().load_template(template_id)
        
        if not template:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить шаблон: {template_id}")
            return
        
        print_type = self.get_print_type()
        
        self.progress_bar.setVisible(True)
        self.print_selected_btn.setEnabled(False)
        self.print_all_btn.setEnabled(False)
        
        self.print_thread = PrintThread(self.main_window, print_type, template)
        self.print_thread.progress.connect(self.on_progress)
        self.print_thread.finished.connect(self.on_print_finished)
        self.print_thread.error.connect(self.on_print_error)
        self.print_thread.start()
    
    def on_progress(self, current: int, message: str) -> None:
        """Handle progress update"""
        self.status_label.setText(message)
        self.progress_bar.setValue(current)
    
    def on_print_finished(self) -> None:
        """Handle print finished"""
        self.progress_bar.setVisible(False)
        self.print_selected_btn.setEnabled(True)
        self.print_all_btn.setEnabled(True)
        self.status_label.setText("✅ Печать завершена успешно")
        QMessageBox.information(self, "Успех", "Этикетки успешно напечатаны")
    
    def on_print_error(self, error: str) -> None:
        """Handle print error"""
        self.progress_bar.setVisible(False)
        self.print_selected_btn.setEnabled(True)
        self.print_all_btn.setEnabled(True)
        self.status_label.setText(f"❌ Ошибка печати: {error}")
        QMessageBox.critical(self, "Ошибка печати", f"Не удалось напечатать этикетки: {error}")
