"""
Settings tab for application configuration
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QComboBox, QSpinBox, QCheckBox, QFormLayout, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt

import config

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Tab for application settings"""
    
    def __init__(self, main_window):
        """Initialize settings tab"""
        super().__init__()
        self.main_window = main_window
        
        self.create_ui()
        self.load_settings()
    
    def create_ui(self) -> None:
        """Create UI"""
        layout = QVBoxLayout()
        
        # API Settings Group
        api_group = QGroupBox("Настройки API")
        api_form = QFormLayout()
        
        self.client_id_input = QLineEdit()
        api_form.addRow("Client ID:", self.client_id_input)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        api_form.addRow("API Key:", self.api_key_input)
        
        api_group.setLayout(api_form)
        layout.addWidget(api_group)
        
        # Printer Settings Group
        printer_group = QGroupBox("Настройки принтера")
        printer_form = QFormLayout()
        
        self.printer_name_input = QLineEdit()
        self.printer_name_input.setText(config.PRINTER_NAME)
        printer_form.addRow("Название принтера:", self.printer_name_input)
        
        self.printer_dpi_spinbox = QSpinBox()
        self.printer_dpi_spinbox.setRange(72, 600)
        self.printer_dpi_spinbox.setValue(config.DEFAULT_PRINTER_DPI)
        printer_form.addRow("DPI принтера:", self.printer_dpi_spinbox)
        
        printer_group.setLayout(printer_form)
        layout.addWidget(printer_group)
        
        # Label Settings Group
        label_group = QGroupBox("Настройки этикеток")
        label_form = QFormLayout()
        
        self.default_label_size_combo = QComboBox()
        self.default_label_size_combo.addItems(config.LABEL_SIZES.keys())
        label_form.addRow("Размер этикетки по умолчанию:", self.default_label_size_combo)
        
        self.default_template_combo = QComboBox()
        self.update_templates()
        label_form.addRow("Шаблон по умолчанию:", self.default_template_combo)
        
        label_group.setLayout(label_form)
        layout.addWidget(label_group)
        
        # Application Settings Group
        app_group = QGroupBox("Параметры приложения")
        app_form = QFormLayout()
        
        self.debug_cb = QCheckBox("Режим отладки")
        self.debug_cb.setChecked(config.DEBUG)
        app_form.addRow("", self.debug_cb)
        
        app_group.setLayout(app_form)
        layout.addWidget(app_group)
        
        layout.addStretch()
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.clicked.connect(self.save_settings)
        buttons_layout.addWidget(self.save_btn)
        
        self.reset_btn = QPushButton("↻ Сбросить")
        self.reset_btn.clicked.connect(self.reset_settings)
        buttons_layout.addWidget(self.reset_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
    
    def update_templates(self) -> None:
        """Update templates list"""
        self.default_template_combo.clear()
        templates = self.main_window.get_template_manager().list_templates()
        self.default_template_combo.addItems(templates)
    
    def load_settings(self) -> None:
        """Load settings from environment"""
        self.client_id_input.setText(config.OZON_CLIENT_ID)
        self.api_key_input.setText(config.OZON_API_KEY)
        self.printer_name_input.setText(config.PRINTER_NAME)
        self.printer_dpi_spinbox.setValue(config.DEFAULT_PRINTER_DPI)
        
        # Set default label size
        if config.DEFAULT_LABEL_SIZE in config.LABEL_SIZES:
            idx = self.default_label_size_combo.findText(config.DEFAULT_LABEL_SIZE)
            self.default_label_size_combo.setCurrentIndex(idx)
        
        # Set default template
        if config.DEFAULT_TEMPLATE:
            idx = self.default_template_combo.findText(config.DEFAULT_TEMPLATE)
            if idx >= 0:
                self.default_template_combo.setCurrentIndex(idx)
    
    def save_settings(self) -> None:
        """Save settings"""
        try:
            # Update config values (in memory)
            config.OZON_CLIENT_ID = self.client_id_input.text()
            config.OZON_API_KEY = self.api_key_input.text()
            config.PRINTER_NAME = self.printer_name_input.text()
            config.DEFAULT_PRINTER_DPI = self.printer_dpi_spinbox.value()
            config.DEFAULT_LABEL_SIZE = self.default_label_size_combo.currentText()
            config.DEFAULT_TEMPLATE = self.default_template_combo.currentText()
            config.DEBUG = self.debug_cb.isChecked()
            
            # Save to .env file
            self._save_to_env()
            
            QMessageBox.information(self, "Успех", "Настройки сохранены")
            logger.info("Settings saved")
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки: {e}")
            logger.error(f"Failed to save settings: {e}")
    
    def reset_settings(self) -> None:
        """Reset settings to defaults"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            "Вы уверены, что хотите сбросить все настройки?"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.load_settings()
            QMessageBox.information(self, "Успех", "Настройки сброшены")
    
    def _save_to_env(self) -> None:
        """Save settings to .env file"""
        from pathlib import Path
        
        env_file = Path('.env')
        
        env_content = f"""# Ozon API Configuration
OZON_CLIENT_ID={config.OZON_CLIENT_ID}
OZON_API_KEY={config.OZON_API_KEY}

# Application Settings
APP_NAME={config.APP_NAME}
DEFAULT_TEMPLATE={config.DEFAULT_TEMPLATE}
DEBUG={str(config.DEBUG)}

# Printer Settings
PRINTER_NAME={config.PRINTER_NAME}
DEFAULT_PRINTER_DPI={config.DEFAULT_PRINTER_DPI}
"""
        
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
